from dataclasses import replace
from pathlib import Path

import pytest

from pycronk.core.api import DEFAULT_ENGINE_ID, Cryptor
from pycronk.core.errors import Cancelled, InvalidFormat
from pycronk.core.interfaces import CancelFlag, Keys
from pycronk.services.crypto_service import TRACE_LIMIT_BYTES, CryptoService
from pycronk.services.models import Kind, Operation, Status
from pycronk.services.settings import Settings

SECRET_TEXT = "texto ultra secreto 123"


@pytest.fixture
def settings() -> dict[str, Settings]:
    return {"value": Settings(chunk_symbols=16)}


@pytest.fixture
def service(fake_history, fake_clock, settings) -> CryptoService:
    return CryptoService(Cryptor.default(), fake_history, fake_clock, lambda: settings["value"])


def test_text_round_trip_records_history(service, fake_history, fake_clock, keys):
    encrypted = service.encrypt_text(SECRET_TEXT, keys)
    assert service.decrypt_text(encrypted.text, keys).text == SECRET_TEXT
    enc, dec = fake_history.entries
    assert (enc.operation, enc.kind, enc.status) == (Operation.ENCRYPT, Kind.TEXT, Status.OK)
    assert (dec.operation, dec.status) == (Operation.DECRYPT, Status.OK)
    assert dec.engine_id == DEFAULT_ENGINE_ID
    assert enc.created_at == fake_clock.now()
    assert enc.duration_ms >= 0


def test_history_never_contains_sensitive_data(service, fake_history, keys, tmp_path):
    encrypted = service.encrypt_text(SECRET_TEXT, keys)
    service.decrypt_text(encrypted.text, keys)
    src = tmp_path / "doc.txt"
    src.write_text(SECRET_TEXT)
    service.encrypt_file(src, keys)
    for entry in fake_history.entries:
        for value in vars(entry).values():
            text = str(value)
            assert keys.matrix not in text
            assert keys.keystream not in text
            assert SECRET_TEXT not in text
            assert encrypted.text[6:30] not in text


def test_history_disabled(service, fake_history, settings, keys):
    settings["value"] = replace(settings["value"], history_enabled=False)
    service.encrypt_text("x", keys)
    assert fake_history.entries == []


def test_error_is_recorded_and_raised(service, fake_history, keys):
    with pytest.raises(InvalidFormat):
        service.decrypt_text("no es cifrado", keys)
    (entry,) = fake_history.entries
    assert entry.status is Status.ERROR
    assert entry.engine_id == "desconocido"


def test_trace_only_when_requested_and_small(service, keys):
    assert service.encrypt_text("hola", keys).trace is None
    traced = service.encrypt_text("hola", keys, trace=True)
    assert traced.trace is not None and len(traced.trace.steps) == 3
    assert service.encrypt_text("x" * (TRACE_LIMIT_BYTES + 1), keys, trace=True).trace is None
    back = service.decrypt_text(traced.text, keys, trace=True)
    assert back.trace is not None and back.trace.length_bytes == 4


def test_file_round_trip(service, fake_history, keys, tmp_path):
    src = tmp_path / "foto.jpg"
    src.write_bytes(bytes(range(256)) * 50)
    encrypted = service.encrypt_file(src, keys)
    assert encrypted.name == "foto.jpg.pcrk"
    decrypted = service.decrypt_file(encrypted, keys, dst=tmp_path / "out.jpg")
    assert decrypted.read_bytes() == src.read_bytes()
    enc, dec = fake_history.entries
    assert enc.kind is Kind.FILE and enc.label == "foto.jpg"
    assert enc.input_size == src.stat().st_size
    assert enc.output_path == str(encrypted)
    assert dec.engine_id == DEFAULT_ENGINE_ID


def test_file_progress(service, keys, tmp_path):
    src = tmp_path / "a.bin"
    src.write_bytes(bytes(1000))
    calls: list[tuple[int, int]] = []
    service.encrypt_file(src, keys, progress=lambda d, t: calls.append((d, t)))
    assert calls[-1] == (1000, 1000)


def test_cancel_removes_partial_output(service, fake_history, keys, tmp_path):
    src = tmp_path / "a.bin"
    src.write_bytes(bytes(1000))
    flag = CancelFlag()
    flag.cancel()
    with pytest.raises(Cancelled):
        service.encrypt_file(src, keys, cancel=flag)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.bin"]
    assert fake_history.entries[-1].status is Status.CANCELLED


def test_failed_decrypt_leaves_no_file(service, keys, tmp_path):
    src = tmp_path / "falso.pcrk"
    src.write_bytes(b"no es un contenedor")
    with pytest.raises(InvalidFormat):
        service.decrypt_file(src, keys)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["falso.pcrk"]


def test_suggest_output_names(service, settings, tmp_path):
    src = tmp_path / "informe.pdf"
    assert service.suggest_output(src, Operation.ENCRYPT) == tmp_path / "informe.pdf.pcrk"
    enc = tmp_path / "informe.pdf.pcrk"
    assert service.suggest_output(enc, Operation.DECRYPT) == tmp_path / "informe.pdf"
    assert service.suggest_output(src, Operation.DECRYPT) == tmp_path / "informe.pdf.descifrado"


def test_suggest_output_avoids_overwriting(service, tmp_path):
    (tmp_path / "a.txt.pcrk").write_bytes(b"")
    (tmp_path / "a.txt (1).pcrk").write_bytes(b"")
    assert service.suggest_output(tmp_path / "a.txt", Operation.ENCRYPT).name == "a.txt (2).pcrk"


def test_suggest_output_uses_configured_folder(service, settings, tmp_path):
    out = tmp_path / "salida"
    settings["value"] = replace(settings["value"], output_dir=str(out))
    assert service.suggest_output(Path("/x/a.txt"), Operation.ENCRYPT) == out / "a.txt.pcrk"


def test_purge_history_uses_retention(service, fake_history, fake_clock, settings, keys):
    service.encrypt_text("viejo", keys)
    fake_clock.advance(days=100)
    service.encrypt_text("nuevo", keys)
    assert service.purge_history() == 1
    assert len(fake_history.entries) == 1


def test_purge_disabled_with_zero_days(service, fake_history, fake_clock, settings, keys):
    settings["value"] = replace(settings["value"], history_retention_days=0)
    service.encrypt_text("viejo", keys)
    fake_clock.advance(days=1000)
    assert service.purge_history() == 0
    assert len(fake_history.entries) == 1


def test_wrong_keys_file(service, keys, tmp_path):
    src = tmp_path / "a.txt"
    src.write_bytes(b"contenido original")
    enc = service.encrypt_file(src, keys)
    out = service.decrypt_file(enc, Keys("mala", "clave"), dst=tmp_path / "b.txt")
    assert out.read_bytes() != b"contenido original"

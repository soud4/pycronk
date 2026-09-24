import io

import pytest

from pycronk.cli import NullHistory, main

KEYS = ["-m", "MAR7", "-k", "otra"]


def test_text_round_trip(capsys):
    assert main(["encrypt-text", "hola mundo", *KEYS]) == 0
    armored = capsys.readouterr().out.strip()
    assert armored.startswith("PCRK1:")
    assert main(["decrypt-text", armored, *KEYS]) == 0
    assert capsys.readouterr().out == "hola mundo\n"


def test_text_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("desde stdin\n"))
    assert main(["encrypt-text", *KEYS]) == 0
    armored = capsys.readouterr().out.strip()
    monkeypatch.setattr("sys.stdin", io.StringIO(armored))
    assert main(["decrypt-text", *KEYS]) == 0
    assert capsys.readouterr().out == "desde stdin\n"


def test_file_round_trip(tmp_path, capsys):
    src = tmp_path / "datos.bin"
    src.write_bytes(bytes(range(256)) * 20)
    assert main(["encrypt", str(src), *KEYS]) == 0
    encrypted = tmp_path / "datos.bin.pcrk"
    assert capsys.readouterr().out.strip() == str(encrypted)
    out = tmp_path / "copia.bin"
    assert main(["decrypt", str(encrypted), "-o", str(out), *KEYS]) == 0
    assert out.read_bytes() == src.read_bytes()


def test_prompts_for_missing_passwords(monkeypatch, capsys):
    answers = iter(["MAR7", "otra"])
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(answers))
    assert main(["encrypt-text", "x"]) == 0
    assert capsys.readouterr().out.startswith("PCRK1:")


def test_errors_return_1(tmp_path, capsys):
    assert main(["decrypt-text", "no cifrado", *KEYS]) == 1
    assert "error:" in capsys.readouterr().err
    assert main(["encrypt", str(tmp_path / "no-existe"), *KEYS]) == 1
    assert main(["encrypt-text", "x", "--engine", "nada", *KEYS]) == 1


def test_engines(capsys):
    assert main(["engines"]) == 0
    assert capsys.readouterr().out.startswith("pycronk-v1\t")


def test_requires_command():
    with pytest.raises(SystemExit):
        main([])


def test_null_history_is_inert():
    history = NullHistory()
    assert history.add(None) == 0  # type: ignore[arg-type]
    assert history.list(limit=5) == []
    history.delete(1)
    history.clear()
    assert history.purge_older_than(None) == 0  # type: ignore[arg-type]

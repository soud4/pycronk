"""Interfaz de línea de comandos. Es otra raíz de composición, igual que ui/app.py."""

import argparse
import getpass
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from pycronk import __version__
from pycronk.core.api import Cryptor
from pycronk.core.errors import PycronkError
from pycronk.core.interfaces import Keys
from pycronk.services.crypto_service import CryptoService
from pycronk.services.models import HistoryEntry, Kind
from pycronk.services.ports import SystemClock
from pycronk.services.settings import Settings


class NullHistory:
    """La CLI no escribe en el historial de la GUI: suele usarse en scripts y llenaría el
    historial de entradas que el usuario no hizo a mano."""

    def add(self, entry: HistoryEntry) -> int:
        return 0

    def list(self, *, limit: int, offset: int = 0, kind: Kind | None = None) -> list[HistoryEntry]:
        return []

    def delete(self, entry_id: int) -> None:
        pass

    def clear(self) -> None:
        pass

    def purge_older_than(self, cutoff: datetime) -> int:
        return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pycronk-cli", description="Cifrado híbrido pycronk.")
    parser.add_argument("--version", action="version", version=f"pycronk {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    def with_keys(sub: argparse.ArgumentParser) -> argparse.ArgumentParser:
        # Pasar contraseñas por argumento las deja en el historial del shell; por eso son
        # opcionales y, si faltan, se piden sin eco.
        sub.add_argument("-m", "--matrix", help="contraseña de la matriz")
        sub.add_argument("-k", "--keystream", help="contraseña del keystream")
        return sub

    for name, help_text in (("encrypt", "cifra un archivo"), ("decrypt", "descifra un archivo")):
        sub = with_keys(commands.add_parser(name, help=help_text))
        sub.add_argument("file", type=Path)
        sub.add_argument("-o", "--output", type=Path, help="archivo de salida")
    enc = commands.choices["encrypt"]
    enc.add_argument("--engine", help="id del motor (ver `engines`)")

    for name, help_text in (
        ("encrypt-text", "cifra texto (argumento o stdin)"),
        ("decrypt-text", "descifra texto (argumento o stdin)"),
    ):
        sub = with_keys(commands.add_parser(name, help=help_text))
        sub.add_argument("text", nargs="?")
    commands.choices["encrypt-text"].add_argument("--engine")

    commands.add_parser("engines", help="lista los motores disponibles")
    return parser


def _keys(args: argparse.Namespace) -> Keys:
    matrix = args.matrix if args.matrix is not None else getpass.getpass("Contraseña de matriz: ")
    keystream = (
        args.keystream
        if args.keystream is not None
        else getpass.getpass("Contraseña de keystream: ")
    )
    return Keys(matrix, keystream)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cryptor = Cryptor.default()
    if args.command == "engines":
        for engine in cryptor.engines:
            print(f"{engine.id}\t{engine.title}")
        return 0

    settings = Settings()
    if getattr(args, "engine", None):
        settings = replace(settings, engine_id=args.engine)
    service = CryptoService(cryptor, NullHistory(), SystemClock(), lambda: settings)
    try:
        keys = _keys(args)
        if args.command == "encrypt":
            print(service.encrypt_file(args.file, keys, dst=args.output))
        elif args.command == "decrypt":
            print(service.decrypt_file(args.file, keys, dst=args.output))
        else:
            text = args.text if args.text is not None else sys.stdin.read()
            if args.command == "encrypt-text":
                print(service.encrypt_text(text.removesuffix("\n"), keys).text)
            else:
                print(service.decrypt_text(text, keys).text)
    except (PycronkError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

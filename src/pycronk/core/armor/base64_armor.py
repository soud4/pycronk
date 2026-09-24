import base64
import binascii

from pycronk.core.errors import InvalidFormat

PREFIX = "PCRK1:"


class Base64Armor:
    id = "base64"

    def encode(self, payload: bytes) -> str:
        return PREFIX + base64.b64encode(payload).decode("ascii")

    def decode(self, text: str) -> bytes:
        # Se toleran espacios y saltos de línea porque los clientes de correo y chat suelen
        # partir las líneas largas al pegar.
        compact = "".join(text.split())
        if not compact.startswith(PREFIX):
            raise InvalidFormat("El texto no es un cifrado de pycronk (falta el prefijo PCRK1:).")
        try:
            return base64.b64decode(compact[len(PREFIX) :], validate=True)
        except binascii.Error:
            raise InvalidFormat("El texto cifrado está incompleto o dañado.") from None

    def detects(self, text: str) -> bool:
        return text.lstrip().startswith(PREFIX)

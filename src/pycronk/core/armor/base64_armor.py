import base64
import binascii

from pycronk.core.container import MAGIC
from pycronk.core.errors import InvalidFormat

# Base64 agrupa de 3 en 3 bytes, así que los 3 primeros del magic (`PCR`) se codifican siempre en
# estos 4 caracteres, sea cual sea el resto del contenedor. Eso permite reconocer un cifrado
# pegado sin decodificarlo entero en cada pulsación de tecla, sin necesitar un prefijo propio.
B64_MAGIC = base64.b64encode(MAGIC).decode("ascii")[:4]
# Hasta la v0.1.0 el texto cifrado llevaba este prefijo delante. Ya no se emite, pero se sigue
# aceptando al descifrar para no invalidar los mensajes que ya estén por ahí.
LEGACY_PREFIX = "PCRK1:"

_NOT_ENCRYPTED = "El texto no es un cifrado de pycronk."


class Base64Armor:
    id = "base64"

    def encode(self, payload: bytes) -> str:
        return base64.b64encode(payload).decode("ascii")

    def decode(self, text: str) -> bytes:
        # Se toleran espacios y saltos de línea porque los clientes de correo y chat suelen
        # partir las líneas largas al pegar.
        compact = "".join(text.split()).removeprefix(LEGACY_PREFIX)
        # El magic se mira antes de decodificar para no confundir dos errores que al usuario le
        # suenan muy distinto: «esto no es un cifrado» vs «el cifrado está dañado».
        if not compact.startswith(B64_MAGIC):
            raise InvalidFormat(_NOT_ENCRYPTED)
        try:
            payload = base64.b64decode(compact, validate=True)
        except binascii.Error:
            raise InvalidFormat("El texto cifrado está incompleto o dañado.") from None
        # `B64_MAGIC` solo cubre 3 de los 4 bytes del magic; el cuarto se comprueba aquí.
        if not payload.startswith(MAGIC):
            raise InvalidFormat(_NOT_ENCRYPTED)
        return payload

    def detects(self, text: str) -> bool:
        return text.lstrip().startswith((B64_MAGIC, LEGACY_PREFIX))

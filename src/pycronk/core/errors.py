class PycronkError(Exception):
    """Raíz común: la UI y la CLI capturan esta clase para mostrar errores de dominio."""


class InvalidFormat(PycronkError):
    pass


class UnsupportedVersion(PycronkError):
    pass


class UnknownEngine(PycronkError):
    pass


class DuplicateRegistration(PycronkError):
    pass


class Cancelled(PycronkError):
    pass

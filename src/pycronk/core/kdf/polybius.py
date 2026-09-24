_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_COORDINATES = {ch: index + 1 for index, ch in enumerate(_ALPHABET)}

# 37 es primo y coprimo con el tamaño del alfabeto (36), así que dos posiciones distintas nunca
# colapsan al mismo peso. 2^61 - 1 es primo de Mersenne: el módulo primo reparte bien los valores
# y cabe holgado en un entero de 64 bits.
_BASE = 37
_PRIME = 2**61 - 1


class PolybiusKdf:
    id = "polybius-poly"

    def derive(self, password: str) -> int:
        result, power = 0, 1
        for ch in password.upper():
            # Los caracteres fuera del cuadrado (tildes, símbolos) no se descartan: perder
            # caracteres reduciría aún más el espacio de claves.
            value = _COORDINATES.get(ch, (ord(ch) % 36) + 1)
            result = (result + value * power) % _PRIME
            power = (power * _BASE) % _PRIME
        return result

from collections.abc import Iterator

from pycronk.core.errors import DuplicateRegistration, PycronkError


class Registry[T]:
    """Colección de implementaciones por id.

    Es una instancia, no un singleton de módulo: cada raíz de composición (GUI, CLI, tests) arma el
    suyo, y los tests nunca se contaminan entre sí.
    """

    def __init__(self, missing_error: type[PycronkError] = PycronkError) -> None:
        self._items: dict[str, T] = {}
        self._missing_error = missing_error

    def register(self, item_id: str, item: T) -> None:
        # Sobrescribir en silencio podría hacer que un archivo se descifre con otro algoritmo.
        if item_id in self._items:
            raise DuplicateRegistration(f"Ya existe una implementación con id '{item_id}'.")
        self._items[item_id] = item

    def get(self, item_id: str) -> T:
        try:
            return self._items[item_id]
        except KeyError:
            raise self._missing_error(
                f"No hay ninguna implementación con id '{item_id}'."
            ) from None

    def ids(self) -> list[str]:
        return list(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, item_id: object) -> bool:
        return item_id in self._items

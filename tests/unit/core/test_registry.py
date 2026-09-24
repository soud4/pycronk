import pytest

from pycronk.core.errors import DuplicateRegistration, UnknownEngine
from pycronk.core.registry import Registry


def test_register_get_and_iterate():
    registry: Registry[str] = Registry(UnknownEngine)
    registry.register("b", "B")
    registry.register("a", "A")
    assert registry.get("a") == "A"
    assert registry.ids() == ["b", "a"]
    assert list(registry) == ["B", "A"]
    assert "a" in registry
    assert "z" not in registry


def test_duplicate_is_rejected():
    registry: Registry[int] = Registry()
    registry.register("x", 1)
    with pytest.raises(DuplicateRegistration):
        registry.register("x", 2)
    assert registry.get("x") == 1


def test_missing_raises_configured_error():
    with pytest.raises(UnknownEngine):
        Registry[int](UnknownEngine).get("nada")

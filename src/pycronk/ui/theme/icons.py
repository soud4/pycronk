import weakref
from collections.abc import Callable
from typing import Any, Protocol

import qtawesome as qta
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel

from pycronk.ui.theme.builder import ThemeManager
from pycronk.ui.theme.tokens import DesignTokens

# Nombres lógicos → Phosphor (regular). Las páginas solo conocen el nombre lógico: cambiar de
# familia de iconos es tocar este diccionario.
PHOSPHOR: dict[str, str] = {
    "encrypt": "ph.lock-simple",
    "decrypt": "ph.lock-simple-open",
    "text": "ph.text-aa",
    "files": "ph.files",
    "file": "ph.file",
    "process": "ph.stack",
    "history": "ph.clock-counter-clockwise",
    "settings": "ph.gear-six",
    "eye": "ph.eye",
    "eye_off": "ph.eye-slash",
    "copy": "ph.copy",
    "trash": "ph.trash",
    "upload": "ph.upload-simple",
    "folder": "ph.folder-open",
    "close": "ph.x",
    "success": "ph.check-circle",
    "error": "ph.warning-circle",
    "info": "ph.info",
    "key": "ph.key",
    "export": "ph.arrow-square-out",
    "clear": "ph.eraser",
    "shield": "ph.shield-check",
}

ROLES = ("primary", "secondary", "accent", "on_accent", "danger", "success")


class IconTarget(Protocol):
    def setIcon(self, icon: QIcon, /) -> None: ...


class IconProvider(Protocol):
    def icon(self, name: str, role: str = "primary") -> QIcon: ...

    def bind(self, target: IconTarget, name: str, role: str = "primary") -> None: ...

    def bind_pixmap(
        self, label: QLabel, name: str, role: str = "primary", size: int = 18
    ) -> None: ...


def _role_color(tokens: DesignTokens, role: str) -> str:
    return {
        "primary": tokens.text_primary,
        "secondary": tokens.text_secondary,
        "accent": tokens.accent_text,
        "on_accent": tokens.on_accent,
        "danger": tokens.danger,
        "success": tokens.success,
    }[role]


class QtAwesomeIconProvider(QObject):
    def __init__(self, theme: ThemeManager) -> None:
        super().__init__(theme)
        self._theme = theme
        self._cache: dict[tuple[str, str, str], QIcon] = {}
        # Referencias débiles: un botón destruido no debe quedar vivo solo porque tiene un icono.
        self._bindings: list[tuple[weakref.ref[Any], Callable[[Any], None]]] = []
        theme.changed.connect(self._refresh)

    def icon(self, name: str, role: str = "primary") -> QIcon:
        tokens = self._theme.tokens
        key = (name, role, tokens.id)
        if key not in self._cache:
            self._cache[key] = qta.icon(PHOSPHOR[name], color=_role_color(tokens, role))
        return self._cache[key]

    def bind(self, target: IconTarget, name: str, role: str = "primary") -> None:
        """Asigna el icono y lo vuelve a asignar con el color correcto cuando cambia el tema."""
        self._bind(target, lambda t: t.setIcon(self.icon(name, role)))

    def bind_pixmap(self, label: QLabel, name: str, role: str = "primary", size: int = 18) -> None:
        self._bind(label, lambda t: t.setPixmap(self.icon(name, role).pixmap(size, size)))

    def _bind(self, target: Any, apply: Callable[[Any], None]) -> None:
        apply(target)
        # Volver a enlazar el mismo objeto reemplaza el enlace anterior (p. ej. ojo ↔ ojo tachado).
        self._bindings = [b for b in self._bindings if b[0]() is not target]
        self._bindings.append((weakref.ref(target), apply))

    def _refresh(self, _tokens: DesignTokens) -> None:
        alive: list[tuple[weakref.ref[Any], Callable[[Any], None]]] = []
        for ref, apply in self._bindings:
            target = ref()
            if target is None:
                continue
            try:
                apply(target)
            except RuntimeError:  # el objeto C++ ya fue destruido por Qt
                continue
            alive.append((ref, apply))
        self._bindings = alive

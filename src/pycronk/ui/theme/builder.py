from pathlib import Path
from string import Template

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from pycronk.services.settings import Theme
from pycronk.ui.theme.tokens import DARK, LIGHT, DesignTokens

ASSETS = Path(__file__).parent
FONTS = ASSETS / "fonts"
UI_FONT = "Inter"
MONO_FONT = "JetBrains Mono"


def build_qss(tokens: DesignTokens, mono_family: str = MONO_FONT) -> str:
    template = Template((ASSETS / "qss_template.qss").read_text(encoding="utf-8"))
    # Qt exige barras normales en url() incluso en Windows.
    chevron = (ASSETS / f"chevron-{tokens.id}.svg").as_posix()
    values = {key: str(value) for key, value in vars(tokens).items()}
    return template.substitute(values, font_mono=mono_family, chevron=chevron)


def build_palette(tokens: DesignTokens) -> QPalette:
    """La paleta cubre lo que QSS no alcanza (menús, diálogos nativos, tooltips) y es la vía por la
    que los widgets pintados a mano leen colores: al cambiar de tema Qt les reenvía un
    PaletteChange y se repintan solos, sin estado global.

    Roles reutilizados por los widgets propios: Midlight = pista (track), Light = pulgar (thumb),
    Mid = separador, Dark = borde fuerte, Highlight = acento.
    """
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: tokens.window,
        QPalette.ColorRole.WindowText: tokens.text_primary,
        QPalette.ColorRole.Base: tokens.card,
        QPalette.ColorRole.AlternateBase: tokens.content,
        QPalette.ColorRole.Text: tokens.text_primary,
        QPalette.ColorRole.PlaceholderText: tokens.text_secondary,
        QPalette.ColorRole.Button: tokens.card,
        QPalette.ColorRole.ButtonText: tokens.text_primary,
        QPalette.ColorRole.BrightText: tokens.danger,
        QPalette.ColorRole.Highlight: tokens.accent,
        QPalette.ColorRole.HighlightedText: tokens.on_accent,
        QPalette.ColorRole.Link: tokens.accent_text,
        QPalette.ColorRole.ToolTipBase: tokens.card,
        QPalette.ColorRole.ToolTipText: tokens.text_primary,
        QPalette.ColorRole.Midlight: tokens.track,
        QPalette.ColorRole.Light: tokens.thumb,
        QPalette.ColorRole.Mid: tokens.separator,
        QPalette.ColorRole.Dark: tokens.border_strong,
        QPalette.ColorRole.Shadow: tokens.border_strong,
        QPalette.ColorRole.Accent: tokens.accent,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(tokens.text_secondary))
    return palette


def relative_luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def load_fonts() -> tuple[str, str]:
    """Registra las fuentes incluidas. Si faltan (p. ej. alguien las borró del paquete) se cae a
    las del sistema en lugar de fallar: la tipografía no es motivo para no arrancar."""
    loaded: set[str] = set()
    for font_file in sorted(FONTS.glob("*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id != -1:
            loaded.update(QFontDatabase.applicationFontFamilies(font_id))
    ui = (
        UI_FONT
        if UI_FONT in loaded
        else QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()
    )
    mono = (
        MONO_FONT
        if MONO_FONT in loaded
        else QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    )
    return ui, mono


class ThemeManager(QObject):
    changed = Signal(object)  # DesignTokens

    def __init__(self, app: QApplication, mono_family: str) -> None:
        super().__init__(app)
        self._app = app
        self._mono = mono_family
        self._mode = Theme.SYSTEM
        self._tokens = LIGHT
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_system_scheme)

    @property
    def tokens(self) -> DesignTokens:
        return self._tokens

    @property
    def mono_family(self) -> str:
        return self._mono

    def apply(self, mode: Theme) -> None:
        self._mode = mode
        tokens = self._resolve(mode)
        # Se aplica aunque no cambie, para que la primera llamada instale paleta y QSS.
        self._tokens = tokens
        self._app.setPalette(build_palette(tokens))
        self._app.setStyleSheet(build_qss(tokens, self._mono))
        self.changed.emit(tokens)

    def _resolve(self, mode: Theme) -> DesignTokens:
        if mode is Theme.LIGHT:
            return LIGHT
        if mode is Theme.DARK:
            return DARK
        scheme = QGuiApplication.styleHints().colorScheme()
        return DARK if scheme == Qt.ColorScheme.Dark else LIGHT

    def _on_system_scheme(self, _scheme: Qt.ColorScheme) -> None:
        if self._mode is Theme.SYSTEM:
            self.apply(Theme.SYSTEM)

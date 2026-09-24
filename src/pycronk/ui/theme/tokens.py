"""Tokens de diseño (spec 006). Única fuente de verdad de colores y medidas de la interfaz."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    id: str
    dark: bool
    window: str
    sidebar: str
    content: str
    card: str
    separator: str
    border_strong: str
    text_primary: str
    text_secondary: str
    accent: str
    accent_pressed: str
    accent_text: str
    on_accent: str
    sidebar_selected: str
    control_hover: str
    control_pressed: str
    track: str
    thumb: str
    success: str
    danger: str
    success_bg: str
    info_bg: str
    danger_bg: str
    radius_control: int = 6
    radius_card: int = 10
    font_body: int = 13
    font_title: int = 22


# Valores tomados de los colores de sistema de macOS (Sonoma), con ajustes donde el original no
# llega a contraste 4.5:1 (WCAG AA):
# - `accent` (relleno con texto blanco) es #0071E3, el azul de los botones de apple.com: el azul
#   de sistema #007AFF solo da 4.0:1 con blanco.
# - `accent_text` separa el acento usado como color de texto/icono, que necesita otro tono en cada
#   tema para contrastar con el fondo.
# - Estados y texto secundario usan las variantes de mayor contraste de la paleta de Apple.
LIGHT = DesignTokens(
    id="light",
    dark=False,
    window="#ECECEC",
    sidebar="#E3E3E3",
    content="#F5F5F7",
    card="#FFFFFF",
    separator="#D1D1D6",
    border_strong="#C1C1C6",
    text_primary="#1D1D1F",
    text_secondary="#626267",
    accent="#0071E3",
    accent_pressed="#005BBF",
    accent_text="#0066CC",
    on_accent="#FFFFFF",
    sidebar_selected="#D0D0D5",
    control_hover="#F7F7F9",
    control_pressed="#E5E5EA",
    track="#E3E3E8",
    thumb="#FFFFFF",
    success="#1E7B34",
    danger="#D70015",
    success_bg="#E6F4EA",
    info_bg="#E5F0FF",
    danger_bg="#FDECEC",
)

DARK = DesignTokens(
    id="dark",
    dark=True,
    window="#1E1E1E",
    sidebar="#262626",
    content="#232323",
    card="#2C2C2E",
    separator="#3A3A3C",
    border_strong="#48484A",
    text_primary="#F5F5F7",
    text_secondary="#98989D",
    accent="#0071E3",
    accent_pressed="#005BBF",
    accent_text="#409CFF",
    on_accent="#FFFFFF",
    sidebar_selected="#3A3A3C",
    control_hover="#333336",
    control_pressed="#3F3F42",
    track="#3A3A3C",
    thumb="#636366",
    success="#30D158",
    danger="#FF6961",
    success_bg="#1E3324",
    info_bg="#1B2B40",
    danger_bg="#3A1F1F",
)

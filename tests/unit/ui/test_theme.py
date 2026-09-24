import itertools
from pathlib import Path

import pytest
from PySide6.QtGui import QPalette

from pycronk.services.settings import Theme
from pycronk.ui.theme.builder import (
    MONO_FONT,
    UI_FONT,
    build_palette,
    build_qss,
    contrast_ratio,
    load_fonts,
)
from pycronk.ui.theme.tokens import DARK, LIGHT

TOKENS = [LIGHT, DARK]


@pytest.mark.parametrize("tokens", TOKENS, ids=lambda t: t.id)
def test_qss_has_no_unresolved_placeholders(tokens):
    qss = build_qss(tokens)
    assert "$" not in qss
    assert tokens.accent in qss
    assert tokens.content in qss


@pytest.mark.parametrize("tokens", TOKENS, ids=lambda t: t.id)
def test_qss_references_existing_chevron(tokens):
    qss = build_qss(tokens)
    path = qss.split('image: url("')[1].split('")')[0]
    assert Path(path).is_file()


@pytest.mark.parametrize("tokens", TOKENS, ids=lambda t: t.id)
def test_palette_maps_tokens(qapp, tokens):
    palette = build_palette(tokens)
    expected = {
        QPalette.ColorRole.Window: tokens.window,
        QPalette.ColorRole.Base: tokens.card,
        QPalette.ColorRole.Text: tokens.text_primary,
        QPalette.ColorRole.Highlight: tokens.accent,
        QPalette.ColorRole.HighlightedText: tokens.on_accent,
        QPalette.ColorRole.Link: tokens.accent_text,
        QPalette.ColorRole.Midlight: tokens.track,
        QPalette.ColorRole.Light: tokens.thumb,
        QPalette.ColorRole.Mid: tokens.separator,
    }
    for role, color in expected.items():
        assert palette.color(role).name().upper() == color.upper(), role
    disabled = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
    assert disabled.name().upper() == tokens.text_secondary.upper()


TEXT_PAIRS = [
    *itertools.product(
        ["text_primary", "text_secondary"],
        ["card", "content", "window", "sidebar", "success_bg", "info_bg", "danger_bg"],
    ),
    ("text_primary", "sidebar_selected"),
    ("on_accent", "accent"),
    ("on_accent", "accent_pressed"),
    ("accent_text", "card"),
    ("accent_text", "content"),
    ("danger", "card"),
    ("success", "card"),
]


@pytest.mark.parametrize("tokens", TOKENS, ids=lambda t: t.id)
@pytest.mark.parametrize(("fg", "bg"), TEXT_PAIRS)
def test_text_contrast_meets_wcag_aa(tokens, fg, bg):
    ratio = contrast_ratio(getattr(tokens, fg), getattr(tokens, bg))
    assert ratio >= 4.5, f"{tokens.id}: {fg} sobre {bg} = {ratio:.2f}"


def test_contrast_ratio_reference_values():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1)


def test_manager_applies_and_emits(qapp, theme, qtbot):
    with qtbot.waitSignal(theme.changed) as blocker:
        theme.apply(Theme.DARK)
    assert blocker.args == [DARK]
    assert theme.tokens is DARK
    assert qapp.palette().color(QPalette.ColorRole.Window).name().upper() == DARK.window
    assert DARK.content in qapp.styleSheet()


def test_manager_system_resolves_to_a_theme(theme):
    theme.apply(Theme.SYSTEM)
    assert theme.tokens in (LIGHT, DARK)


def test_bundled_fonts_are_loaded(qapp):
    assert load_fonts() == (UI_FONT, MONO_FONT)

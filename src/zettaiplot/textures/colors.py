"""Color and palette helpers for texture rendering."""

from __future__ import annotations

from zettaiplot.textures.specs import ColorLike, ColorPreset, PaletteSpec, PalettePreset, RGB


COLOR_PRESETS: dict[ColorPreset, RGB] = {
    "black": (23, 22, 28),
    "white": (245, 242, 232),
    "pink": (245, 138, 177),
    "navy": (38, 52, 92),
    "brown": (91, 54, 38),
}
PALETTE_PRESETS: dict[PalettePreset, tuple[RGB, RGB]] = {
    "mono_black": ((30, 29, 35), (64, 62, 70)),
    "school": ((34, 40, 74), (238, 238, 224)),
    "candy": ((247, 143, 184), (255, 238, 246)),
    "classic": ((28, 27, 31), (245, 242, 232)),
}


def resolve_color(color: ColorLike) -> RGB:
    """Resolve a color preset or RGB tuple into an RGB tuple."""
    if isinstance(color, str):
        return COLOR_PRESETS[color]
    red, green, blue = color
    return (
        clamp_channel(red),
        clamp_channel(green),
        clamp_channel(blue),
    )


def resolve_palette(palette: PaletteSpec | PalettePreset) -> tuple[RGB, RGB]:
    """Resolve a palette preset or custom palette into two RGB colors."""
    if isinstance(palette, str):
        return PALETTE_PRESETS[palette]
    if palette.preset is not None:
        return PALETTE_PRESETS[palette.preset]
    if palette.color_a is None or palette.color_b is None:
        raise ValueError("Custom PaletteSpec requires color_a and color_b")
    return resolve_color(palette.color_a), resolve_color(palette.color_b)


def clamp_channel(value: int) -> int:
    """Clamp a color channel to 0-255."""
    return max(0, min(255, int(value)))

"""Pixel blending helpers for texture rendering."""

from __future__ import annotations

from zettaiplot.textures.specs import RGB, RGBA


def alpha_blend(source: RGBA, overlay: RGBA) -> RGBA:
    """Alpha-composite one overlay pixel over a source pixel."""
    alpha = overlay[3] / 255
    inv = 1.0 - alpha
    return (
        round(source[0] * inv + overlay[0] * alpha),
        round(source[1] * inv + overlay[1] * alpha),
        round(source[2] * inv + overlay[2] * alpha),
        source[3],
    )


def multiply_tinted(source: RGBA, tint: RGB, amount: float) -> RGBA:
    """Blend source toward a multiply-tinted color."""
    alpha = clamp_float(amount, 0.0, 1.0)
    multiplied = (
        round(source[0] * tint[0] / 255),
        round(source[1] * tint[1] / 255),
        round(source[2] * tint[2] / 255),
    )
    return (
        round(lerp(source[0], multiplied[0], alpha)),
        round(lerp(source[1], multiplied[1], alpha)),
        round(lerp(source[2], multiplied[2], alpha)),
        source[3],
    )


def scale_color(color: RGB, factor: float) -> RGB:
    """Scale an RGB color by a clamped factor."""
    return (
        round(clamp_float(color[0] * factor, 0, 255)),
        round(clamp_float(color[1] * factor, 0, 255)),
        round(clamp_float(color[2] * factor, 0, 255)),
    )


def luminance(color: RGBA) -> float:
    """Return perceived luminance for an RGBA pixel."""
    return color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114


def rgba_tuple(value: object) -> RGBA:
    """Cast a Pillow RGBA pixel to a typed tuple."""
    if not isinstance(value, tuple) or len(value) != 4:
        raise TypeError("Expected RGBA pixel tuple")
    red, green, blue, alpha = value
    return (int(red), int(green), int(blue), int(alpha))


def deterministic_noise(x: int, y: int) -> float:
    """Return deterministic pseudo-random noise in the range [-0.5, 0.5]."""
    value = (x * 12_989 + y * 78_233) & 0xFFFF
    value = (value * 1_103_515_245 + 12_345) & 0x7FFFFFFF
    return value / 0x7FFFFFFF - 0.5


def lerp(start: float, end: float, t: float) -> float:
    """Linearly interpolate between two numbers."""
    return start + (end - start) * t


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    """Clamp a float to a closed interval."""
    return max(minimum, min(maximum, value))

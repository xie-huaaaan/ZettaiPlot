"""Geometry helpers for cylindrical texture effects."""

from __future__ import annotations

from zettaiplot.textures.blend import clamp_float
from zettaiplot.textures.masks import RowProfile


def row_u(profile: RowProfile | None, x: int) -> float:
    """Return normalized row coordinate for cylindrical approximations."""
    if profile is None:
        return 0.0
    return clamp_float((x - profile.center) / profile.half_width, -1.0, 1.0)


def gradient_t(value: float, curve: str) -> float:
    """Apply a named gradient curve."""
    t = clamp_float(value, 0.0, 1.0)
    if curve == "ease_in":
        return t * t
    if curve == "ease_out":
        return 1.0 - (1.0 - t) * (1.0 - t)
    return t


def near_periodic_line(value: float, period: int, line_width: int) -> bool:
    """Return whether a coordinate is close to a repeated line."""
    distance = periodic_distance(value, period)
    return distance <= line_width or distance >= period - line_width


def periodic_distance(value: float, period: int) -> float:
    """Return distance from the nearest lower period boundary."""
    wrapped = value % period
    return min(wrapped, period - wrapped)

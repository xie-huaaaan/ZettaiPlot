"""Alpha mask and row-profile helpers for sock rendering."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from zettaiplot.textures.blend import clamp_float


@dataclass(frozen=True)
class RowProfile:
    """Alpha span profile for one y row."""

    left: int
    right: int
    center: float
    half_width: float


def sock_mask_and_profiles(
    image: Image.Image,
    coverage_ratio: float,
) -> tuple[list[bool], list[RowProfile | None], int]:
    """Return sock coverage mask and per-row alpha profiles."""
    width, height = image.size
    alpha_values = image.getchannel("A").get_flattened_data()
    coverage = clamp_float(coverage_ratio, 0.0, 1.0)
    covered_height = max(1, round(height * coverage))
    top_y = max(0, height - covered_height)
    mask = [False] * (width * height)
    profiles: list[RowProfile | None] = [None] * height

    for y in range(top_y, height):
        row_offset = y * width
        alpha_xs: list[int] = []
        for x in range(width):
            alpha_value = alpha_values[row_offset + x]
            if isinstance(alpha_value, int | float) and alpha_value > 0:
                alpha_xs.append(x)
        if not alpha_xs:
            continue
        left = min(alpha_xs)
        right = max(alpha_xs)
        center = (left + right) / 2
        half_width = max((right - left) / 2, 1.0)
        profiles[y] = RowProfile(left, right, center, half_width)
        for x in alpha_xs:
            mask[row_offset + x] = True

    return mask, profiles, top_y

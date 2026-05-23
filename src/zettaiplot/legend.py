"""Texture swatch legend helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
from matplotlib.artist import Artist
from matplotlib.image import BboxImage
from matplotlib.legend_handler import HandlerBase
from matplotlib.transforms import Bbox, Transform
from PIL import Image

from zettaiplot.textures import SockTextureSpec, render_sock_texture
from zettaiplot.textures.blend import rgba_tuple


class TextureLegendHandle(Artist):
    """Legend proxy that carries a rendered texture swatch."""

    def __init__(self, label: str, image: Image.Image) -> None:
        """Initialize a texture swatch legend proxy."""
        super().__init__()
        self.label = label
        self.image = image


class HandlerTextureSwatch(HandlerBase):
    """Matplotlib legend handler for texture swatches."""

    def create_artists(
        self,
        legend: object,
        orig_handle: object,
        xdescent: float,
        ydescent: float,
        width: float,
        height: float,
        fontsize: float,
        trans: Transform,
    ) -> list[Artist]:
        """Create the rectangular swatch artist for a legend entry."""
        del legend, fontsize
        if not isinstance(orig_handle, TextureLegendHandle):
            raise TypeError("HandlerTextureSwatch requires TextureLegendHandle")
        bbox = Bbox.from_bounds(xdescent, ydescent, width, height)
        image = BboxImage(bbox, interpolation="bilinear")
        image.set_data(np.asarray(orig_handle.image.convert("RGBA")))
        image.set_transform(trans)
        return [image]


def make_texture_swatch(spec: SockTextureSpec, width: int = 96, height: int = 34) -> Image.Image:
    """Render a small rectangular texture sample for legends."""
    leg = Image.new("RGBA", (width, height), (236, 188, 164, 255))
    pixels = list(leg.get_flattened_data())
    shaded: list[tuple[int, int, int, int]] = []
    center = (width - 1) / 2
    half_width = max(center, 1.0)
    for y in range(height):
        for x in range(width):
            u = abs((x - center) / half_width)
            # 图例 swatch 使用简单柱面明暗：边缘按 |u| 加深，模拟腿部圆柱边缘阴影。
            factor = 1.0 - 0.18 * (u**1.7) - 0.04 * (y / max(height - 1, 1))
            red, green, blue, alpha = rgba_tuple(pixels[y * width + x])
            shaded.append(
                (
                    round(red * factor),
                    round(green * factor),
                    round(blue * factor),
                    alpha,
                ),
            )
    leg.putdata(shaded)
    return render_sock_texture(leg, spec, coverage_ratio=1.0)


def make_legend_handles(
    labels: Sequence[str],
    textures: Mapping[str, SockTextureSpec],
) -> list[TextureLegendHandle]:
    """Create texture legend handles in label order."""
    return [
        TextureLegendHandle(label=label, image=make_texture_swatch(textures[label]))
        for label in labels
    ]


def normalize_legend_ncol(
    handles: Sequence[TextureLegendHandle],
    labels: Sequence[str],
    requested_ncol: int | None,
) -> tuple[list[TextureLegendHandle], list[str], int]:
    """Normalize positive/negative ncol semantics for Matplotlib legends."""
    if requested_ncol is None:
        return list(handles), list(labels), 1
    if requested_ncol == 0:
        raise ValueError("legend ncol=0 is invalid")
    if requested_ncol > 0:
        return list(handles), list(labels), requested_ncol

    rows_per_column = abs(requested_ncol)
    item_count = len(handles)
    column_count = max(1, math.ceil(item_count / rows_per_column))
    order: list[int] = []
    for row_index in range(rows_per_column):
        for column_index in range(column_count):
            item_index = column_index * rows_per_column + row_index
            if item_index < item_count:
                order.append(item_index)
    ordered_handles = [handles[index] for index in order]
    ordered_labels = [labels[index] for index in order]
    return ordered_handles, ordered_labels, column_count

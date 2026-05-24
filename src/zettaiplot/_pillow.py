"""Compatibility helpers for supported Pillow versions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

from PIL import Image


type ImagePixel = int | float | tuple[int, ...]


class _FlattenedImageProtocol(Protocol):
    """Image-like object exposing Pillow's newer flattened pixel API."""

    def get_flattened_data(self) -> Sequence[ImagePixel]:
        """Return flattened pixel data."""
        ...


def flattened_pixels(image: Image.Image) -> list[ImagePixel]:
    """Return image pixels as a flat list across Pillow 11 and newer."""
    if hasattr(image, "get_flattened_data"):
        flattened = cast(_FlattenedImageProtocol, image).get_flattened_data()
        return list(flattened)
    return list(cast(Sequence[ImagePixel], image.getdata()))

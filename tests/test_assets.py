"""Tests for packaged asset loading."""

from __future__ import annotations

from zettaiplot.assets import load_default_assets, open_leg


def test_default_assets_are_packaged() -> None:
    """Default packaged assets include the split manifest and leg PNGs."""
    library = load_default_assets()

    assert len(library.assets) == 26
    assert len(library.pairs) == 13
    assert {asset.side for asset in library.assets.values()} == {"l", "r"}


def test_open_packaged_leg_preserves_height() -> None:
    """Packaged leg images open as 720px-high RGBA images."""
    library = load_default_assets()
    asset = library.assets["leg_10_l"]
    image = open_leg(asset)

    assert image.mode == "RGBA"
    assert image.height == 720
    assert image.width == asset.width

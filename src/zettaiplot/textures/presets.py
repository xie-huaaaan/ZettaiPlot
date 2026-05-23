"""Convenience texture preset constructors."""

from __future__ import annotations

from zettaiplot.textures.specs import (
    FishnetSpec,
    HorizontalStripesSpec,
    LaceTopSpec,
    OpaqueSpec,
    PaletteSpec,
    SheerSpec,
)


def sheer_black() -> SheerSpec:
    """Return a black sheer stocking preset."""
    return SheerSpec(color="black", denier=36, edge_enrichment=0.35, grain_strength=0.05)


def opaque_white() -> OpaqueSpec:
    """Return a white opaque sock preset."""
    return OpaqueSpec(color="white", opacity=0.84, edge_shadow=0.16, cuff_height=18)


def school_stripes() -> HorizontalStripesSpec:
    """Return a blue-white school stripe preset."""
    return HorizontalStripesSpec(palette=PaletteSpec(preset="school"), stripe_height=16, gap_height=12)


def classic_fishnet() -> FishnetSpec:
    """Return a classic black fishnet preset."""
    return FishnetSpec(color="black", cell_size=30, line_width=2, angle=45)


def lace_sheer_black() -> LaceTopSpec:
    """Return a black sheer lace-top preset."""
    return LaceTopSpec(base_style="sheer", lace_height=46, motif_scale=14, lace_opacity=0.72)

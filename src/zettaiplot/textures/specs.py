"""Texture specification types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


type RGB = tuple[int, int, int]
type RGBA = tuple[int, int, int, int]
type ColorPreset = Literal["black", "white", "pink", "navy", "brown"]
type PalettePreset = Literal["mono_black", "school", "candy", "classic"]
type ColorLike = ColorPreset | RGB
type GradientCurve = Literal["linear", "ease_in", "ease_out"]
type BaseStyle = Literal["opaque", "sheer"]
type SockTextureKind = Literal[
    "opaque",
    "sheer",
    "gradient_sheer",
    "horizontal_stripes",
    "ribbed",
    "fishnet",
    "polka_dot",
    "lace_top",
]


@dataclass(frozen=True)
class PaletteSpec:
    """Two-color palette used by patterned textures."""

    preset: PalettePreset | None = None
    color_a: ColorLike | None = None
    color_b: ColorLike | None = None


@dataclass(frozen=True)
class OpaqueSpec:
    """Solid over-knee sock texture parameters."""

    kind: Literal["opaque"] = "opaque"
    color: ColorLike = "black"
    opacity: float = 0.9
    edge_shadow: float = 0.25
    cuff_height: int = 18


@dataclass(frozen=True)
class SheerSpec:
    """Transparent stocking texture parameters."""

    kind: Literal["sheer"] = "sheer"
    color: ColorLike = "black"
    denier: float = 40.0
    edge_enrichment: float = 0.35
    grain_strength: float = 0.08


@dataclass(frozen=True)
class GradientSheerSpec:
    """Sheer stocking texture with vertical opacity falloff."""

    kind: Literal["gradient_sheer"] = "gradient_sheer"
    color: ColorLike = "black"
    top_opacity: float = 0.65
    bottom_opacity: float = 0.25
    gradient_curve: GradientCurve = "linear"


@dataclass(frozen=True)
class HorizontalStripesSpec:
    """Horizontal striped sock texture parameters."""

    kind: Literal["horizontal_stripes"] = "horizontal_stripes"
    palette: PaletteSpec = PaletteSpec(preset="school")
    stripe_height: int = 18
    gap_height: int = 14
    warp_strength: float = 0.45


@dataclass(frozen=True)
class RibbedSpec:
    """Vertical ribbed fabric texture parameters."""

    kind: Literal["ribbed"] = "ribbed"
    color: ColorLike = "white"
    rib_spacing: int = 10
    rib_depth: float = 0.28
    highlight_strength: float = 0.22


@dataclass(frozen=True)
class FishnetSpec:
    """Diamond mesh stocking texture parameters."""

    kind: Literal["fishnet"] = "fishnet"
    color: ColorLike = "black"
    cell_size: int = 30
    line_width: int = 2
    angle: float = 45.0


@dataclass(frozen=True)
class PolkaDotSpec:
    """Polka-dot sock texture parameters."""

    kind: Literal["polka_dot"] = "polka_dot"
    palette: PaletteSpec = PaletteSpec(preset="candy")
    dot_radius: int = 5
    dot_spacing: int = 24
    staggered: bool = True


@dataclass(frozen=True)
class LaceTopSpec:
    """Decorative lace top texture parameters."""

    kind: Literal["lace_top"] = "lace_top"
    base_style: BaseStyle = "sheer"
    lace_height: int = 46
    motif_scale: int = 14
    lace_opacity: float = 0.72


type SockTextureSpec = (
    OpaqueSpec
    | SheerSpec
    | GradientSheerSpec
    | HorizontalStripesSpec
    | RibbedSpec
    | FishnetSpec
    | PolkaDotSpec
    | LaceTopSpec
)

"""Matplotlib-style public sockbar API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.image import AxesImage

from zettaiplot.artists import draw_sock_leg
from zettaiplot.assets import load_default_assets
from zettaiplot.data import normalize_values, resolve_sockbar_records
from zettaiplot.layout import (
    HueInnerGap,
    LegPlacement,
    OddSingle,
    SockBarLayout,
    compute_sockbar_layout,
)
from zettaiplot.legend import (
    HandlerTextureSwatch,
    TextureLegendHandle,
    make_legend_handles,
    normalize_legend_ncol,
)
from zettaiplot.textures import (
    FishnetSpec,
    HorizontalStripesSpec,
    OpaqueSpec,
    PaletteSpec,
    PolkaDotSpec,
    RibbedSpec,
    SheerSpec,
    SockTextureSpec,
)


@dataclass(frozen=True)
class SockBarContainer:
    """Return value for :func:`sockbar`."""

    ax: Axes
    image_artists: list[AxesImage]
    asset_ids: list[str]
    values: list[float]
    normalized_values: list[float]
    legend_handles: list[TextureLegendHandle]
    legend_labels: list[str]
    placements: list[LegPlacement]
    legend_ncol: int | None


def sockbar(
    data: object,
    label: object | None = None,
    *,
    texture: SockTextureSpec | None = None,
    hue_textures: Mapping[object, SockTextureSpec]
    | Sequence[SockTextureSpec]
    | None = None,
    ax: Axes | None = None,
    legend: bool = True,
    legend_kwargs: Mapping[str, object] | None = None,
    hue_inner_gap: HueInnerGap = "auto",
    group_gap: int = 80,
    odd_single: OddSingle = "center",
    seed: int | None = None,
) -> SockBarContainer:
    """Draw a ZettaiPlot sock bar chart on Matplotlib axes.

    Args:
        data: Numeric chart data. Accepted forms are a one-dimensional sequence,
            a NumPy array, a two-dimensional matrix, or a mapping where each key
            is a hue/legend label and each value is that hue's category series.
        label: Optional category labels. When omitted, integer labels are generated.
        texture: Default texture for non-hue charts or explicit shared texture.
        hue_textures: Optional mapping/sequence of textures for hue labels.
        ax: Existing axes. When omitted, a new figure and axes are created.
        legend: Whether to add a texture swatch legend for hue charts.
        legend_kwargs: Keyword arguments passed to ``Axes.legend``.
        hue_inner_gap: Pixel gap between hue legs; negative values overlap.
            The default ``"auto"`` uses the packaged source-pair gap for
            exactly two hue levels and falls back to 14px for other hue counts.
        group_gap: Pixel gap between category groups.
        odd_single: Unpaired single-leg position for odd non-hue category counts.
        seed: Random seed for single-leg asset side selection.

    Returns:
        A container with axes, artists, asset ids, normalized values, and legend metadata.
    """
    records = resolve_sockbar_records(data, label)
    normalized_values = normalize_values(records)
    library = load_default_assets()
    layout = compute_sockbar_layout(
        records,
        normalized_values,
        library,
        hue_inner_gap=hue_inner_gap,
        group_gap=group_gap,
        odd_single=odd_single,
        seed=seed,
    )
    texture_by_hue = resolve_chart_textures(
        layout.hue_labels,
        texture=texture,
        hue_textures=hue_textures,
    )

    if ax is None:
        width = max(6.0, (layout.right_x - layout.left_x + 180) / 180)
        _, created_ax = plt.subplots(figsize=(width, 5.8))
        ax = cast(Axes, created_ax)
    assert ax is not None
    target_ax: Axes = ax

    image_artists: list[AxesImage] = []
    for placement in layout.placements:
        spec = texture_for_placement(placement, texture, texture_by_hue)
        artist = draw_sock_leg(
            target_ax,
            placement.asset,
            x=placement.center_x,
            value=placement.coverage_ratio,
            texture=spec,
            zorder=placement.zorder,
        )
        image_artists.append(artist)

    configure_axes(target_ax, layout)
    legend_handles: list[TextureLegendHandle] = []
    legend_labels: list[str] = []
    legend_ncol: int | None = None
    if legend and layout.hue_labels:
        legend_handles, legend_labels, legend_ncol = add_texture_legend(
            target_ax,
            layout.hue_labels,
            texture_by_hue,
            legend_kwargs,
        )

    return SockBarContainer(
        ax=target_ax,
        image_artists=image_artists,
        asset_ids=[placement.asset.asset_id for placement in layout.placements],
        values=[record.value for record in records],
        normalized_values=normalized_values,
        legend_handles=legend_handles,
        legend_labels=legend_labels,
        placements=layout.placements,
        legend_ncol=legend_ncol,
    )


def resolve_chart_textures(
    hue_labels: Sequence[str],
    *,
    texture: SockTextureSpec | None,
    hue_textures: Mapping[object, SockTextureSpec] | Sequence[SockTextureSpec] | None,
) -> dict[str, SockTextureSpec]:
    """Resolve chart texture specs for each hue label."""
    if not hue_labels:
        return {}
    if hue_textures is None:
        if texture is not None:
            return {label: texture for label in hue_labels}
        defaults = default_hue_textures()
        if len(hue_labels) > len(defaults):
            raise ValueError(f"only {len(defaults)} default hue textures are available")
        return {label: defaults[index] for index, label in enumerate(hue_labels)}
    if isinstance(hue_textures, Mapping):
        resolved: dict[str, SockTextureSpec] = {}
        for label in hue_labels:
            if label in hue_textures:
                resolved[label] = hue_textures[label]
            else:
                raise KeyError(f"missing texture for hue label {label!r}")
        return resolved
    specs = list(hue_textures)
    if len(specs) < len(hue_labels):
        raise ValueError("hue_textures sequence is shorter than the hue label count")
    return {label: specs[index] for index, label in enumerate(hue_labels)}


def default_hue_textures() -> tuple[SockTextureSpec, ...]:
    """Return visually distinct default hue textures."""
    return (
        OpaqueSpec(color="black", opacity=0.88, edge_shadow=0.22, cuff_height=18),
        HorizontalStripesSpec(
            palette=PaletteSpec(preset="school"),
            stripe_height=16,
            gap_height=12,
        ),
        SheerSpec(color="pink", denier=42, edge_enrichment=0.36, grain_strength=0.05),
        FishnetSpec(color="navy", cell_size=28, line_width=2),
        RibbedSpec(color="white", rib_spacing=9, rib_depth=0.25),
        PolkaDotSpec(palette=PaletteSpec(preset="candy"), dot_radius=5, dot_spacing=24),
    )


def texture_for_placement(
    placement: LegPlacement,
    texture: SockTextureSpec | None,
    texture_by_hue: Mapping[str, SockTextureSpec],
) -> SockTextureSpec:
    """Return the texture for a placement."""
    if placement.hue_label is not None:
        return texture_by_hue[placement.hue_label]
    if texture is not None:
        return texture
    return OpaqueSpec()


def configure_axes(ax: Axes, layout: SockBarLayout) -> None:
    """Apply basic Matplotlib axes limits and category ticks."""
    ax.set_xlim(layout.left_x - 60, layout.right_x + 60)
    ax.set_ylim(0, 740)
    ax.set_xticks([category.center_x for category in layout.categories])
    ax.set_xticklabels([category.label for category in layout.categories])
    ax.set_ylabel("value")
    ax.set_aspect("equal", adjustable="box")


def add_texture_legend(
    ax: Axes,
    hue_labels: Sequence[str],
    texture_by_hue: Mapping[str, SockTextureSpec],
    legend_kwargs: Mapping[str, object] | None,
) -> tuple[list[TextureLegendHandle], list[str], int]:
    """Add a texture swatch legend to an axes."""
    handles = make_legend_handles(hue_labels, texture_by_hue)
    labels = list(hue_labels)
    kwargs: dict[str, object] = {
        "loc": "upper left",
        "bbox_to_anchor": (1.01, 1.0),
        "borderaxespad": 0.0,
    }
    kwargs.update(dict(legend_kwargs or {}))
    requested_ncol = kwargs.pop("ncol", kwargs.pop("ncols", 1))  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(requested_ncol, int):
        raise TypeError("legend ncol must be an integer")
    ordered_handles, ordered_labels, ncol = normalize_legend_ncol(
        handles,
        labels,
        requested_ncol,
    )
    kwargs["ncols"] = ncol
    ax.legend(
        ordered_handles,
        ordered_labels,
        handler_map={TextureLegendHandle: HandlerTextureSwatch()},
        **kwargs,  # pyright: ignore[reportUnknownArgumentType]
    )
    return ordered_handles, ordered_labels, ncol

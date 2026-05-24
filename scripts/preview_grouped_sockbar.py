# ruff: noqa: E402
"""Generate grouped sockbar previews through the formal Matplotlib API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import zettaiplot as zp
from zettaiplot.textures import (
    FishnetSpec,
    HorizontalStripesSpec,
    OpaqueSpec,
    PaletteSpec,
    RibbedSpec,
    SheerSpec,
    SockTextureSpec,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "assets" / "split" / "grouped_previews"
type PreviewHueInnerGap = int | Literal["auto"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate grouped sockbar layout preview images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where grouped preview images are written.",
    )
    return parser.parse_args()


def hue_specs(count: int) -> tuple[SockTextureSpec, ...]:
    """Return visually distinct texture specs for hue previews."""
    specs: tuple[SockTextureSpec, ...] = (
        OpaqueSpec(color="black", opacity=0.88, edge_shadow=0.22, cuff_height=18),
        HorizontalStripesSpec(
            palette=PaletteSpec(preset="school"),
            stripe_height=16,
            gap_height=12,
        ),
        SheerSpec(color="pink", denier=42, edge_enrichment=0.36, grain_strength=0.05),
        FishnetSpec(color="navy", cell_size=28, line_width=2),
        RibbedSpec(color="white", rib_spacing=9, rib_depth=0.25),
    )
    if count > len(specs):
        raise ValueError(f"Only {len(specs)} hue texture specs are defined")
    return specs[:count]


def render_sockbar_preview(
    output_path: Path,
    *,
    title: str,
    categories: list[str],
    hue_labels: list[str],
    values: list[list[float]],
    hue_inner_gap: PreviewHueInnerGap,
    group_gap: int,
    legend_ncol: int = 1,
) -> None:
    """Render one grouped preview image."""
    fig, ax = plt.subplots(figsize=(12, 5.6))
    zp.sockbar(
        values_by_hue(hue_labels, values),
        label=categories,
        ax=ax,
        hue_textures=hue_specs(len(hue_labels)),
        hue_inner_gap=hue_inner_gap,
        group_gap=group_gap,
        legend_kwargs={
            "loc": "upper right",
            "frameon": True,
            "fontsize": 11,
            "ncol": legend_ncol,
        },
        seed=20260524,
    )
    ax.set_title(title, fontsize=15)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def render_two_hue_original_pair(output_dir: Path) -> None:
    """Render two-hue groups using original source-pair spacing."""
    categories = [f"day {index + 1}" for index in range(5)]
    values: list[list[float]] = []
    for index in range(len(categories)):
        values.append([0.36 + index * 0.09, 0.68 - index * 0.05])
    render_sockbar_preview(
        output_dir / "two_hue_original_pair_gap.png",
        title="2 hue items: original source-pair gaps, wider group spacing",
        categories=categories,
        hue_labels=["A", "B"],
        values=values,
        hue_inner_gap="auto",
        group_gap=120,
        legend_ncol=2,
    )


def render_grouped_spacing_and_overlap(output_dir: Path) -> None:
    """Render spacing and negative-gap overlap variants in one figure."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
    variants = (
        ("default: in 14, out 80", 3, 14, 80),
        ("zero inner: in 0, out 80", 3, 0, 80),
        ("loose: in 26, out 112", 3, 26, 112),
        ("overlap 3 legs: in -18, out 112", 3, -18, 112),
        ("overlap 4 legs: in -34, out 112", 4, -34, 112),
        ("overlap 5 legs: in -50, out 112", 5, -50, 112),
    )
    for ax, (title, hue_count, inner_gap, group_gap) in zip(axes.flat, variants, strict=True):
        categories = ["day 1", "day 2", "day 3"]
        hue_labels = [chr(ord("A") + index) for index in range(hue_count)]
        values: list[list[float]] = []
        for category_index in range(len(categories)):
            row: list[float] = []
            for hue_index in range(hue_count):
                row.append(0.32 + 0.12 * category_index + 0.1 * hue_index)
            values.append(row)
        zp.sockbar(
            values_by_hue(hue_labels, values),
            label=categories,
            ax=ax,
            hue_textures=hue_specs(hue_count),
            hue_inner_gap=inner_gap,
            group_gap=group_gap,
            legend_kwargs={
                "loc": "upper right",
                "frameon": True,
                "fontsize": 8,
                "ncol": -2,
            },
            seed=20260524,
        )
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(output_dir / "hue_spacing_and_overlap_variants.png", dpi=150)
    plt.close(fig)


def values_by_hue(
    hue_labels: list[str],
    rows: list[list[float]],
) -> dict[str, list[float]]:
    """Convert row-major preview values into sockbar's mapping input."""
    return {
        hue_label: [row[hue_index] for row in rows]
        for hue_index, hue_label in enumerate(hue_labels)
    }


def main() -> None:
    """Generate grouped sockbar layout previews."""
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    render_two_hue_original_pair(output_dir)
    render_grouped_spacing_and_overlap(output_dir)
    print(f"Wrote grouped previews to {output_dir}")


if __name__ == "__main__":
    main()

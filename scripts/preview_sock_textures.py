# ruff: noqa: E402
"""Generate staged previews for procedural sock texture categories."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zettaiplot.textures import (
    FishnetSpec,
    GradientSheerSpec,
    HorizontalStripesSpec,
    LaceTopSpec,
    OpaqueSpec,
    PaletteSpec,
    PalettePreset,
    PolkaDotSpec,
    RibbedSpec,
    SheerSpec,
    SockTextureSpec,
    render_sock_texture,
)


type ParameterKind = Literal["enum", "number", "bool"]

DEFAULT_SPLIT_DIR = PROJECT_ROOT / "assets" / "split"
DEFAULT_PAIR_ID = 10
DEFAULT_COVERAGE_RATIO = 0.72


class PreviewParameter:
    """A single texture parameter sweep definition."""

    def __init__(
        self,
        name: str,
        kind: ParameterKind,
        values: tuple[object, ...],
    ) -> None:
        """Initialize the preview parameter."""
        self.name = name
        self.kind = kind
        self.values = values


class TexturePreview:
    """Preview definition for one sock texture category."""

    def __init__(
        self,
        name: str,
        default_spec: SockTextureSpec,
        parameters: tuple[PreviewParameter, ...],
    ) -> None:
        """Initialize the texture preview definition."""
        self.name = name
        self.default_spec = default_spec
        self.parameters = parameters


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate texture preview sheets for split leg assets.",
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=DEFAULT_SPLIT_DIR,
        help="Directory containing manifest.json and split leg assets.",
    )
    parser.add_argument(
        "--pair-id",
        type=int,
        default=DEFAULT_PAIR_ID,
        help="Source pair id used for every texture preview sample.",
    )
    parser.add_argument(
        "--coverage-ratio",
        type=float,
        default=DEFAULT_COVERAGE_RATIO,
        help="Fixed sock coverage ratio for texture previews.",
    )
    return parser.parse_args()


def load_manifest(split_dir: Path) -> dict[str, object]:
    """Load split asset manifest."""
    return json.loads((split_dir / "manifest.json").read_text(encoding="utf-8"))


def pair_asset_paths(
    split_dir: Path,
    manifest: dict[str, object],
    pair_id: int,
) -> tuple[Path, Path]:
    """Return left and right leg paths for a source pair."""
    raw_pairs = manifest.get("source_pairs")
    raw_assets = manifest.get("assets")
    if not isinstance(raw_pairs, list) or not isinstance(raw_assets, list):
        raise TypeError("manifest must contain source_pairs and assets lists")

    pair = next(  # pyright: ignore[reportUnknownVariableType]
        (  # pyright: ignore[reportUnknownArgumentType]
            candidate
            for candidate in raw_pairs  # pyright: ignore[reportUnknownVariableType]
            if isinstance(candidate, dict) and candidate.get("pair_id") == pair_id
        ),
        None,
    )
    if pair is None:
        raise ValueError(f"pair_id {pair_id} was not found in manifest")

    paths_by_id: dict[str, Path] = {}
    for raw_asset in raw_assets:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(raw_asset, dict):
            continue
        asset_id = raw_asset.get("asset_id")  # pyright: ignore[reportUnknownVariableType]
        path_value = raw_asset.get("path")  # pyright: ignore[reportUnknownVariableType]
        if isinstance(asset_id, str) and isinstance(path_value, str):
            paths_by_id[asset_id] = split_dir / path_value

    left_id = pair.get("left_asset_id")  # pyright: ignore[reportUnknownVariableType]
    right_id = pair.get("right_asset_id")  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(left_id, str) or not isinstance(right_id, str):
        raise TypeError("source pair must contain left_asset_id and right_asset_id")
    return paths_by_id[left_id], paths_by_id[right_id]


def texture_previews() -> tuple[TexturePreview, ...]:
    """Return all texture preview definitions."""
    colors = ("black", "white", "pink", "navy", "brown")
    palettes = ("mono_black", "school", "candy", "classic")
    return (
        TexturePreview(
            "opaque",
            OpaqueSpec(),
            (
                PreviewParameter("color", "enum", colors),
                PreviewParameter("opacity", "number", floats(0.45, 0.95)),
                PreviewParameter("edge_shadow", "number", floats(0.0, 0.45)),
                PreviewParameter("cuff_height", "number", ints(0, 40)),
            ),
        ),
        TexturePreview(
            "sheer",
            SheerSpec(),
            (
                PreviewParameter("color", "enum", colors),
                PreviewParameter("denier", "number", floats(8, 120)),
                PreviewParameter("edge_enrichment", "number", floats(0.0, 0.7)),
                PreviewParameter("grain_strength", "number", floats(0.0, 0.18)),
            ),
        ),
        TexturePreview(
            "gradient_sheer",
            GradientSheerSpec(),
            (
                PreviewParameter("color", "enum", colors),
                PreviewParameter("top_opacity", "number", floats(0.25, 0.85)),
                PreviewParameter("bottom_opacity", "number", floats(0.08, 0.6)),
                PreviewParameter(
                    "gradient_curve", "enum", ("linear", "ease_in", "ease_out")
                ),
            ),
        ),
        TexturePreview(
            "horizontal_stripes",
            HorizontalStripesSpec(),
            (
                PreviewParameter("palette", "enum", palettes),
                PreviewParameter("stripe_height", "number", ints(8, 34)),
                PreviewParameter("gap_height", "number", ints(6, 28)),
                PreviewParameter("warp_strength", "number", floats(0.0, 0.9)),
            ),
        ),
        TexturePreview(
            "ribbed",
            RibbedSpec(),
            (
                PreviewParameter("color", "enum", colors),
                PreviewParameter("rib_spacing", "number", ints(5, 20)),
                PreviewParameter("rib_depth", "number", floats(0.0, 0.5)),
                PreviewParameter("highlight_strength", "number", floats(0.0, 0.4)),
            ),
        ),
        TexturePreview(
            "fishnet",
            FishnetSpec(),
            (
                PreviewParameter("color", "enum", colors),
                PreviewParameter("cell_size", "number", ints(16, 52)),
                PreviewParameter("line_width", "number", ints(1, 5)),
                PreviewParameter("angle", "number", floats(28, 62)),
            ),
        ),
        TexturePreview(
            "polka_dot",
            PolkaDotSpec(),
            (
                PreviewParameter("palette", "enum", palettes),
                PreviewParameter("dot_radius", "number", ints(2, 10)),
                PreviewParameter("dot_spacing", "number", ints(14, 38)),
                PreviewParameter("staggered", "bool", (False, True)),
            ),
        ),
        TexturePreview(
            "lace_top",
            LaceTopSpec(),
            (
                PreviewParameter("base_style", "enum", ("opaque", "sheer")),
                PreviewParameter("lace_height", "number", ints(22, 74)),
                PreviewParameter("motif_scale", "number", ints(8, 24)),
                PreviewParameter("lace_opacity", "number", floats(0.35, 0.95)),
            ),
        ),
    )


def floats(start: float, end: float, count: int = 5) -> tuple[float, ...]:
    """Return evenly spaced float samples."""
    if count == 1:
        return (start,)
    step = (end - start) / (count - 1)
    return tuple(round(start + step * index, 3) for index in range(count))


def ints(start: int, end: int, count: int = 5) -> tuple[int, ...]:
    """Return evenly spaced integer samples."""
    if count == 1:
        return (start,)
    step = (end - start) / (count - 1)
    return tuple(round(start + step * index) for index in range(count))


def make_spec_sample(
    base_spec: SockTextureSpec,
    parameter: PreviewParameter,
    value: object,
) -> SockTextureSpec:
    """Return a spec with one preview parameter changed."""
    if parameter.name == "palette" and isinstance(value, str):
        return replace(
            base_spec, palette=PaletteSpec(preset=cast(PalettePreset, value))
        )
    return replace(base_spec, **{parameter.name: value})


def render_pair_sample(
    left_leg: Image.Image,
    right_leg: Image.Image,
    spec: SockTextureSpec,
    label: str,
    coverage_ratio: float,
) -> Image.Image:
    """Render one labeled pair sample for a preview sheet."""
    left = render_sock_texture(left_leg, spec, coverage_ratio=coverage_ratio)
    right = render_sock_texture(right_leg, spec, coverage_ratio=coverage_ratio)
    pair_gap = 14
    label_height = 24
    padding_x = 12
    sample_width = left.width + pair_gap + right.width + padding_x * 2
    sample_height = left.height + label_height + 8
    sample = Image.new("RGBA", (sample_width, sample_height), "white")
    draw = ImageDraw.Draw(sample)
    font = ImageFont.load_default()
    left_x = padding_x
    right_x = left_x + left.width + pair_gap
    sample.alpha_composite(left, (left_x, label_height))
    sample.alpha_composite(right, (right_x, label_height))
    draw.text((padding_x, 6), label, fill=(36, 36, 36, 255), font=font)
    return sample


def render_preview_sheet(
    preview: TexturePreview,
    left_leg: Image.Image,
    right_leg: Image.Image,
    output_path: Path,
    coverage_ratio: float,
) -> None:
    """Render one texture kind preview sheet."""
    samples: list[Image.Image] = []
    for parameter in preview.parameters:
        for value in parameter.values:
            spec = make_spec_sample(preview.default_spec, parameter, value)
            label = f"{parameter.name}={format_value(value)}"
            samples.append(
                render_pair_sample(
                    left_leg,
                    right_leg,
                    spec,
                    label,
                    coverage_ratio=coverage_ratio,
                ),
            )

    columns = 4
    gap = 12
    title_height = 30
    cell_width = max(sample.width for sample in samples)
    cell_height = max(sample.height for sample in samples)
    rows = (len(samples) + columns - 1) // columns
    sheet_width = columns * cell_width + (columns + 1) * gap
    sheet_height = title_height + rows * cell_height + (rows + 1) * gap
    sheet = Image.new("RGBA", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((gap, 8), preview.name, fill=(20, 20, 20, 255), font=font)

    for index, sample in enumerate(samples):
        row, column = divmod(index, columns)
        x = gap + column * (cell_width + gap)
        y = title_height + gap + row * (cell_height + gap)
        draw.rectangle(
            (x - 1, y - 1, x + cell_width, y + cell_height),
            outline=(224, 224, 224, 255),
        )
        sheet.alpha_composite(sample, (x, y))

    sheet.convert("RGB").save(output_path)


def format_value(value: object) -> str:
    """Format a preview parameter value for labels."""
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def main() -> None:
    """Run the texture preview generation pipeline."""
    args = parse_args()
    split_dir = args.split_dir.resolve()
    manifest = load_manifest(split_dir)
    left_path, right_path = pair_asset_paths(split_dir, manifest, args.pair_id)
    with Image.open(left_path) as left_image:
        left_leg = left_image.convert("RGBA")
    with Image.open(right_path) as right_image:
        right_leg = right_image.convert("RGBA")

    output_dir = split_dir / "texture_previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    for preview in texture_previews():
        render_preview_sheet(
            preview,
            left_leg,
            right_leg,
            output_dir / f"{preview.name}.png",
            coverage_ratio=args.coverage_ratio,
        )
    print(f"Wrote texture previews to {output_dir}")


if __name__ == "__main__":
    main()

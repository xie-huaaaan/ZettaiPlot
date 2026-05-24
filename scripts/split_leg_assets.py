"""Split transparent row images into tight-cropped leg assets.

This temporary maintenance script reads the source leg rows from ``assets``
and writes individual leg PNGs plus a compact manifest.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from PIL import Image, ImageDraw, ImageFont

from zettaiplot._pillow import flattened_pixels


type BBox = tuple[int, int, int, int]

DEFAULT_AREA_THRESHOLD = 5_000
SOURCE_PATTERN = "row*.png"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "assets"
DEFAULT_OUTPUT_DIR = DEFAULT_ASSETS_DIR / "split"


@dataclass(frozen=True)
class Component:
    """Alpha connected component detected in a source image."""

    bbox: BBox
    area: int

    @property
    def width(self) -> int:
        """Return the component bbox width."""
        left, _, right, _ = self.bbox
        return right - left + 1

    @property
    def height(self) -> int:
        """Return the component bbox height."""
        _, top, _, bottom = self.bbox
        return bottom - top + 1


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Split RGBA row PNGs into individual tight-cropped leg assets.",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=DEFAULT_ASSETS_DIR,
        help="Directory containing source row PNGs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where split assets and manifest are written.",
    )
    parser.add_argument(
        "--area-threshold",
        type=int,
        default=DEFAULT_AREA_THRESHOLD,
        help="Minimum alpha-component area treated as a leg.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing output directory instead of recreating it.",
    )
    return parser.parse_args()


def alpha_mask(image: Image.Image) -> list[bool]:
    """Return a boolean alpha mask for an RGBA image."""
    alpha = image.getchannel("A")
    return [
        isinstance(value, int | float) and value > 0
        for value in flattened_pixels(alpha)
    ]


def alpha_components(image: Image.Image) -> list[Component]:
    """Find 8-neighbor connected components in the image alpha channel."""
    width, height = image.size
    mask = alpha_mask(image)
    components: list[Component] = []

    for start_index, has_alpha in enumerate(mask):
        if not has_alpha:
            continue

        mask[start_index] = False
        queue: deque[int] = deque([start_index])
        area = 0
        min_x = width
        min_y = height
        max_x = -1
        max_y = -1

        while queue:
            index = queue.popleft()
            y, x = divmod(index, width)
            area += 1
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

            for neighbor_y in range(max(0, y - 1), min(height, y + 2)):
                row_offset = neighbor_y * width
                for neighbor_x in range(max(0, x - 1), min(width, x + 2)):
                    if neighbor_x == x and neighbor_y == y:
                        continue
                    neighbor_index = row_offset + neighbor_x
                    if mask[neighbor_index]:
                        mask[neighbor_index] = False
                        queue.append(neighbor_index)

        components.append(Component((min_x, min_y, max_x, max_y), area))

    return sorted(components, key=lambda component: component.bbox[0])


def crop_leg_full_height(image: Image.Image, bbox: BBox) -> Image.Image:
    """Crop a leg horizontally while preserving the full source height."""
    left, _, right, _ = bbox
    width, height = image.size
    crop_box = (max(0, left), 0, min(width, right + 1), height)
    return image.crop(crop_box)


def component_summary(component: Component) -> dict[str, int | list[int]]:
    """Return an audit-friendly component summary."""
    return {
        "bbox": list(component.bbox),
        "area": component.area,
    }


def residue_summary(components: list[Component]) -> dict[str, object]:
    """Summarize ignored residue components without storing every tiny pixel detail."""
    if not components:
        return {
            "count": 0,
            "max_area": 0,
            "examples": [],
        }

    largest = sorted(components, key=lambda component: component.area, reverse=True)[:8]
    return {
        "count": len(components),
        "max_area": largest[0].area,
        "examples": [component_summary(component) for component in largest],
    }


def reset_output_dir(path: Path, keep_existing: bool) -> None:
    """Prepare a clean output directory."""
    if path.exists() and not keep_existing:
        shutil.rmtree(path)
    (path / "legs").mkdir(parents=True, exist_ok=True)


def split_assets(
    assets_dir: Path,
    output_dir: Path,
    area_threshold: int,
) -> dict[str, object]:
    """Split all source rows and return the manifest data."""
    source_paths = sorted(assets_dir.glob(SOURCE_PATTERN))
    if not source_paths:
        raise FileNotFoundError(f"No source images matched {assets_dir / SOURCE_PATTERN}")

    assets: list[dict[str, object]] = []
    source_pairs: list[dict[str, object]] = []
    source_diagnostics: list[dict[str, object]] = []
    widths: list[int] = []
    pair_widths: list[int] = []
    pair_id = 0

    for source_path in source_paths:
        with Image.open(source_path) as source_image:
            image = source_image.convert("RGBA")

        components = alpha_components(image)
        leg_components = [
            component for component in components if component.area >= area_threshold
        ]
        residue_components = [
            component for component in components if component.area < area_threshold
        ]

        if len(leg_components) % 2 != 0:
            raise ValueError(
                f"{source_path} produced an odd number of leg components: "
                f"{len(leg_components)}"
            )

        source_diagnostics.append(
            {
                "source_file": source_path.name,
                "source_size": list(image.size),
                "component_count": len(components),
                "leg_component_count": len(leg_components),
                "ignored_residue": residue_summary(residue_components),
            },
        )

        for source_pair_index in range(0, len(leg_components), 2):
            left_component = leg_components[source_pair_index]
            right_component = leg_components[source_pair_index + 1]
            pair_components = {"l": left_component, "r": right_component}
            left_bbox = left_component.bbox
            right_bbox = right_component.bbox
            pair_bbox = (
                min(left_bbox[0], right_bbox[0]),
                min(left_bbox[1], right_bbox[1]),
                max(left_bbox[2], right_bbox[2]),
                max(left_bbox[3], right_bbox[3]),
            )
            pair_gap = right_bbox[0] - left_bbox[2] - 1
            pair_width = pair_bbox[2] - pair_bbox[0] + 1
            pair_widths.append(pair_width)
            pair_asset_ids: dict[str, str] = {}

            for side, component in pair_components.items():
                asset_id = f"leg_{pair_id}_{side}"
                asset_path = output_dir / "legs" / f"{asset_id}.png"
                cropped = crop_leg_full_height(image, component.bbox)
                cropped.save(asset_path)
                widths.append(cropped.width)
                pair_asset_ids[side] = asset_id
                assets.append(
                    {
                        "asset_id": asset_id,
                        "side": side,
                        "path": asset_path.relative_to(output_dir).as_posix(),
                        "source_file": source_path.name,
                        "source_bbox": list(component.bbox),
                        "source_pair_id": pair_id,
                    },
                )

            source_pairs.append(
                {
                    "pair_id": pair_id,
                    "source_file": source_path.name,
                    "left_asset_id": pair_asset_ids["l"],
                    "right_asset_id": pair_asset_ids["r"],
                    "original_pair_gap": pair_gap,
                    "original_pair_bbox": list(pair_bbox),
                },
            )
            pair_id += 1

    diagnostics = {
        "total_legs": len(assets),
        "total_pairs": len(source_pairs),
        "area_threshold": area_threshold,
        "single_leg_width": width_stats(widths),
        "source_pair_width": width_stats(pair_widths),
        "sources": source_diagnostics,
    }

    return {
        "schema_version": 1,
        "assets": assets,
        "source_pairs": source_pairs,
        "diagnostics": diagnostics,
    }


def width_stats(values: list[int]) -> dict[str, float | int]:
    """Return compact width statistics."""
    if not values:
        return {
            "min": 0,
            "mean": 0.0,
            "max": 0,
        }
    return {
        "min": min(values),
        "mean": round(mean(values), 2),
        "max": max(values),
    }


def save_manifest(manifest: dict[str, object], output_dir: Path) -> None:
    """Write the manifest JSON file."""
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def asset_by_id(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return manifest assets keyed by asset id."""
    assets = manifest["assets"]
    if not isinstance(assets, list):
        raise TypeError("manifest assets must be a list")
    return {
        asset["asset_id"]: asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("asset_id"), str)
    }


def make_contact_sheet(manifest: dict[str, object], output_dir: Path) -> None:
    """Generate a compact visual preview of the split assets."""
    pairs = manifest["source_pairs"]
    if not isinstance(pairs, list):
        raise TypeError("manifest source_pairs must be a list")

    assets = asset_by_id(manifest)
    cell_width = 230
    cell_height = 250
    label_height = 26
    columns = 4
    rows = math.ceil(len(pairs) / columns)
    sheet = Image.new("RGBA", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            continue
        row, column = divmod(index, columns)
        origin_x = column * cell_width
        origin_y = row * cell_height
        draw.rectangle(
            (origin_x, origin_y, origin_x + cell_width - 1, origin_y + cell_height - 1),
            outline=(220, 220, 220, 255),
        )
        pair_id = pair["pair_id"]
        draw.text(
            (origin_x + 8, origin_y + 6),
            f"pair {pair_id} | {pair['source_file']}",
            fill=(20, 20, 20, 255),
            font=font,
        )

        for side_index, side in enumerate(("l", "r")):
            asset_key = "left_asset_id" if side == "l" else "right_asset_id"
            asset_id = pair[asset_key]
            asset = assets[asset_id]
            leg_path = output_dir / str(asset["path"])
            with Image.open(leg_path) as image:
                leg = image.convert("RGBA")
            preview_height = cell_height - label_height - 18
            scale = preview_height / leg.height
            preview_width = max(1, round(leg.width * scale))
            preview = leg.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            center_x = origin_x + (cell_width * (side_index + 1) // 3)
            paste_x = center_x - preview.width // 2
            paste_y = origin_y + label_height + 10
            sheet.alpha_composite(preview, (paste_x, paste_y))
            draw.text(
                (center_x - 22, origin_y + cell_height - 18),
                str(asset_id),
                fill=(70, 70, 70, 255),
                font=font,
            )

    sheet.convert("RGB").save(output_dir / "preview_contact_sheet.png")


def main() -> None:
    """Run the asset split pipeline."""
    args = parse_args()
    output_dir = args.output_dir.resolve()
    reset_output_dir(output_dir, keep_existing=args.keep_existing)
    manifest = split_assets(
        assets_dir=args.assets_dir.resolve(),
        output_dir=output_dir,
        area_threshold=args.area_threshold,
    )
    save_manifest(manifest, output_dir)
    make_contact_sheet(manifest, output_dir)
    diagnostics = manifest["diagnostics"]
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

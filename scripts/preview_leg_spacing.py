"""Generate spacing-only mock chart previews from split leg assets."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


type OddSingle = str

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SPLIT_DIR = PROJECT_ROOT / "assets" / "split"
ALLOWED_ODD_POLICIES = ("left", "center", "right")


@dataclass(frozen=True)
class LegAsset:
    """A split leg asset loaded from the manifest."""

    asset_id: str
    side: str
    path: Path
    width: int
    height: int


@dataclass(frozen=True)
class PositionedLeg:
    """A leg selected for one mock chart category."""

    category_index: int
    asset: LegAsset
    is_single: bool


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate spacing-only mock chart previews for split leg assets.",
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=DEFAULT_SPLIT_DIR,
        help="Directory containing manifest.json and split leg assets.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260522,
        help="Random seed used for reproducible sampling.",
    )
    parser.add_argument(
        "--even-count",
        type=int,
        default=8,
        help="Number of categories in the even-count spacing preview.",
    )
    parser.add_argument(
        "--odd-count",
        type=int,
        default=9,
        help="Number of categories in odd-count spacing previews.",
    )
    return parser.parse_args()


def load_manifest(split_dir: Path) -> dict[str, object]:
    """Load the split asset manifest."""
    manifest_path = split_dir / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_assets(split_dir: Path, manifest: dict[str, object]) -> list[LegAsset]:
    """Load asset dimensions from image files referenced by the manifest."""
    raw_assets = manifest.get("assets")
    if not isinstance(raw_assets, list):
        raise TypeError("manifest assets must be a list")

    assets: list[LegAsset] = []
    for raw_asset in raw_assets:
        if not isinstance(raw_asset, dict):
            continue
        path_value = raw_asset.get("path")
        asset_id = raw_asset.get("asset_id")
        side = raw_asset.get("side")
        if not isinstance(path_value, str):
            raise TypeError("asset path must be a string")
        if not isinstance(asset_id, str):
            raise TypeError("asset_id must be a string")
        if side not in {"l", "r"}:
            raise ValueError(f"unexpected side for {asset_id}: {side}")
        asset_path = split_dir / path_value
        with Image.open(asset_path) as image:
            width, height = image.size
        assets.append(
            LegAsset(
                asset_id=asset_id,
                side=side,
                path=asset_path,
                width=width,
                height=height,
            ),
        )
    return assets


def odd_single_index(count: int, policy: OddSingle) -> int | None:
    """Return the category index that should remain visually unpaired."""
    if count % 2 == 0:
        return None
    if policy == "left":
        return 0
    if policy == "center":
        return count // 2
    if policy == "right":
        return count - 1
    raise ValueError(f"Unsupported odd policy: {policy}")


def choose_asset(rng: random.Random, assets_by_side: dict[str, list[LegAsset]], side: str) -> LegAsset:
    """Choose a leg asset for a side."""
    return rng.choice(assets_by_side[side])


def sample_chart_legs(
    assets: list[LegAsset],
    count: int,
    odd_policy: OddSingle,
    seed: int,
) -> list[PositionedLeg]:
    """Sample one leg per category while respecting odd-single placement."""
    if count < 1:
        raise ValueError("count must be positive")
    if odd_policy not in ALLOWED_ODD_POLICIES:
        raise ValueError(f"odd_policy must be one of {ALLOWED_ODD_POLICIES}")

    assets_by_side = {
        "l": [asset for asset in assets if asset.side == "l"],
        "r": [asset for asset in assets if asset.side == "r"],
    }
    if not assets_by_side["l"] or not assets_by_side["r"]:
        raise ValueError("both left and right leg assets are required")

    rng = random.Random(seed)
    single_index = odd_single_index(count, odd_policy)
    positioned: list[PositionedLeg] = []
    next_pair_side = "l"

    for category_index in range(count):
        is_single = category_index == single_index
        if is_single:
            side = rng.choice(("l", "r"))
        else:
            side = next_pair_side
            next_pair_side = "r" if next_pair_side == "l" else "l"
        positioned.append(
            PositionedLeg(
                category_index=category_index,
                asset=choose_asset(rng, assets_by_side, side),
                is_single=is_single,
            ),
        )

    return positioned


def adaptive_slot_width(positioned: list[PositionedLeg]) -> int:
    """Compute spacing from the sampled assets for the mock chart."""
    max_width = max(item.asset.width for item in positioned)
    mean_width = sum(item.asset.width for item in positioned) / len(positioned)
    return round(max(max_width * 1.2, mean_width + 54))


def render_preview(
    positioned: list[PositionedLeg],
    output_path: Path,
    title: str,
) -> None:
    """Render one spacing-only preview image."""
    slot_width = adaptive_slot_width(positioned)
    top_padding = 36
    bottom_padding = 28
    side_padding = 52
    baseline_y = top_padding + 720
    canvas_width = side_padding * 2 + slot_width * len(positioned)
    canvas_height = baseline_y + bottom_padding
    canvas = Image.new("RGBA", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.text((side_padding, 10), title, fill=(40, 40, 40, 255), font=font)
    draw.line(
        (side_padding // 2, baseline_y, canvas_width - side_padding // 2, baseline_y),
        fill=(215, 215, 215, 255),
        width=1,
    )

    for item in positioned:
        center_x = side_padding + slot_width * item.category_index + slot_width // 2
        with Image.open(item.asset.path) as image:
            leg = image.convert("RGBA")
        anchor_x = (leg.width - 1) / 2
        draw_x = round(center_x - anchor_x)
        draw_y = baseline_y - (leg.height - 1)
        canvas.alpha_composite(leg, (draw_x, draw_y))
        label = f"{item.category_index}:{item.asset.side}"
        if item.is_single:
            label += "*"
        label_bbox = draw.textbbox((0, 0), label, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text(
            (center_x - label_width // 2, baseline_y + 8),
            label,
            fill=(70, 70, 70, 255),
            font=font,
        )

    canvas.convert("RGB").save(output_path)


def main() -> None:
    """Run the spacing preview pipeline."""
    args = parse_args()
    split_dir = args.split_dir.resolve()
    manifest = load_manifest(split_dir)
    assets = load_assets(split_dir, manifest)
    output_dir = split_dir / "spacing_previews"
    output_dir.mkdir(parents=True, exist_ok=True)

    even_legs = sample_chart_legs(
        assets=assets,
        count=args.even_count,
        odd_policy="center",
        seed=args.seed,
    )
    render_preview(
        even_legs,
        output_dir / "spacing_even.png",
        f"even count={args.even_count}",
    )

    for offset, policy in enumerate(ALLOWED_ODD_POLICIES):
        odd_legs = sample_chart_legs(
            assets=assets,
            count=args.odd_count,
            odd_policy=policy,
            seed=args.seed + offset + 1,
        )
        render_preview(
            odd_legs,
            output_dir / f"spacing_odd_{policy}.png",
            f"odd count={args.odd_count} policy={policy}",
        )

    print(f"Wrote spacing previews to {output_dir}")


if __name__ == "__main__":
    main()

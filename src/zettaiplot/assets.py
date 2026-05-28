"""Packaged leg asset loading."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable

from PIL import Image


@dataclass(frozen=True)
class LegAsset:
    """A packaged split leg asset."""

    asset_id: str
    side: str
    relative_path: str
    resource: Traversable
    source_pair_id: int
    width: int
    height: int


@dataclass(frozen=True)
class SourcePair:
    """Original source-pair metadata."""

    pair_id: int
    left_asset_id: str
    right_asset_id: str
    original_pair_gap: int


@dataclass(frozen=True)
class LegAssetLibrary:
    """Packaged leg asset library."""

    assets: dict[str, LegAsset]
    pairs: dict[int, SourcePair]

    def assets_by_side(self, side: str) -> list[LegAsset]:
        """Return assets matching a side label."""
        return [asset for asset in self.assets.values() if asset.side == side]


def load_default_assets() -> LegAssetLibrary:
    """Load the packaged default leg asset library."""
    root = resources.files("zettaiplot") / "assets" / "split"
    manifest_path = root / "manifest.json"
    with resources.as_file(manifest_path) as manifest_file:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    return load_asset_library_from_split(root, manifest)


def load_asset_library_from_split(
    split_root: Traversable,
    manifest: Mapping[str, object],
) -> LegAssetLibrary:
    """Load an asset library from a split-root traversable and manifest."""
    raw_assets = manifest.get("assets")
    raw_pairs = manifest.get("source_pairs")
    if not isinstance(raw_assets, list) or not isinstance(raw_pairs, list):
        raise TypeError("manifest must contain assets and source_pairs lists")

    assets: dict[str, LegAsset] = {}
    for raw_asset in raw_assets:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(raw_asset, dict):
            continue
        asset_id = require_str(raw_asset, "asset_id")  # pyright: ignore[reportUnknownArgumentType]
        relative_path = require_str(raw_asset, "path")  # pyright: ignore[reportUnknownArgumentType]
        image_resource = split_root / relative_path
        with image_resource.open("rb") as image_file, Image.open(image_file) as image:
            width, height = image.size
        assets[asset_id] = LegAsset(
            asset_id=asset_id,
            side=require_str(raw_asset, "side"),  # pyright: ignore[reportUnknownArgumentType]
            relative_path=relative_path,
            resource=image_resource,
            source_pair_id=require_int(raw_asset, "source_pair_id"),  # pyright: ignore[reportUnknownArgumentType]
            width=width,
            height=height,
        )

    pairs: dict[int, SourcePair] = {}
    for raw_pair in raw_pairs:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(raw_pair, dict):
            continue
        pair_id = require_int(raw_pair, "pair_id")  # pyright: ignore[reportUnknownArgumentType]
        pairs[pair_id] = SourcePair(
            pair_id=pair_id,
            left_asset_id=require_str(raw_pair, "left_asset_id"),  # pyright: ignore[reportUnknownArgumentType]
            right_asset_id=require_str(raw_pair, "right_asset_id"),  # pyright: ignore[reportUnknownArgumentType]
            original_pair_gap=require_int(raw_pair, "original_pair_gap"),  # pyright: ignore[reportUnknownArgumentType]
        )
    return LegAssetLibrary(assets=assets, pairs=pairs)


def open_leg(asset: LegAsset) -> Image.Image:
    """Open a leg asset as an RGBA image."""
    with asset.resource.open("rb") as image_file, Image.open(image_file) as image:
        return image.convert("RGBA")


def require_str(data: Mapping[str, object], key: str) -> str:
    """Return a required string field from a manifest object."""
    value = data.get(key)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def require_int(data: Mapping[str, object], key: str) -> int:
    """Return a required integer field from a manifest object."""
    value = data.get(key)
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value

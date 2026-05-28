"""Pixel layout rules for sock bar charts."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from zettaiplot.assets import LegAsset, LegAssetLibrary
from zettaiplot.data import SockBarRecord, unique_in_order


type OddSingle = Literal["left", "center", "right"]
type HueInnerGap = int | Literal["auto"]


@dataclass(frozen=True)
class LegPlacement:
    """A leg image placement in chart pixel coordinates."""

    record_index: int
    category_label: str
    hue_label: str | None
    center_x: float
    asset: LegAsset
    coverage_ratio: float
    value: float
    group_index: int
    hue_index: int
    zorder: int


@dataclass(frozen=True)
class CategoryPlacement:
    """A category group placement."""

    label: str
    center_x: float
    left_x: float
    right_x: float


@dataclass(frozen=True)
class SockBarLayout:
    """Computed layout for a sockbar chart."""

    placements: list[LegPlacement]
    categories: list[CategoryPlacement]
    hue_labels: list[str]
    left_x: float
    right_x: float


@dataclass(frozen=True)
class RelativeLeg:
    """A leg placement relative to one category group."""

    record: SockBarRecord
    hue_index: int
    asset: LegAsset
    center_x: float
    zorder: int


def compute_sockbar_layout(
    records: Sequence[SockBarRecord],
    normalized_values: Sequence[float],
    library: LegAssetLibrary,
    *,
    hue_inner_gap: HueInnerGap = "auto",
    group_gap: int = 80,
    odd_single: OddSingle = "center",
    seed: int | None = None,
) -> SockBarLayout:
    """Compute category and hue leg positions in fixed pixel units."""
    validate_odd_single(odd_single)
    if len(records) != len(normalized_values):
        raise ValueError("records and normalized_values must have the same length")
    if not records:
        raise ValueError("sockbar requires at least one record")

    categories = unique_in_order(record.category_label for record in records)
    hue_labels = unique_in_order(
        record.hue_label for record in records if record.hue_label is not None
    )
    records_by_category = group_records_by_category(records, categories, hue_labels)
    rng = random.Random(seed)

    if hue_labels:
        relative_groups = [
            relative_hue_group(
                category_records,
                category_index,
                hue_labels,
                library,
                hue_inner_gap,
            )
            for category_index, category_records in enumerate(records_by_category)
        ]
    else:
        relative_groups = relative_single_groups(records, library, odd_single, rng)

    placements: list[LegPlacement] = []
    category_placements: list[CategoryPlacement] = []
    cursor = 0.0
    value_by_record = {
        record.index: normalized_values[position]
        for position, record in enumerate(records)
    }

    for group_index, (category_label, relative_group) in enumerate(
        zip(categories, relative_groups, strict=True),
    ):
        left, right = group_bounds(relative_group)
        shift = cursor - left
        absolute_centers = [relative.center_x + shift for relative in relative_group]
        category_left = min(
            center - relative.asset.width / 2
            for center, relative in zip(absolute_centers, relative_group, strict=True)
        )
        category_right = max(
            center + relative.asset.width / 2
            for center, relative in zip(absolute_centers, relative_group, strict=True)
        )
        category_center = (category_left + category_right) / 2
        category_placements.append(
            CategoryPlacement(
                label=category_label,
                center_x=category_center,
                left_x=category_left,
                right_x=category_right,
            ),
        )
        for center_x, relative in zip(absolute_centers, relative_group, strict=True):
            placements.append(
                LegPlacement(
                    record_index=relative.record.index,
                    category_label=relative.record.category_label,
                    hue_label=relative.record.hue_label,
                    center_x=center_x,
                    asset=relative.asset,
                    coverage_ratio=value_by_record[relative.record.index],
                    value=relative.record.value,
                    group_index=group_index,
                    hue_index=relative.hue_index,
                    zorder=relative.zorder,
                ),
            )
        cursor = category_right + group_gap

    left_x = min(category.left_x for category in category_placements)
    right_x = max(category.right_x for category in category_placements)
    return SockBarLayout(
        placements=sorted(placements, key=lambda placement: placement.record_index),
        categories=category_placements,
        hue_labels=hue_labels,
        left_x=left_x,
        right_x=right_x,
    )


def validate_odd_single(policy: OddSingle) -> None:
    """Validate the odd-single policy."""
    if policy not in {"left", "center", "right"}:
        raise ValueError("odd_single must be 'left', 'center', or 'right'")


def group_records_by_category(
    records: Sequence[SockBarRecord],
    categories: Sequence[str],
    hue_labels: Sequence[str],
) -> list[list[SockBarRecord]]:
    """Group records by category and order hue records consistently."""
    hue_order = {label: index for index, label in enumerate(hue_labels)}
    grouped: list[list[SockBarRecord]] = []
    for category in categories:
        category_records = [
            record for record in records if record.category_label == category
        ]
        if hue_labels:
            category_records.sort(
                key=lambda record: hue_order.get(
                    record.hue_label or "", len(hue_order)
                ),
            )
        grouped.append(category_records)
    return grouped


def relative_hue_group(
    records: Sequence[SockBarRecord],
    category_index: int,
    hue_labels: Sequence[str],
    library: LegAssetLibrary,
    hue_inner_gap: HueInnerGap,
) -> list[RelativeLeg]:
    """Return relative placements for one hue group."""
    pair_ids = sorted(library.pairs)
    if not pair_ids:
        raise ValueError("asset library does not contain source pairs")
    pair = library.pairs[pair_ids[category_index % len(pair_ids)]]
    assets = select_hue_assets(records, hue_labels, library, pair.pair_id)

    if hue_inner_gap == "auto":
        inner_gap = pair.original_pair_gap if len(hue_labels) == 2 else 14
    elif isinstance(hue_inner_gap, int):
        inner_gap = hue_inner_gap
    else:
        raise ValueError('hue_inner_gap must be "auto" or an integer')

    total_width = sum(asset.width for asset in assets)
    total_width += inner_gap * max(0, len(assets) - 1)
    cursor = -total_width / 2
    relative: list[RelativeLeg] = []
    for local_index, (record, asset) in enumerate(zip(records, assets, strict=True)):
        center_x = cursor + asset.width / 2
        relative.append(
            RelativeLeg(
                record=record,
                hue_index=hue_labels.index(record.hue_label or ""),
                asset=asset,
                center_x=center_x,
                zorder=local_index,
            ),
        )
        cursor += asset.width + inner_gap
    return relative


def select_hue_assets(
    records: Sequence[SockBarRecord],
    hue_labels: Sequence[str],
    library: LegAssetLibrary,
    base_pair_id: int,
) -> list[LegAsset]:
    """Select alternating left/right leg assets for hue records."""
    pair_ids = sorted(library.pairs)
    selected: list[LegAsset] = []
    for record in records:
        hue_index = hue_labels.index(record.hue_label or "")
        pair = library.pairs[pair_ids[(base_pair_id + hue_index // 2) % len(pair_ids)]]
        asset_id = pair.left_asset_id if hue_index % 2 == 0 else pair.right_asset_id
        selected.append(library.assets[asset_id])
    return selected


def relative_single_groups(
    records: Sequence[SockBarRecord],
    library: LegAssetLibrary,
    odd_single: OddSingle,
    rng: random.Random,
) -> list[list[RelativeLeg]]:
    """Return one-leg category groups with odd category pairing policy."""
    pair_ids = sorted(library.pairs)
    if not pair_ids:
        raise ValueError("asset library does not contain source pairs")

    single_index = odd_single_index(len(records), odd_single)
    groups: list[list[RelativeLeg]] = []
    pair_cursor = 0
    side_cursor = "l"
    active_pair = library.pairs[pair_ids[pair_cursor % len(pair_ids)]]

    for category_index, record in enumerate(records):
        if category_index == single_index:
            random_pair = library.pairs[pair_ids[rng.randrange(len(pair_ids))]]
            use_left = rng.choice((True, False))
            asset_id = (
                random_pair.left_asset_id if use_left else random_pair.right_asset_id
            )
            asset = library.assets[asset_id]
            hue_index = 0 if asset.side == "l" else 1
        else:
            if side_cursor == "l":
                active_pair = library.pairs[pair_ids[pair_cursor % len(pair_ids)]]
                asset_id = active_pair.left_asset_id
                side_cursor = "r"
                hue_index = 0
            else:
                asset_id = active_pair.right_asset_id
                side_cursor = "l"
                pair_cursor += 1
                hue_index = 1
            asset = library.assets[asset_id]

        groups.append(
            [
                RelativeLeg(
                    record=record,
                    hue_index=hue_index,
                    asset=asset,
                    center_x=0.0,
                    zorder=0,
                ),
            ],
        )
    return groups


def odd_single_index(count: int, policy: OddSingle) -> int | None:
    """Return the unpaired index for an odd count."""
    if count % 2 == 0:
        return None
    if policy == "left":
        return 0
    if policy == "center":
        return count // 2
    return count - 1


def group_bounds(relative_group: Sequence[RelativeLeg]) -> tuple[float, float]:
    """Return the horizontal bounds of a relative group."""
    if not relative_group:
        return 0.0, 0.0
    left = min(
        relative.center_x - relative.asset.width / 2 for relative in relative_group
    )
    right = max(
        relative.center_x + relative.asset.width / 2 for relative in relative_group
    )
    return left, right

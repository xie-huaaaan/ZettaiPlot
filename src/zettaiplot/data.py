"""Input normalization for sock bar charts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np


class ColumnLookup(Protocol):
    """Protocol for DataFrame-like column access."""

    def __getitem__(self, key: str) -> object:
        """Return a column-like object by name."""


@dataclass(frozen=True)
class SockBarRecord:
    """One normalized sockbar observation."""

    index: int
    category_label: str
    value: float
    hue_label: str | None


def resolve_sockbar_records(
    x: object | None,
    height: object | None,
    hue: object | None,
    data: object | None,
) -> list[SockBarRecord]:
    """Resolve public sockbar inputs into chart records."""
    height_values = resolve_required_height(height, data)
    count = len(height_values)
    x_values = resolve_optional_values(x, data, count, "x")
    hue_values = resolve_optional_values(hue, data, count, "hue")

    records: list[SockBarRecord] = []
    for index, raw_height in enumerate(height_values):
        category = str(x_values[index]) if x_values is not None else str(index)
        hue_label = str(hue_values[index]) if hue_values is not None else None
        records.append(
            SockBarRecord(
                index=index,
                category_label=category,
                value=float(raw_height),
                hue_label=hue_label,
            ),
        )
    return records


def resolve_required_height(height: object | None, data: object | None) -> list[float]:
    """Resolve the required height/value vector."""
    if height is None:
        for column_name in ("height", "value"):
            if has_column(data, column_name):
                height = get_column(data, column_name)
                break
    elif isinstance(height, str) and data is not None:
        height = get_column(data, height)

    if height is None:
        raise ValueError("height is required unless data contains a height or value column")

    values = object_list(height)
    if not values:
        raise ValueError("height must contain at least one value")
    return [coerce_float(value) for value in values]


def resolve_optional_values(
    value: object | None,
    data: object | None,
    expected_length: int,
    name: str,
) -> list[object] | None:
    """Resolve an optional vector argument."""
    if value is None:
        return None
    if isinstance(value, str) and data is not None:
        value = get_column(data, value)
    values = object_list(value)
    if len(values) != expected_length:
        raise ValueError(
            f"{name} length {len(values)} does not match height length {expected_length}",
        )
    return values


def has_column(data: object | None, key: str) -> bool:
    """Return whether mapping/DataFrame-like data exposes a named column."""
    if data is None:
        return False
    if isinstance(data, Mapping):
        return key in data
    try:
        get_column(data, key)
    except (KeyError, TypeError, AttributeError):
        return False
    return True


def get_column(data: object | None, key: str) -> object:
    """Return a column from mapping/DataFrame-like data."""
    if data is None:
        raise KeyError(key)
    if isinstance(data, Mapping):
        return data[key]
    return cast(ColumnLookup, data)[key]


def object_list(value: object) -> list[object]:
    """Convert scalar, NumPy, pandas-like, and iterable values into a flat list."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, bytes):
        return [value]
    if isinstance(value, np.ndarray):
        return [item.item() if hasattr(item, "item") else item for item in value.reshape(-1)]
    if isinstance(value, Sequence):
        return list(value)
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    array = np.asarray(value, dtype=object)
    if array.ndim == 0:
        return [array.item()]
    return [item.item() if hasattr(item, "item") else item for item in array.reshape(-1)]


def coerce_float(value: object) -> float:
    """Convert a scalar object into a float."""
    if isinstance(value, str | bytes):
        try:
            return float(value)
        except ValueError as exc:
            raise TypeError("height values must be numeric") from exc
    if isinstance(value, int | float | np.number):
        return float(value)
    raise TypeError("height values must be numeric")


def normalize_values(records: Sequence[SockBarRecord]) -> list[float]:
    """Normalize record values into sock coverage ratios."""
    positive_max = max((record.value for record in records if record.value > 0), default=1.0)
    return [min(1.0, max(0.0, record.value / positive_max)) for record in records]


def unique_in_order(values: Iterable[str]) -> list[str]:
    """Return unique strings while preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

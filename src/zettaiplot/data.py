"""Input normalization for sock bar charts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np


MAX_COVERAGE_RATIO = 0.8


@dataclass(frozen=True)
class SockBarRecord:
    """One normalized sockbar observation."""

    index: int
    category_label: str
    value: float
    hue_label: str | None


def resolve_sockbar_records(data: object, label: object | None = None) -> list[SockBarRecord]:
    """Resolve public wide-form sockbar inputs into internal records.

    Args:
        data: Numeric values. Accepted forms are a one-dimensional sequence,
            a two-dimensional matrix, or a mapping of hue label to numeric sequence.
        label: Optional category labels. When omitted, integer labels are generated.

    Returns:
        A row-major list of strict internal records. Grouped inputs are expanded so
        every category/hue item becomes one record.
    """
    mapped = mapping_columns(data)
    if mapped is not None:
        hue_labels = [hue_label for hue_label, _ in mapped]
        columns = [values for _, values in mapped]
        category_labels = resolve_category_labels(label, len(columns[0]))
        return records_from_columns(category_labels, hue_labels, columns)

    matrix = object_matrix(data)
    if matrix is not None:
        category_labels = resolve_category_labels(label, len(matrix))
        hue_labels = [str(index) for index in range(len(matrix[0]))]
        columns = [
            [matrix[row_index][column_index] for row_index in range(len(matrix))]
            for column_index in range(len(matrix[0]))
        ]
        return records_from_columns(category_labels, hue_labels, columns)

    values = [coerce_float(value) for value in object_list(data)]
    if not values:
        raise ValueError("data must contain at least one value")
    category_labels = resolve_category_labels(label, len(values))
    return [
        SockBarRecord(
            index=index,
            category_label=category_labels[index],
            value=value,
            hue_label=None,
        )
        for index, value in enumerate(values)
    ]


def mapping_columns(value: object) -> list[tuple[str, list[float]]] | None:
    """Return wide-form columns from a mapping, when possible."""
    if not isinstance(value, Mapping):
        return None
    columns: list[tuple[str, list[float]]] = []
    expected_length: int | None = None
    for key, raw_column in value.items():
        column = [coerce_float(item) for item in object_list(raw_column)]
        if expected_length is None:
            expected_length = len(column)
        elif len(column) != expected_length:
            raise ValueError("all data series must have the same length")
        columns.append((str(key), column))
    if not columns or expected_length == 0:
        raise ValueError("data mapping must contain non-empty series")
    return columns


def object_matrix(value: object) -> list[list[float]] | None:
    """Return a rectangular numeric matrix if value is two-dimensional."""
    if isinstance(value, str | bytes | Mapping):
        return None
    array = np.asarray(value, dtype=object)
    if array.ndim != 2:
        return None
    row_count, column_count = array.shape
    if row_count == 0 or column_count == 0:
        raise ValueError("data matrix must be non-empty")
    matrix: list[list[float]] = []
    for row_index in range(row_count):
        row: list[float] = []
        for column_index in range(column_count):
            row.append(coerce_float(array[row_index, column_index]))
        matrix.append(row)
    return matrix


def resolve_category_labels(label: object | None, expected_length: int) -> list[str]:
    """Resolve optional category labels."""
    if expected_length < 1:
        raise ValueError("expected_length must be positive")
    if label is None:
        return [str(index) for index in range(expected_length)]
    labels = [str(value) for value in object_list(label)]
    if len(labels) != expected_length:
        raise ValueError(
            f"label length {len(labels)} does not match data length {expected_length}",
        )
    return labels


def records_from_columns(
    category_labels: Sequence[str],
    hue_labels: Sequence[str],
    columns: Sequence[Sequence[float]],
) -> list[SockBarRecord]:
    """Build long records from wide-form columns."""
    records: list[SockBarRecord] = []
    index = 0
    for row_index, category in enumerate(category_labels):
        for column_index, hue_label in enumerate(hue_labels):
            records.append(
                SockBarRecord(
                    index=index,
                    category_label=category,
                    value=columns[column_index][row_index],
                    hue_label=hue_label,
                ),
            )
            index += 1
    return records


def object_list(value: object) -> list[object]:
    """Convert scalar, NumPy, pandas-like, and iterable values into a flat list."""
    if isinstance(value, str | bytes):
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
            raise TypeError("data values must be numeric") from exc
    if isinstance(value, int | float | np.number):
        return float(value)
    raise TypeError("data values must be numeric")


def normalize_values(records: Sequence[SockBarRecord]) -> list[float]:
    """Normalize record values into sock coverage ratios."""
    positive_max = max((record.value for record in records if record.value > 0), default=1.0)
    return [
        min(MAX_COVERAGE_RATIO, max(0.0, record.value / positive_max * MAX_COVERAGE_RATIO))
        for record in records
    ]


def unique_in_order(values: Iterable[str]) -> list[str]:
    """Return unique strings while preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

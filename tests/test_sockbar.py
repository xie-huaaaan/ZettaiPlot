"""Tests for the public sockbar API."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import zettaiplot as zp
from zettaiplot.data import resolve_sockbar_records


class FakeFrame:
    """Small DataFrame-like object for duck-typed column access tests."""

    def __init__(self, columns: dict[str, list[object]]) -> None:
        """Initialize with column vectors."""
        self.columns = columns

    def __getitem__(self, key: str) -> list[object]:
        """Return a named column."""
        return self.columns[key]


def test_sockbar_accepts_lists_and_creates_axes() -> None:
    """List inputs draw one artist per value and create axes when omitted."""
    container = zp.sockbar(["a", "b", "c"], [1, 2, 4], seed=1)

    assert len(container.image_artists) == 3
    assert container.normalized_values == [0.25, 0.5, 1.0]
    assert container.ax is not None
    plt.close("all")


def test_sockbar_accepts_numpy_and_existing_axes() -> None:
    """NumPy array inputs draw into an existing axes."""
    _, ax = plt.subplots()
    container = zp.sockbar(
        x=np.array(["a", "b"]),
        height=np.array([2.0, 4.0]),
        ax=ax,
    )

    assert container.ax is ax
    assert len(container.image_artists) == 2
    plt.close("all")


def test_sockbar_accepts_mapping_data() -> None:
    """Mapping data resolves column names for x, height, and hue."""
    data = {
        "day": ["d1", "d1", "d2", "d2"],
        "sales": [1, 2, 3, 4],
        "person": ["A", "B", "A", "B"],
    }

    container = zp.sockbar(x="day", height="sales", hue="person", data=data)

    assert container.legend_labels == ["A", "B"]
    assert len(container.image_artists) == 4
    plt.close("all")


def test_sockbar_accepts_dataframe_like_data() -> None:
    """DataFrame-like objects are supported through __getitem__ access."""
    data = FakeFrame(
        {
            "x": ["a", "a", "b", "b"],
            "height": [1, 3, 2, 4],
            "hue": ["north", "south", "north", "south"],
        },
    )

    records = resolve_sockbar_records("x", "height", "hue", data)
    container = zp.sockbar(x="x", height="height", hue="hue", data=data)

    assert [record.category_label for record in records] == ["a", "a", "b", "b"]
    assert container.legend_labels == ["north", "south"]
    plt.close("all")


def test_grouped_layout_positive_zero_and_negative_gap() -> None:
    """Grouped hue spacing treats negative inner gaps as overlap."""
    positive = zp.sockbar(
        x=["a", "a"],
        height=[1, 2],
        hue=["A", "B"],
        hue_inner_gap=14,
        legend=False,
    )
    zero = zp.sockbar(
        x=["a", "a"],
        height=[1, 2],
        hue=["A", "B"],
        hue_inner_gap=0,
        legend=False,
    )
    negative = zp.sockbar(
        x=["a", "a"],
        height=[1, 2],
        hue=["A", "B"],
        hue_inner_gap=-20,
        legend=False,
    )

    def center_delta(container: zp.SockBarContainer) -> float:
        return abs(container.placements[1].center_x - container.placements[0].center_x)

    assert center_delta(positive) > center_delta(zero)
    assert center_delta(negative) < center_delta(zero)
    plt.close("all")


def test_original_gap_requires_two_hues() -> None:
    """Original pair gaps are only valid for two-hue layouts."""
    zp.sockbar(
        x=["a", "a"],
        height=[1, 2],
        hue=["A", "B"],
        hue_inner_gap="original",
        legend=False,
    )
    plt.close("all")

    with pytest.raises(ValueError, match="exactly 2 hue"):
        zp.sockbar(
            x=["a", "a", "a"],
            height=[1, 2, 3],
            hue=["A", "B", "C"],
            hue_inner_gap="original",
            legend=False,
        )


def test_legend_ncol_positive_negative_and_invalid() -> None:
    """Legend ncol supports row-first and column-first semantics."""
    positive = zp.sockbar(
        x=["a", "a", "b", "b"],
        height=[1, 2, 3, 4],
        hue=["A", "B", "A", "B"],
        legend_kwargs={"ncol": 2},
    )
    negative = zp.sockbar(
        x=["a", "a", "a", "b", "b", "b"],
        height=[1, 2, 3, 4, 5, 6],
        hue=["A", "B", "C", "A", "B", "C"],
        legend_kwargs={"ncol": -2},
    )

    assert positive.legend_ncol == 2
    assert negative.legend_ncol == 2
    assert negative.legend_labels == ["A", "C", "B"]
    plt.close("all")

    with pytest.raises(ValueError, match="ncol=0"):
        zp.sockbar(
            x=["a", "a"],
            height=[1, 2],
            hue=["A", "B"],
            legend_kwargs={"ncol": 0},
        )

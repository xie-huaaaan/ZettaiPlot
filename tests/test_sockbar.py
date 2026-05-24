"""Tests for the public sockbar API."""

from __future__ import annotations

from typing import cast

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import zettaiplot as zp
from zettaiplot.data import resolve_sockbar_records
from zettaiplot.layout import HueInnerGap


def test_sockbar_accepts_list_data_and_creates_axes() -> None:
    """List data draws one artist per value and generates integer labels."""
    container = zp.sockbar([1, 2, 4], seed=1)

    assert len(container.image_artists) == 3
    assert [placement.category_label for placement in container.placements] == ["0", "1", "2"]
    assert container.normalized_values == [0.2, 0.4, 0.8]
    assert container.ax is not None
    plt.close("all")


def test_sockbar_accepts_all_zero_data() -> None:
    """All-zero data is valid and normalizes to zero coverage."""
    container = zp.sockbar([0, 0, 0])

    assert container.normalized_values == [0.0, 0.0, 0.0]
    assert len(container.image_artists) == 3
    plt.close("all")


def test_sockbar_accepts_numpy_data_and_existing_axes() -> None:
    """NumPy array data draws into an existing axes."""
    _, ax = plt.subplots()
    container = zp.sockbar(
        np.array([2.0, 4.0]),
        label=np.array(["a", "b"]),
        ax=ax,
    )

    assert container.ax is ax
    assert len(container.image_artists) == 2
    assert [placement.category_label for placement in container.placements] == ["a", "b"]
    plt.close("all")


def test_sockbar_accepts_mapping_wide_data() -> None:
    """Mapping data uses keys as hue labels and values as category series."""
    container = zp.sockbar(
        {
            "甲": [100, 150, 200],
            "乙": [80, 120, 160],
        },
        label=["第一天", "第二天", "第三天"],
    )

    assert container.legend_labels == ["甲", "乙"]
    assert len(container.image_artists) == 6
    assert [placement.category_label for placement in container.placements] == [
        "第一天",
        "第一天",
        "第二天",
        "第二天",
        "第三天",
        "第三天",
    ]
    plt.close("all")


def test_sockbar_accepts_matrix_wide_data() -> None:
    """Matrix data expands row-major and auto-generates hue labels."""
    container = zp.sockbar(
        [
            [1, 2],
            [3, 4],
            [5, 6],
        ],
        label=["d1", "d2", "d3"],
    )

    assert len(container.image_artists) == 6
    assert container.legend_labels == ["0", "1"]
    assert [placement.category_label for placement in container.placements] == [
        "d1",
        "d1",
        "d2",
        "d2",
        "d3",
        "d3",
    ]
    plt.close("all")


def test_resolve_sockbar_records_is_strict_internal_long_form() -> None:
    """Public wide inputs resolve into one strict internal record list."""
    records = resolve_sockbar_records(
        {"A": [1, 3], "B": [2, 4]},
        label=["x", "y"],
    )

    assert [(record.category_label, record.hue_label, record.value) for record in records] == [
        ("x", "A", 1.0),
        ("x", "B", 2.0),
        ("y", "A", 3.0),
        ("y", "B", 4.0),
    ]


def test_grouped_layout_positive_zero_and_negative_gap() -> None:
    """Grouped hue spacing treats negative inner gaps as overlap."""
    positive = zp.sockbar({"A": [1], "B": [2]}, hue_inner_gap=14, legend=False)
    zero = zp.sockbar({"A": [1], "B": [2]}, hue_inner_gap=0, legend=False)
    negative = zp.sockbar({"A": [1], "B": [2]}, hue_inner_gap=-20, legend=False)

    def center_delta(container: zp.SockBarContainer) -> float:
        return abs(container.placements[1].center_x - container.placements[0].center_x)

    assert center_delta(positive) > center_delta(zero)
    assert center_delta(negative) < center_delta(zero)
    plt.close("all")


def test_auto_gap_uses_original_gap_for_two_hues_and_default_for_more() -> None:
    """Auto hue spacing uses original pair gaps only for two hue levels."""
    two_auto = zp.sockbar({"A": [1], "B": [2]}, hue_inner_gap="auto", legend=False)
    two_default = zp.sockbar({"A": [1], "B": [2]}, hue_inner_gap=14, legend=False)
    three_auto = zp.sockbar({"A": [1], "B": [2], "C": [3]}, hue_inner_gap="auto", legend=False)
    three_default = zp.sockbar({"A": [1], "B": [2], "C": [3]}, hue_inner_gap=14, legend=False)

    def center_delta(container: zp.SockBarContainer, left: int, right: int) -> float:
        return abs(container.placements[right].center_x - container.placements[left].center_x)

    assert center_delta(two_auto, 0, 1) != center_delta(two_default, 0, 1)
    assert center_delta(three_auto, 0, 1) == center_delta(three_default, 0, 1)

    with pytest.raises(ValueError, match='"auto" or an integer'):
        zp.sockbar(
            {"A": [1], "B": [2], "C": [3]},
            hue_inner_gap=cast(HueInnerGap, "original"),
            legend=False,
        )
    plt.close("all")


def test_legend_ncol_positive_negative_and_invalid() -> None:
    """Legend ncol supports row-first and column-first semantics."""
    positive = zp.sockbar(
        {"A": [1, 3], "B": [2, 4]},
        legend_kwargs={"ncol": 2},
    )
    negative = zp.sockbar(
        {"A": [1, 4], "B": [2, 5], "C": [3, 6]},
        legend_kwargs={"ncol": -2},
    )

    assert positive.legend_ncol == 2
    assert negative.legend_ncol == 2
    assert negative.legend_labels == ["A", "C", "B"]
    plt.close("all")

    with pytest.raises(ValueError, match="ncol=0"):
        zp.sockbar({"A": [1], "B": [2]}, legend_kwargs={"ncol": 0})

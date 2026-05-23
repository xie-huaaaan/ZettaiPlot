"""Tests for procedural texture rendering."""

from __future__ import annotations

from PIL import Image

from zettaiplot.assets import load_default_assets, open_leg
from zettaiplot.textures import (
    HorizontalStripesSpec,
    OpaqueSpec,
    PaletteSpec,
    PolkaDotSpec,
    SheerSpec,
    render_sock_texture,
    resolve_color,
    resolve_palette,
)


def test_render_sock_texture_preserves_size_and_alpha() -> None:
    """Texture rendering keeps the tight-cropped image size and alpha channel."""
    library = load_default_assets()
    leg = open_leg(library.assets["leg_10_l"])
    rendered = render_sock_texture(leg, SheerSpec(color="black"), coverage_ratio=0.72)

    assert rendered.size == leg.size
    assert list(rendered.getchannel("A").get_flattened_data()) == list(
        leg.getchannel("A").get_flattened_data(),
    )


def test_custom_rgb_and_palette_specs_render() -> None:
    """Custom RGB colors and two-color palettes are accepted by texture specs."""
    assert resolve_color((300, -10, 128)) == (255, 0, 128)
    assert resolve_palette(PaletteSpec(color_a=(1, 2, 3), color_b="white")) == (
        (1, 2, 3),
        (245, 242, 232),
    )

    leg = Image.new("RGBA", (80, 120), (236, 188, 164, 255))
    striped = render_sock_texture(
        leg,
        HorizontalStripesSpec(
            palette=PaletteSpec(color_a=(30, 40, 90), color_b=(240, 240, 220)),
        ),
        coverage_ratio=1.0,
    )
    dotted = render_sock_texture(
        leg,
        PolkaDotSpec(palette=PaletteSpec(color_a="pink", color_b=(250, 240, 245))),
        coverage_ratio=1.0,
    )
    opaque = render_sock_texture(
        leg,
        OpaqueSpec(color=(12, 24, 48), opacity=0.85),
        coverage_ratio=1.0,
    )

    assert striped.size == leg.size
    assert dotted.size == leg.size
    assert opaque.size == leg.size

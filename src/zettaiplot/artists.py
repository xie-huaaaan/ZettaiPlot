"""Matplotlib artist helpers for drawing textured legs."""

from __future__ import annotations

from PIL import Image
from matplotlib.axes import Axes
from matplotlib.image import AxesImage

from zettaiplot.assets import LegAsset, open_leg
from zettaiplot.textures import OpaqueSpec, SockTextureSpec, render_sock_texture


def draw_sock_leg(
    ax: Axes,
    leg: Image.Image | LegAsset,
    *,
    x: float,
    value: float,
    scale: float = 1.0,
    texture: SockTextureSpec | None = None,
    baseline: float = 0.0,
    zorder: float | None = None,
) -> AxesImage:
    """Draw one tight-cropped leg with a procedural sock texture.

    Args:
        ax: Target Matplotlib axes.
        leg: Pillow image or packaged leg asset.
        x: Category center in chart pixel coordinates.
        value: Sock coverage ratio in the closed interval [0, 1].
        scale: Image scale in chart pixel units.
        texture: Sock texture specification. Defaults to opaque black.
        baseline: Bottom baseline of the leg image.
        zorder: Optional Matplotlib z-order.

    Returns:
        The image artist added to the axes.
    """
    image = open_leg(leg) if isinstance(leg, LegAsset) else leg.convert("RGBA")
    spec = texture if texture is not None else OpaqueSpec()
    rendered = render_sock_texture(image, spec, coverage_ratio=value)
    width, height = rendered.size
    anchor_x = (width - 1) / 2 * scale
    left = x - anchor_x
    right = left + width * scale
    bottom = baseline
    top = baseline + height * scale
    return ax.imshow(
        rendered,
        extent=(left, right, bottom, top),
        origin="upper",
        zorder=zorder,
    )

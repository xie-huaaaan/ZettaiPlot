"""Concrete procedural sock texture renderers."""

from __future__ import annotations

import math
from collections.abc import Callable

from PIL import Image

from zettaiplot._pillow import flattened_pixels
from zettaiplot.textures.blend import (
    alpha_blend,
    clamp_float,
    deterministic_noise,
    lerp,
    luminance,
    multiply_tinted,
    rgba_tuple,
    scale_color,
)
from zettaiplot.textures.colors import resolve_color, resolve_palette
from zettaiplot.textures.geometry import (
    gradient_t,
    near_periodic_line,
    periodic_distance,
    row_u,
)
from zettaiplot.textures.masks import RowProfile, sock_mask_and_profiles
from zettaiplot.textures.specs import (
    FishnetSpec,
    GradientSheerSpec,
    HorizontalStripesSpec,
    LaceTopSpec,
    OpaqueSpec,
    PolkaDotSpec,
    RGB,
    RGBA,
    RibbedSpec,
    SheerSpec,
    SockTextureSpec,
)


type PixelFunc = Callable[[int, int, RGBA], RGBA]


def render_sock_texture(
    leg: Image.Image,
    spec: SockTextureSpec,
    coverage_ratio: float = 0.72,
) -> Image.Image:
    """Render a sock texture over a tight-cropped leg image."""
    image = leg.convert("RGBA")
    mask, profiles, top_y = sock_mask_and_profiles(image, coverage_ratio)
    if spec.kind == "opaque":
        return render_opaque(image, mask, profiles, top_y, spec)
    if spec.kind == "sheer":
        return render_sheer(image, mask, profiles, top_y, spec)
    if spec.kind == "gradient_sheer":
        return render_gradient_sheer(image, mask, profiles, top_y, spec)
    if spec.kind == "horizontal_stripes":
        return render_horizontal_stripes(image, mask, profiles, top_y, spec)
    if spec.kind == "ribbed":
        return render_ribbed(image, mask, profiles, top_y, spec)
    if spec.kind == "fishnet":
        return render_fishnet(image, mask, profiles, top_y, spec)
    if spec.kind == "polka_dot":
        return render_polka_dot(image, mask, profiles, top_y, spec)
    if spec.kind == "lace_top":
        return render_lace_top(image, mask, profiles, top_y, spec)
    raise ValueError(f"Unsupported texture kind: {spec.kind}")


def render_opaque(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: OpaqueSpec,
) -> Image.Image:
    """Render a solid sock while retaining source shading."""
    base = resolve_color(spec.color)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        edge = abs(u) ** 1.8
        alpha = clamp_float(spec.opacity * (1.0 + spec.edge_shadow * edge), 0.0, 1.0)
        shade = luminance(source) / 255
        shaded = scale_color(base, 0.72 + shade * 0.38 - spec.edge_shadow * edge * 0.35)
        return alpha_blend(source, (*shaded, round(alpha * 255)))

    output = apply_pixels(image, mask, profiles, pixel)
    return draw_cuff(output, mask, profiles, top_y, base, spec.cuff_height, 0.86)


def render_sheer(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: SheerSpec,
) -> Image.Image:
    """Render a transparent stocking texture."""
    del top_y
    base = resolve_color(spec.color)
    base_opacity = 0.10 + clamp_float(spec.denier, 5.0, 120.0) / 120.0 * 0.42

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        edge = abs(u) ** 2.2
        grain = deterministic_noise(x, y) * spec.grain_strength
        alpha = clamp_float(
            base_opacity * (1.0 + spec.edge_enrichment * edge) + grain,
            0.0,
            0.82,
        )
        enriched = scale_color(base, 1.0 - spec.edge_enrichment * edge * 0.28)
        return multiply_tinted(source, enriched, alpha)

    return apply_pixels(image, mask, profiles, pixel)


def render_gradient_sheer(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: GradientSheerSpec,
) -> Image.Image:
    """Render sheer stockings with vertical opacity falloff."""
    base = resolve_color(spec.color)
    height = image.height
    span = max(height - top_y - 1, 1)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        t = gradient_t((y - top_y) / span, spec.gradient_curve)
        alpha = lerp(spec.top_opacity, spec.bottom_opacity, t)
        u = row_u(profiles[y], x)
        edge = abs(u) ** 2
        return multiply_tinted(source, scale_color(base, 1.0 - edge * 0.18), alpha)

    return apply_pixels(image, mask, profiles, pixel)


def render_horizontal_stripes(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: HorizontalStripesSpec,
) -> Image.Image:
    """Render warped horizontal striped socks."""
    primary, secondary = resolve_palette(spec.palette)
    period = max(1, spec.stripe_height + spec.gap_height)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        # 圆柱体近似：u=(x-center_x(y))/half_width(y)，边缘处 |u| 趋近 1。
        # 将 u 映射为 theta=asin(clamp(u,-1,1)) 可模拟圆柱表面横向压缩。
        theta = math.asin(clamp_float(u, -1.0, 1.0))
        # 横纹弧垂：在边缘处按 theta^2 增加 y 偏移，让横线形成轻微椭圆下垂。
        droop = spec.warp_strength * (theta * theta) * 9.0
        pattern_y = y + droop - top_y
        stripe_on = int(pattern_y) % period < spec.stripe_height
        color = primary if stripe_on else secondary
        edge = abs(u) ** 1.9
        shaded = scale_color(color, 1.0 - edge * 0.22)
        return multiply_tinted(source, shaded, 0.82)

    return apply_pixels(image, mask, profiles, pixel)


def render_ribbed(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: RibbedSpec,
) -> Image.Image:
    """Render vertical ribbed knit socks."""
    del top_y
    base = resolve_color(spec.color)
    spacing = max(2, spec.rib_spacing)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        # 竖向罗纹也使用 theta=asin(u) 压缩横向纹理坐标，避免边缘像平贴直线。
        theta = math.asin(clamp_float(u, -1.0, 1.0))
        pattern_x = (theta / math.pi + 0.5) * spacing * 8
        wave = (math.cos(pattern_x * math.tau / spacing) + 1.0) / 2.0
        edge = abs(u) ** 1.8
        factor = 0.9 + spec.highlight_strength * wave - spec.rib_depth * (1.0 - wave)
        factor -= edge * 0.20
        return multiply_tinted(source, scale_color(base, factor), 0.78)

    return apply_pixels(image, mask, profiles, pixel)


def render_fishnet(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: FishnetSpec,
) -> Image.Image:
    """Render diamond fishnet stockings."""
    del top_y
    base = resolve_color(spec.color)
    cell = max(8, spec.cell_size)
    line_width = max(1, spec.line_width)
    angle = math.radians(spec.angle)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        # 网格使用 theta=asin(u) 作为横向坐标，边缘横向距离被压缩后网眼会自然变窄。
        theta = math.asin(clamp_float(u, -1.0, 1.0))
        virtual_x = theta / math.pi * cell * 4
        virtual_y = y * 0.62 + abs(theta) * 5.5
        a = virtual_x * cos_a + virtual_y * sin_a
        b = -virtual_x * cos_a + virtual_y * sin_a
        on_line = near_periodic_line(a, cell, line_width) or near_periodic_line(
            b,
            cell,
            line_width,
        )
        if on_line:
            edge = abs(u) ** 1.7
            return multiply_tinted(source, scale_color(base, 1.0 - edge * 0.25), 0.82)
        return multiply_tinted(source, base, 0.10)

    return apply_pixels(image, mask, profiles, pixel)


def render_polka_dot(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: PolkaDotSpec,
) -> Image.Image:
    """Render polka-dot socks."""
    primary, secondary = resolve_palette(spec.palette)
    spacing = max(6, spec.dot_spacing)
    radius = max(1, spec.dot_radius)

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        u = row_u(profiles[y], x)
        theta = math.asin(clamp_float(u, -1.0, 1.0))
        virtual_x = theta / math.pi * spacing * 6
        row = math.floor((y - top_y) / spacing)
        offset = spacing / 2 if spec.staggered and row % 2 else 0
        local_x = periodic_distance(virtual_x + offset, spacing)
        local_y = periodic_distance(y - top_y, spacing)
        color = (
            primary
            if local_x * local_x + local_y * local_y <= radius * radius
            else secondary
        )
        return multiply_tinted(source, color, 0.78)

    return apply_pixels(image, mask, profiles, pixel)


def render_lace_top(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    spec: LaceTopSpec,
) -> Image.Image:
    """Render sheer or opaque socks with decorative lace top."""
    if spec.base_style == "opaque":
        output = render_opaque(
            image,
            mask,
            profiles,
            top_y,
            OpaqueSpec(color="black", opacity=0.78, edge_shadow=0.18, cuff_height=0),
        )
    else:
        output = render_sheer(
            image,
            mask,
            profiles,
            top_y,
            SheerSpec(
                color="black", denier=32, edge_enrichment=0.25, grain_strength=0.02
            ),
        )

    lace_height = max(8, spec.lace_height)
    motif = max(6, spec.motif_scale)
    base = resolve_color("black")

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        if y > top_y + lace_height:
            return source
        u = row_u(profiles[y], x)
        theta = math.asin(clamp_float(u, -1.0, 1.0))
        virtual_x = (theta / math.pi + 0.5) * motif * 10
        local = periodic_distance(virtual_x, motif)
        scallop_y = (math.sin(virtual_x * math.tau / motif) + 1.0) * lace_height * 0.22
        lace_band = y - top_y <= lace_height * 0.28
        motif_line = abs(local - motif * 0.5) <= 1.3
        scallop_line = abs((y - top_y) - (lace_height * 0.55 + scallop_y)) <= 2.0
        if lace_band or motif_line or scallop_line:
            return multiply_tinted(source, base, spec.lace_opacity)
        return source

    return apply_pixels(output, mask, profiles, pixel)


def draw_cuff(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    top_y: int,
    color: RGB,
    cuff_height: int,
    opacity: float,
) -> Image.Image:
    """Draw a simple sock cuff band at the coverage top."""
    if cuff_height <= 0:
        return image

    def pixel(x: int, y: int, source: RGBA) -> RGBA:
        if top_y <= y < top_y + cuff_height:
            u = abs(row_u(profiles[y], x))
            return multiply_tinted(source, scale_color(color, 1.05 - u * 0.18), opacity)
        return source

    return apply_pixels(image, mask, profiles, pixel)


def apply_pixels(
    image: Image.Image,
    mask: list[bool],
    profiles: list[RowProfile | None],
    pixel_func: PixelFunc,
) -> Image.Image:
    """Apply a pixel function over the sock mask."""
    output = image.copy()
    pixels = [rgba_tuple(pixel) for pixel in flattened_pixels(output)]
    width, height = output.size

    for y in range(height):
        if profiles[y] is None:
            continue
        row_offset = y * width
        for x in range(width):
            index = row_offset + x
            if mask[index]:
                source = rgba_tuple(pixels[index])
                pixels[index] = pixel_func(x, y, source)

    output.putdata(pixels)
    return output

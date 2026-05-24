# ZettaiPlot API Reference

ZettaiPlot is a Matplotlib-based visualization library that replaces the
rectangular bars of a bar chart with stylized leg assets. Numeric values are
encoded as sock coverage height: the higher the value, the higher the sock is
drawn on the leg. The leg height remains visually fixed.

This document describes the current v0.1 API.

---

## Installation

```bash
pip install zettaiplot
```

Runtime requirements:

| Package | Version |
| --- | --- |
| Python | `>=3.12` |
| Matplotlib | `>=3.8.0` |
| NumPy | `>=1.26.0` |
| Pillow | `>=11.0.0` |

---

## Quick Start

### Single-Series Chart

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

zp.sockbar(
    [100, 150, 80, 200],
    label=["Mon", "Tue", "Wed", "Thu"],
)

plt.tight_layout()
plt.show()
```

If `label` is omitted, ZettaiPlot generates category labels automatically:

```python
zp.sockbar([100, 150, 80])
# labels become ["0", "1", "2"]
```

### Grouped Chart

Use a mapping when each category contains multiple legend items.

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

data = {
    "Alice": [100, 150, 200],
    "Bob": [80, 120, 160],
}

zp.sockbar(
    data,
    label=["Day 1", "Day 2", "Day 3"],
)

plt.tight_layout()
plt.show()
```

Mapping keys become legend labels. Mapping values are the per-category series
for each legend item.

---

## Design Model

The public input API is intentionally "wide in, strict out":

1. Users pass flexible `data` plus optional `label`.
2. ZettaiPlot immediately normalizes that input into internal `SockBarRecord`
   rows.
3. Layout and rendering only consume the normalized internal records.

The internal record shape is:

```python
SockBarRecord(
    index=int,
    category_label=str,
    value=float,
    hue_label=str | None,
)
```

This keeps the public API compact while giving the renderer one strict data
format.

---

## Top-Level API

### `sockbar()`

```python
zp.sockbar(
    data,
    label=None,
    *,
    texture=None,
    hue_textures=None,
    ax=None,
    legend=True,
    legend_kwargs=None,
    hue_inner_gap="auto",
    group_gap=80,
    odd_single="center",
    seed=None,
) -> SockBarContainer
```

Draw a sock bar chart on Matplotlib axes. This is the primary public entry
point.

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `data` | see [Data Input](#data-input) | required | Numeric values to plot. |
| `label` | sequence-like \| `None` | `None` | Category labels. If omitted, integer labels are generated as strings. |
| `texture` | `SockTextureSpec \| None` | `None` | Shared texture for all legs. In non-hue charts this controls every leg. In hue charts it is used only when `hue_textures` is omitted and you explicitly want one shared texture. |
| `hue_textures` | mapping \| sequence \| `None` | `None` | Per-hue textures. Mapping keys should match hue labels. Sequence items are assigned to hue labels in order. If omitted, built-in default textures are used for hue charts. |
| `ax` | `matplotlib.axes.Axes \| None` | `None` | Target axes. If omitted, a new figure and axes are created. |
| `legend` | `bool` | `True` | Whether to render a texture swatch legend for hue charts. Ignored for single-series charts. |
| `legend_kwargs` | mapping \| `None` | `None` | Extra keyword arguments passed to `Axes.legend()`, with special `ncol` handling. |
| `hue_inner_gap` | `int \| "auto"` | `"auto"` | Pixel gap between adjacent hue legs in one category. Negative values create overlap. |
| `group_gap` | `int` | `80` | Pixel gap between category groups. |
| `odd_single` | `"left" \| "center" \| "right"` | `"center"` | For odd single-series category counts, controls which category is the unpaired single leg. |
| `seed` | `int \| None` | `None` | Random seed used when choosing the side/source asset for unpaired single legs. |

---

## Data Input

### 1-D Data

Use this for a single series: one value per category.

```python
zp.sockbar([100, 150, 200])

zp.sockbar(
    [100, 150, 200],
    label=["Day 1", "Day 2", "Day 3"],
)
```

NumPy arrays work the same way:

```python
import numpy as np

zp.sockbar(
    np.array([100, 150, 200]),
    label=["Day 1", "Day 2", "Day 3"],
)
```

### Mapping Data

Use a mapping for grouped/hue charts.

```python
zp.sockbar(
    {
        "A": [100, 150, 200],
        "B": [80, 120, 160],
    },
    label=["Day 1", "Day 2", "Day 3"],
)
```

Rules:

- Each key is a hue/legend label.
- Each value is that hue's values across categories.
- All series must have the same length.
- `label`, if provided, must have the same length as each series.

The example above expands internally to:

| category | hue | value |
| --- | --- | --- |
| Day 1 | A | 100 |
| Day 1 | B | 80 |
| Day 2 | A | 150 |
| Day 2 | B | 120 |
| Day 3 | A | 200 |
| Day 3 | B | 160 |

### 2-D Matrix Data

Matrices are also supported.

```python
zp.sockbar(
    [
        [100, 80],
        [150, 120],
        [200, 160],
    ],
    label=["Day 1", "Day 2", "Day 3"],
)
```

Matrix semantics:

- Rows are category groups.
- Columns are hue items.
- Hue labels are auto-generated as `"0"`, `"1"`, `"2"`, and so on.

If you need readable legend labels, prefer mapping data.

### Empty, Invalid, And All-Zero Data

- Empty data raises `ValueError`.
- Non-numeric data raises `TypeError`.
- Mapping series with unequal lengths raise `ValueError`.
- `label` length mismatches raise `ValueError`.
- All-zero data is valid. It normalizes to all `0.0` coverage and does not
  raise an error.

---

## Value Normalization

Sock height is normalized from data values.

- The maximum positive value maps to coverage ratio `0.8`.
- Positive values are scaled linearly relative to that maximum.
- Zero and negative values map to `0.0`.
- All-zero input maps all values to `0.0`.

Example:

```python
container = zp.sockbar([1, 2, 4])
container.normalized_values
# [0.2, 0.4, 0.8]
```

The leg image remains 720 pixels high; only sock coverage changes.

---

## Grouped/Hue Layout

Grouped charts are produced whenever normalized records have a `hue_label`.
Mapping input and 2-D matrix input both create hue charts.

### `hue_inner_gap`

Controls spacing within a category group.

| Value | Behavior |
| --- | --- |
| `"auto"` | If there are exactly 2 hue levels, use the original source-pair gap from the asset manifest. Otherwise use `14` pixels. |
| `>= 0` | Visible pixel gap between adjacent hue legs. |
| `< 0` | Pixel overlap between adjacent hue legs. For example, `-20` means 20 pixels of overlap. |

> The old spelling `"original"` is not part of the public API. Passing it raises
> `ValueError`.

### `group_gap`

Controls spacing between category groups. The default is `80` pixels.

### `odd_single`

Only applies to single-series charts with an odd number of categories.

| Value | Behavior |
| --- | --- |
| `"left"` | The first category is the unpaired single leg. |
| `"center"` | The middle category is the unpaired single leg. |
| `"right"` | The last category is the unpaired single leg. |

Default: `"center"`.

---

## Legend

Hue charts can show texture swatch legends.

```python
zp.sockbar(
    {"A": [1, 2], "B": [2, 3]},
    legend=True,
    legend_kwargs={
        "loc": "upper left",
        "bbox_to_anchor": (1.01, 1.0),
        "frameon": True,
        "fontsize": 10,
    },
)
```

Default legend placement is outside the axes on the upper right side:

```python
{"loc": "upper left", "bbox_to_anchor": (1.01, 1.0), "borderaxespad": 0.0}
```

### `ncol` Semantics

`legend_kwargs["ncol"]` has special handling:

| Value | Behavior |
| --- | --- |
| positive `n` | Row-first layout, `n` items per row. (Standard Matplotlib behavior) |
| negative `-n` | Column-first layout, `n` items per column. Handles and labels are reordered before calling Matplotlib. |
| `0` | Invalid; raises `ValueError`. |

> Legend swatches are rendered on a light artificial skin background `#FDEAE4`.

---

## Return Value

### `SockBarContainer`

`sockbar()` returns a frozen dataclass.

| Attribute | Type | Description |
| --- | --- | --- |
| `ax` | `matplotlib.axes.Axes` | Axes the chart was drawn on. |
| `image_artists` | `list[AxesImage]` | Matplotlib image artists for rendered legs. |
| `asset_ids` | `list[str]` | Asset IDs used for each leg. |
| `values` | `list[float]` | Original numeric values after parsing. |
| `normalized_values` | `list[float]` | Coverage ratios in `[0.0, 0.8]`. |
| `legend_handles` | `list[TextureLegendHandle]` | Proxy artists used by the legend. |
| `legend_labels` | `list[str]` | Legend label strings after any `ncol < 0` reordering. |
| `placements` | `list[LegPlacement]` | Per-leg layout records. |
| `legend_ncol` | `int \| None` | Actual number of columns passed to Matplotlib, or `None` when no legend is drawn. |

---

## Texture Specifications

All texture specs are frozen dataclasses importable from `zettaiplot`.

```python
import zettaiplot as zp

spec = zp.OpaqueSpec(color="black", opacity=0.9)
```

Pass a spec to:

- `sockbar(texture=...)`
- `sockbar(hue_textures=...)`
- `render_sock_texture(..., spec=...)`
- `draw_sock_leg(..., texture=...)`

### Color Types

```python
RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

ColorPreset = Literal["black", "white", "pink", "navy", "brown"]
ColorLike = ColorPreset | RGB
```

Built-in color values:

| Preset | RGB |
| --- | --- |
| `"black"` | `(23, 22, 28)` |
| `"white"` | `(245, 242, 232)` |
| `"pink"` | `(245, 138, 177)` |
| `"navy"` | `(38, 52, 92)` |
| `"brown"` | `(91, 54, 38)` |

Custom RGB values are allowed:

```python
zp.OpaqueSpec(color=(40, 60, 120))
```

Channels are clipped to `[0, 255]` by `resolve_color()`.

### Palette

`PaletteSpec` is used by stripe and polka-dot textures.

```python
zp.PaletteSpec(preset="school")

zp.PaletteSpec(
    color_a=(30, 40, 90),
    color_b=(240, 240, 220),
)
```

Provide either `preset` or both `color_a` and `color_b`.

Built-in palette presets:

| Preset | Colors |
| --- | --- |
| `"mono_black"` | `(30, 29, 35)` + `(64, 62, 70)` |
| `"school"` | `(34, 40, 74)` + `(238, 238, 224)` |
| `"candy"` | `(247, 143, 184)` + `(255, 238, 246)` |
| `"classic"` | `(28, 27, 31)` + `(245, 242, 232)` |

---

## Texture Spec Classes

### `OpaqueSpec`

Solid over-knee sock.

```python
zp.OpaqueSpec(
    color="black",
    opacity=0.9,
    edge_shadow=0.25,
    cuff_height=18,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | Main sock color. |
| `opacity` | `float` | `0.9` | Overlay opacity. |
| `edge_shadow` | `float` | `0.25` | Extra edge darkening for cylindrical volume. |
| `cuff_height` | `int` | `18` | Pixel height of the top cuff band. |

### `SheerSpec`

Transparent stocking.

```python
zp.SheerSpec(
    color="black",
    denier=40.0,
    edge_enrichment=0.35,
    grain_strength=0.08,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | Stocking tint. |
| `denier` | `float` | `40.0` | Higher values are more opaque. |
| `edge_enrichment` | `float` | `0.35` | Opacity/darkening boost near leg edges. |
| `grain_strength` | `float` | `0.08` | Subtle deterministic fabric noise. |

### `GradientSheerSpec`

Sheer stocking with vertical opacity falloff.

```python
zp.GradientSheerSpec(
    color="black",
    top_opacity=0.65,
    bottom_opacity=0.25,
    gradient_curve="linear",
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | Stocking tint. |
| `top_opacity` | `float` | `0.65` | Opacity near the top cuff. |
| `bottom_opacity` | `float` | `0.25` | Opacity near the ankle. |
| `gradient_curve` | `"linear" \| "ease_in" \| "ease_out"` | `"linear"` | Vertical interpolation curve. |

### `HorizontalStripesSpec`

Two-color horizontal striped sock.

```python
zp.HorizontalStripesSpec(
    palette=zp.PaletteSpec(preset="school"),
    stripe_height=18,
    gap_height=14,
    warp_strength=0.45,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `palette` | `PaletteSpec` | `PaletteSpec(preset="school")` | `color_a` is used for stripe bands; `color_b` for gaps. |
| `stripe_height` | `int` | `18` | Stripe band height in pixels. |
| `gap_height` | `int` | `14` | Gap band height in pixels. |
| `warp_strength` | `float` | `0.45` | Amount of edge droop/cylindrical bending. |

### `RibbedSpec`

Vertical ribbed knit.

```python
zp.RibbedSpec(
    color="white",
    rib_spacing=10,
    rib_depth=0.28,
    highlight_strength=0.22,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"white"` | Fabric tint. |
| `rib_spacing` | `int` | `10` | Distance between rib centers. |
| `rib_depth` | `float` | `0.28` | Darkness of rib valleys. |
| `highlight_strength` | `float` | `0.22` | Brightness of rib peaks. |

### `FishnetSpec`

Diamond mesh stocking.

```python
zp.FishnetSpec(
    color="black",
    cell_size=30,
    line_width=2,
    angle=45.0,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | Mesh color. |
| `cell_size` | `int` | `30` | Diamond cell size in pixels. |
| `line_width` | `int` | `2` | Mesh thread width in pixels. |
| `angle` | `float` | `45.0` | Mesh rotation angle in degrees. |

### `PolkaDotSpec`

Two-color polka-dot sock.

```python
zp.PolkaDotSpec(
    palette=zp.PaletteSpec(preset="candy"),
    dot_radius=5,
    dot_spacing=24,
    staggered=True,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `palette` | `PaletteSpec` | `PaletteSpec(preset="candy")` | `color_a` is used for dots; `color_b` for the base. |
| `dot_radius` | `int` | `5` | Dot radius in pixels. |
| `dot_spacing` | `int` | `24` | Distance between dot centers. |
| `staggered` | `bool` | `True` | Offset alternate dot rows. |

### `LaceTopSpec`

Decorative lace-top sock.

```python
zp.LaceTopSpec(
    base_style="sheer",
    lace_height=46,
    motif_scale=14,
    lace_opacity=0.72,
)
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `base_style` | `"opaque" \| "sheer"` | `"sheer"` | Base sock rendering style. |
| `lace_height` | `int` | `46` | Lace band height in pixels. |
| `motif_scale` | `int` | `14` | Repeated motif size in pixels. |
| `lace_opacity` | `float` | `0.72` | Lace overlay opacity. |

---

## Low-Level Texture Rendering

### `render_sock_texture()`

```python
zp.render_sock_texture(
    leg,
    spec,
    coverage_ratio=0.72,
)
```

Render a procedural sock texture onto a Pillow RGBA leg image.

| Parameter | Description |
| --- | --- |
| `leg` | RGBA Pillow image. |
| `spec` | Any `SockTextureSpec`. |
| `coverage_ratio` | Sock coverage ratio. `0.0` means no sock; `1.0` means fully covered. |

Returns a new RGBA image. Transparent source pixels remain transparent.

---

## Low-Level Matplotlib Drawing

### `draw_sock_leg()`

```python
zp.draw_sock_leg(
    ax,
    leg,
    *,
    x,
    value,
    scale=1.0,
    texture=None,
    baseline=0.0,
    zorder=None,
)
```

Draw one textured leg onto Matplotlib axes.

| Parameter | Description |
| --- | --- |
| `ax` | Target Matplotlib axes. |
| `leg` | Pillow image or `LegAsset`. |
| `x` | Horizontal center position in pixel-like chart coordinates. |
| `value` | Sock coverage ratio. |
| `scale` | Uniform image scale. |
| `texture` | Texture spec. If omitted, `OpaqueSpec()` is used. |
| `baseline` | Y-coordinate of the image bottom. |
| `zorder` | Matplotlib z-order. |

Returns the `AxesImage` artist.

---

## Asset API

### `load_default_assets()`

```python
library = zp.load_default_assets()
```

Load the bundled leg asset library from package resources.

The current packaged library contains 13 source pairs / 26 single-leg PNGs. All
leg images are 720 pixels high.

### `open_leg()`

```python
image = zp.open_leg(library.assets["leg_10_l"])
```

Open a packaged leg asset as an RGBA Pillow image.

### `LegAssetLibrary`

| Attribute | Type | Description |
| --- | --- | --- |
| `assets` | `dict[str, LegAsset]` | All leg assets keyed by asset id. |
| `pairs` | `dict[int, SourcePair]` | Original source-pair metadata keyed by pair id. |

Method:

```python
library.assets_by_side("l")
library.assets_by_side("r")
```

### `LegAsset`

| Attribute | Type | Description |
| --- | --- | --- |
| `asset_id` | `str` | Example: `"leg_10_l"`. |
| `side` | `str` | `"l"` or `"r"`. |
| `relative_path` | `str` | Path under packaged split assets. |
| `resource` | `Traversable` | `importlib.resources` handle. |
| `source_pair_id` | `int` | Pair id in the source manifest. |
| `width` | `int` | Image width in pixels. |
| `height` | `int` | Image height in pixels, currently always 720. |

### `SourcePair`

| Attribute | Type | Description |
| --- | --- | --- |
| `pair_id` | `int` | Pair identifier. |
| `left_asset_id` | `str` | Left leg asset id. |
| `right_asset_id` | `str` | Right leg asset id. |
| `original_pair_gap` | `int` | Pixel gap between the original left/right components. |

---

## Texture Presets

Convenience constructors live in `zettaiplot.textures.presets`.

```python
from zettaiplot.textures.presets import (
    sheer_black,
    opaque_white,
    school_stripes,
    classic_fishnet,
    lace_sheer_black,
)
```

| Function | Returns |
| --- | --- |
| `sheer_black()` | `SheerSpec(color="black", denier=36, ...)` |
| `opaque_white()` | `OpaqueSpec(color="white", opacity=0.84, ...)` |
| `school_stripes()` | `HorizontalStripesSpec(palette=PaletteSpec(preset="school"), ...)` |
| `classic_fishnet()` | `FishnetSpec(color="black", cell_size=30, ...)` |
| `lace_sheer_black()` | `LaceTopSpec(base_style="sheer", ...)` |

---

## Utility Functions

### `resolve_color()`

```python
from zettaiplot.textures.colors import resolve_color

resolve_color("navy")
# (38, 52, 92)
```

### `resolve_palette()`

```python
from zettaiplot.textures.colors import resolve_palette

resolve_palette(zp.PaletteSpec(preset="school"))
# ((34, 40, 74), (238, 238, 224))
```

### `make_texture_swatch()`

```python
from zettaiplot.legend import make_texture_swatch

swatch = make_texture_swatch(zp.SheerSpec(color="pink"))
```

Render a small rectangular legend sample on `#FDEAE4`.

---

## Complete Examples

### Custom Single-Series Texture

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

container = zp.sockbar(
    [42, 78, 55, 91, 33],
    label=["Mon", "Tue", "Wed", "Thu", "Fri"],
    texture=zp.SheerSpec(color="black", denier=30),
)

plt.tight_layout()
plt.show()
```

### Per-Hue Textures

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

data = {
    "Class A": [80, 120, 95],
    "Class B": [60, 140, 110],
}

container = zp.sockbar(
    data,
    label=["Week 1", "Week 2", "Week 3"],
    hue_textures={
        "Class A": zp.OpaqueSpec(color="black"),
        "Class B": zp.HorizontalStripesSpec(
            palette=zp.PaletteSpec(preset="school"),
        ),
    },
    legend_kwargs={"ncol": 2},
)

plt.tight_layout()
plt.show()
```

### Controlled Overlap

```python
zp.sockbar(
    {
        "A": [10, 12, 14],
        "B": [8, 16, 11],
        "C": [13, 9, 18],
    },
    label=["Day 1", "Day 2", "Day 3"],
    hue_inner_gap=-20,
)
```

### Manual Texture Rendering

```python
import zettaiplot as zp

library = zp.load_default_assets()
asset = library.assets["leg_10_l"]
leg = zp.open_leg(asset)

textured = zp.render_sock_texture(
    leg,
    zp.FishnetSpec(color="black", cell_size=28, line_width=2),
    coverage_ratio=0.65,
)

textured.save("preview.png")
```

### Manual Matplotlib Drawing

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

fig, ax = plt.subplots(figsize=(3, 5))
library = zp.load_default_assets()
asset = library.assets["leg_10_r"]

zp.draw_sock_leg(
    ax,
    asset,
    x=150,
    value=0.7,
    texture=zp.RibbedSpec(color="white", rib_spacing=10),
)

ax.set_xlim(0, 300)
ax.set_ylim(0, 740)
ax.set_aspect("equal")
plt.show()
```

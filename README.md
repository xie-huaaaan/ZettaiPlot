# ZettaiPlot

**[English] \[[简体中文](README.zh-CN.md)]**

Also named "StockingPlot", A Python data visualization library that encodes numeric values as sock coverage height on stylized anime-aesthetic leg assets — a bar chart where "how high the sock is pulled up" carries the data.

> **Absolute Territory** (絶対領域, *zettai ryōiki*): the strip of bare skin between an over-knee sock and a skirt — the visual space this chart type makes data-driven.

![texture sweep preview](assets/split/grouped_previews/two_hue_original_pair_gap.png)

## Features

- **8 procedural texture types** — opaque, sheer, gradient sheer, horizontal stripes, ribbed knit, fishnet, polka-dot, lace top
- **Grouped / hue layouts** — multiple series per category with configurable gap or overlap
- **Matplotlib-native** — drop into any existing Matplotlib figure; returns artists and layout metadata
- **Flexible data input** — accepts plain lists, NumPy arrays, 2-D matrices, or label→series mappings
- **Texture legend** — automatic swatch legend with procedurally-rendered previews
- **Cylindrical warping** — textures curve and compress toward leg edges for realistic volume

## Installation

```bash
pip install zettaiplot
```

**Requirements:** Python ≥ 3.12 · matplotlib ≥ 3.8 · numpy ≥ 1.26 · Pillow ≥ 11.0

## Quick Start

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

# Single series
zp.sockbar(
    [42, 78, 55, 91, 33],
    label=["Mon", "Tue", "Wed", "Thu", "Fri"],
    texture=zp.SheerSpec(color="black", denier=30),
)
plt.tight_layout()
plt.show()
```

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

# Grouped / hue chart
zp.sockbar(
    {"Class A": [80, 120, 95], "Class B": [60, 140, 110]},
    label=["Week 1", "Week 2", "Week 3"],
    hue_textures={
        "Class A": zp.OpaqueSpec(color="black"),
        "Class B": zp.HorizontalStripesSpec(palette=zp.PaletteSpec(preset="school")),
    },
)
plt.tight_layout()
plt.show()
```

## Texture Types

| Spec class | Appearance |
|---|---|
| `OpaqueSpec` | Solid over-knee sock with cuff band |
| `SheerSpec` | Semi-transparent stocking (denier-controlled) |
| `GradientSheerSpec` | Sheer with vertical opacity falloff |
| `HorizontalStripesSpec` | Two-color horizontal stripes with cylindrical warp |
| `RibbedSpec` | Vertical ribbed knit with highlight/shadow |
| `FishnetSpec` | Diamond mesh stocking |
| `PolkaDotSpec` | Two-color polka dots (staggered or aligned) |
| `LaceTopSpec` | Sheer or opaque base with decorative lace cuff |

All textures accept a `ColorLike` color — either a preset string (`"black"`, `"white"`, `"pink"`, `"navy"`, `"brown"`) or a raw `(r, g, b)` tuple.

## API Overview

```python
import zettaiplot as zp

# Main chart function
container = zp.sockbar(data, label=None, *, texture=None, hue_textures=None,
                       ax=None, legend=True, legend_kwargs=None,
                       hue_inner_gap="auto", group_gap=80,
                       odd_single="center", seed=None)

# Low-level: render texture onto a leg image
textured_img = zp.render_sock_texture(leg_image, spec, coverage_ratio=0.72)

# Low-level: draw one leg onto axes
artist = zp.draw_sock_leg(ax, leg, x=200, value=0.65, texture=spec)

# Asset library
library = zp.load_default_assets()   # 13 pairs / 26 legs
leg_img = zp.open_leg(library.assets["pair_01_l"])
```

Full API reference: [docs/api.md](docs/api.md)

## `sockbar()` Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `data` | — | List, array, 2-D matrix, or `{hue: series}` mapping |
| `label` | auto int | Category axis labels |
| `texture` | `OpaqueSpec()` | Shared texture for non-hue charts |
| `hue_textures` | auto | Per-hue texture mapping or sequence |
| `ax` | new figure | Existing Matplotlib axes |
| `legend` | `True` | Add texture swatch legend (hue charts) |
| `legend_kwargs` | `{}` | Forwarded to `ax.legend()` |
| `hue_inner_gap` | `"auto"` | px gap between hue legs; negative = overlap |
| `group_gap` | `80` | px gap between category groups |
| `odd_single` | `"center"` | Unpaired leg position for odd category counts |
| `seed` | `None` | RNG seed for leg asset selection |

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Type check
uv run pyright

# Lint / format
uv run ruff check src tests
uv run ruff format src tests
```

## Project Structure

```
src/zettaiplot/
├── __init__.py        # Public exports
├── bar.py             # sockbar() top-level API
├── data.py            # Input normalization
├── layout.py          # Leg placement computation
├── artists.py         # draw_sock_leg()
├── assets.py          # Packaged leg PNG library
├── legend.py          # Texture swatch legend
└── textures/          # Procedural texture engine
    ├── specs.py       # Texture spec dataclasses
    ├── renderers.py   # Per-type rendering functions
    ├── colors.py      # Color & palette resolution
    ├── geometry.py    # Cylindrical geometry helpers
    ├── masks.py       # Alpha mask generation
    ├── blend.py       # Pixel blending operations
    └── presets.py     # Convenience constructors
```

## Contributing

Contributions are welcome. Please open an issue before submitting a large change so we can discuss the approach.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make changes with tests and type annotations
4. Ensure `pytest`, `pyright`, and `ruff check` all pass
5. Open a pull request

Code style: [Ruff](https://docs.astral.sh/ruff/) for formatting and linting, strict type annotations (Python 3.12+, PEP 695 generics), Google-style docstrings.

## License

MIT License — see [LICENSE](LICENSE) for details.

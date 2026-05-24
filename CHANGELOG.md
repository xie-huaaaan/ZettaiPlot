# Changelog

All notable changes to ZettaiPlot are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
ZettaiPlot uses [Semantic Versioning](https://semver.org/).

---

## [0.1.1] — 2025-01-XX

### Added
- README and API reference documentation (`docs/api.md`).

---

## [0.1.0] — 2025-01-XX

Initial release.

### Added
- `sockbar()` top-level API: single-series and grouped/hue bar charts rendered as sock-covered leg assets.
- 8 procedural texture types: `OpaqueSpec`, `SheerSpec`, `GradientSheerSpec`, `HorizontalStripesSpec`, `RibbedSpec`, `FishnetSpec`, `PolkaDotSpec`, `LaceTopSpec`.
- Flexible data input: Python sequences, NumPy arrays, 2-D matrices, and label→series mappings.
- Cylindrical geometry warping for edge compression and stripe arc droop.
- Grouped/hue layout engine with configurable `hue_inner_gap` (gap or overlap), `group_gap`, and `odd_single` positioning.
- Automatic texture swatch legend with procedurally-rendered previews.
- Packaged leg asset library: 13 matched pairs / 26 individual legs at 720 px height.
- `render_sock_texture()` and `draw_sock_leg()` low-level interfaces.
- `LegAssetLibrary`, `LegAsset`, `SourcePair` asset management API.
- Color presets (`black`, `white`, `pink`, `navy`, `brown`) and palette presets (`mono_black`, `school`, `candy`, `classic`).
- Convenience texture preset constructors in `zettaiplot.textures.presets`.
- `SockBarContainer` return type with axes, artists, placements, normalized values, and legend metadata.
- Full static type annotations (Python 3.12, PEP 695 generics, Pyright-verified).
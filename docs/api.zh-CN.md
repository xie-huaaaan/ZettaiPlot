# ZettaiPlot API 参考文档

ZettaiPlot 是一个基于 Matplotlib 的数据可视化库。它把普通条形图中的矩形柱子替换成风格化腿部素材，并用“袜子穿到多高”来表达数值大小。数值越大，袜子覆盖越高；腿本身的总高度保持不变。

本文档描述当前 v0.1 API。

---

## 安装

```bash
pip install zettaiplot
```

运行时要求：

| 依赖 | 版本 |
| --- | --- |
| Python | `>=3.12` |
| Matplotlib | `>=3.10.9` |
| NumPy | `>=2.4.6` |
| Pillow | `>=12.2.0` |

---

## 快速开始

### 单系列图

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

如果不传 `label`，ZettaiPlot 会自动生成类别标签：

```python
zp.sockbar([100, 150, 80])
# label 自动变成 ["0", "1", "2"]
```

### 分组 / 多图例图

当每个类别中有多个图例项时，推荐使用 mapping 输入：

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

data = {
    "甲": [100, 150, 200],
    "乙": [80, 120, 160],
}

zp.sockbar(
    data,
    label=["第一天", "第二天", "第三天"],
)

plt.tight_layout()
plt.show()
```

mapping 的 key 会成为图例标签；mapping 的 value 是该图例项在各类别下的数值。

---

## 设计模型

当前公开输入 API 采用“宽进严出”的模式：

1. 用户只传灵活的 `data` 和可选的 `label`。
2. ZettaiPlot 立即把输入解析成内部 `SockBarRecord` 行记录。
3. 后续布局和绘制层只消费这一种严格的内部格式。

内部记录结构为：

```python
SockBarRecord(
    index=int,
    category_label=str,
    value=float,
    hue_label=str | None,
)
```

这样外部 API 能保持简洁，而绘图内部仍然有稳定统一的数据结构。

---

## 顶层 API

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

在 Matplotlib 坐标轴上绘制丝袜条形图。这是最主要的公开入口。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `data` | 见下文 | 必填 | 要绘制的数值数据。 |
| `label` | 序列或 `None` | `None` | 类别标签。不传时会生成字符串形式的整数标签。 |
| `texture` | `SockTextureSpec \| None` | `None` | 所有腿共用的纹理。单系列图中会作用于全部腿；多图例图中，如果未提供 `hue_textures` 且想强制共用一种纹理，也可使用它。 |
| `hue_textures` | mapping / sequence / `None` | `None` | 每个 hue / 图例项对应的纹理。mapping 的 key 应与 hue 标签一致；sequence 会按 hue 顺序分配。 |
| `ax` | `matplotlib.axes.Axes \| None` | `None` | 目标坐标轴。不传时自动创建 figure 和 axes。 |
| `legend` | `bool` | `True` | 是否为多图例图绘制纹理图例。单系列图中不会显示图例。 |
| `legend_kwargs` | mapping / `None` | `None` | 传给 `Axes.legend()` 的额外参数，其中 `ncol` 有特殊处理。 |
| `hue_inner_gap` | `int \| "auto"` | `"auto"` | 同一类别组内相邻 hue 腿之间的像素间距。负数表示重叠。 |
| `group_gap` | `int` | `80` | 类别组之间的像素间距。 |
| `odd_single` | `"left" \| "center" \| "right"` | `"center"` | 单系列且类别数为奇数时，哪一个类别作为未配对单腿。 |
| `seed` | `int \| None` | `None` | 为未配对单腿选择素材时使用的随机种子。 |

---

## 数据输入

### 一维数据

用于单系列图：每个数值对应一个类别。

```python
zp.sockbar([100, 150, 200])

zp.sockbar(
    [100, 150, 200],
    label=["第一天", "第二天", "第三天"],
)
```

NumPy 数组也可以：

```python
import numpy as np

zp.sockbar(
    np.array([100, 150, 200]),
    label=["第一天", "第二天", "第三天"],
)
```

### Mapping 数据

用于 grouped / hue 图。

```python
zp.sockbar(
    {
        "甲": [100, 150, 200],
        "乙": [80, 120, 160],
    },
    label=["第一天", "第二天", "第三天"],
)
```

规则：

- 每个 key 是一个 hue / 图例标签。
- 每个 value 是该图例项在各类别下的数值。
- 所有序列长度必须一致。
- 如果传入 `label`，它的长度必须等于每个序列的长度。

上面的例子会在内部展开为：

| 类别 | hue | 数值 |
| --- | --- | --- |
| 第一天 | 甲 | 100 |
| 第一天 | 乙 | 80 |
| 第二天 | 甲 | 150 |
| 第二天 | 乙 | 120 |
| 第三天 | 甲 | 200 |
| 第三天 | 乙 | 160 |

### 二维矩阵数据

也支持二维矩阵：

```python
zp.sockbar(
    [
        [100, 80],
        [150, 120],
        [200, 160],
    ],
    label=["第一天", "第二天", "第三天"],
)
```

矩阵语义：

- 每一行是一个类别组。
- 每一列是一个 hue / 图例项。
- hue 标签会自动生成 `"0"`、`"1"`、`"2"` 等。

如果需要可读的图例名，推荐使用 mapping 输入。

### 空数据、非法数据、全 0 数据

- 空数据会抛出 `ValueError`。
- 非数值数据会抛出 `TypeError`。
- mapping 中各序列长度不一致会抛出 `ValueError`。
- `label` 长度不匹配会抛出 `ValueError`。
- 全部数值为 0 是合法输入，不会报错；所有袜高会归一化为 `0.0`。

---

## 数值归一化

袜子高度由数值归一化而来。

- 最大正数值会映射为覆盖率 `0.8`。
- 其他正数按比例线性缩放。
- 0 和负数映射为 `0.0`。
- 全 0 输入全部映射为 `0.0`。

示例：

```python
container = zp.sockbar([1, 2, 4])
container.normalized_values
# [0.2, 0.4, 0.8]
```

腿部图片高度仍然保持 720px；变化的是袜子的覆盖比例。

---

## Grouped / Hue 布局

当内部记录有 `hue_label` 时，会绘制 grouped 图。mapping 输入和二维矩阵输入都会产生 hue 图。

### `hue_inner_gap`

控制同一类别组内部的间距。

| 值 | 行为 |
| --- | --- |
| `"auto"` | hue 数量正好为 2 时，使用素材 manifest 中的原始双腿间距；其他 hue 数量使用 14 像素。 |
| `>= 0` | 相邻 hue 腿之间的可见像素间距。 |
| `< 0` | 相邻 hue 腿之间的重叠像素数。例如 `-20` 表示重叠 20 像素。 |

> 旧写法 `"original"` 不属于公开 API；传入会抛出 `ValueError`。

### `group_gap`

控制类别组之间的间距，默认值为 `80` 像素。

### `odd_single`

只对单系列且类别数量为奇数的图生效。

| 值 | 行为 |
| --- | --- |
| `"left"` | 第一个类别作为未配对单腿。 |
| `"center"` | 中间类别作为未配对单腿。 |
| `"right"` | 最后一个类别作为未配对单腿。 |

默认值为 `"center"`。

---

## 图例

多图例图可以显示纹理 swatch 图例。

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

默认图例位置在坐标轴右侧外部：

```python
{"loc": "upper left", "bbox_to_anchor": (1.01, 1.0), "borderaxespad": 0.0}
```

### `ncol` 语义

`legend_kwargs["ncol"]` 有特殊规则：

| 值 | 行为 |
| --- | --- |
| 正数 `n` | 行优先排列，每行 `n` 个。（标准 Matplotlib 行为） |
| 负数 `-n` | 列优先排列，每列 `n` 个；内部会先重排 handles 和 labels，再传给 Matplotlib。 |
| `0` | 非法，会抛出 `ValueError`。 |

> 图例 swatch 使用浅肤色背景 `#FDEAE4` 渲染。

---

## 返回值

### `SockBarContainer`

`sockbar()` 返回一个 frozen dataclass。

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `ax` | `matplotlib.axes.Axes` | 图表绘制所在的坐标轴。 |
| `image_artists` | `list[AxesImage]` | 每条腿对应的 Matplotlib image artist。 |
| `asset_ids` | `list[str]` | 每条腿使用的素材 id。 |
| `values` | `list[float]` | 解析后的原始数值。 |
| `normalized_values` | `list[float]` | 袜高覆盖率，范围为 `[0.0, 0.8]`。 |
| `legend_handles` | `list[TextureLegendHandle]` | 图例使用的代理 artist。 |
| `legend_labels` | `list[str]` | 图例标签；若 `ncol < 0`，这里是重排后的顺序。 |
| `placements` | `list[LegPlacement]` | 每条腿的完整布局信息。 |
| `legend_ncol` | `int \| None` | 实际传给 Matplotlib 的 legend 列数；没有图例时为 `None`。 |

---

## 袜子纹理规格

所有纹理规格都是 frozen dataclass，并且可从 `zettaiplot` 顶层导入。

```python
import zettaiplot as zp

spec = zp.OpaqueSpec(color="black", opacity=0.9)
```

可以传给：

- `sockbar(texture=...)`
- `sockbar(hue_textures=...)`
- `render_sock_texture(..., spec=...)`
- `draw_sock_leg(..., texture=...)`

### 颜色类型

```python
RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

ColorPreset = Literal["black", "white", "pink", "navy", "brown"]
ColorLike = ColorPreset | RGB
```

内置颜色：

| 预设 | RGB |
| --- | --- |
| `"black"` | `(23, 22, 28)` |
| `"white"` | `(245, 242, 232)` |
| `"pink"` | `(245, 138, 177)` |
| `"navy"` | `(38, 52, 92)` |
| `"brown"` | `(91, 54, 38)` |

也支持自定义 RGB：

```python
zp.OpaqueSpec(color=(40, 60, 120))
```

`resolve_color()` 会把通道值裁剪到 `[0, 255]`。

### 调色板

`PaletteSpec` 用于条纹和波点纹理。

```python
zp.PaletteSpec(preset="school")

zp.PaletteSpec(
    color_a=(30, 40, 90),
    color_b=(240, 240, 220),
)
```

要么提供 `preset`，要么同时提供 `color_a` 和 `color_b`。

内置调色板：

| 预设 | 颜色 |
| --- | --- |
| `"mono_black"` | `(30, 29, 35)` + `(64, 62, 70)` |
| `"school"` | `(34, 40, 74)` + `(238, 238, 224)` |
| `"candy"` | `(247, 143, 184)` + `(255, 238, 246)` |
| `"classic"` | `(28, 27, 31)` + `(245, 242, 232)` |

---

## 纹理规格类

### `OpaqueSpec`

不透明过膝袜。

```python
zp.OpaqueSpec(
    color="black",
    opacity=0.9,
    edge_shadow=0.25,
    cuff_height=18,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | 袜子主色。 |
| `opacity` | `float` | `0.9` | 覆盖透明度。 |
| `edge_shadow` | `float` | `0.25` | 圆柱体边缘暗化强度。 |
| `cuff_height` | `int` | `18` | 顶部袜口像素高度。 |

### `SheerSpec`

半透明丝袜。

```python
zp.SheerSpec(
    color="black",
    denier=40.0,
    edge_enrichment=0.35,
    grain_strength=0.08,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | 丝袜颜色。 |
| `denier` | `float` | `40.0` | 数值越高越不透明。 |
| `edge_enrichment` | `float` | `0.35` | 腿部边缘处的透明度/暗度增强。 |
| `grain_strength` | `float` | `0.08` | 轻微织物颗粒噪声。 |

### `GradientSheerSpec`

带纵向透明度渐变的丝袜。

```python
zp.GradientSheerSpec(
    color="black",
    top_opacity=0.65,
    bottom_opacity=0.25,
    gradient_curve="linear",
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | 丝袜颜色。 |
| `top_opacity` | `float` | `0.65` | 袜口附近透明度。 |
| `bottom_opacity` | `float` | `0.25` | 脚踝附近透明度。 |
| `gradient_curve` | `"linear" \| "ease_in" \| "ease_out"` | `"linear"` | 纵向插值曲线。 |

### `HorizontalStripesSpec`

双色横条纹袜。

```python
zp.HorizontalStripesSpec(
    palette=zp.PaletteSpec(preset="school"),
    stripe_height=18,
    gap_height=14,
    warp_strength=0.45,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `palette` | `PaletteSpec` | `PaletteSpec(preset="school")` | `color_a` 用于条纹，`color_b` 用于间隔。 |
| `stripe_height` | `int` | `18` | 条纹带像素高度。 |
| `gap_height` | `int` | `14` | 间隔带像素高度。 |
| `warp_strength` | `float` | `0.45` | 边缘弧垂/圆柱弯曲强度。 |

### `RibbedSpec`

竖向罗纹针织袜。

```python
zp.RibbedSpec(
    color="white",
    rib_spacing=10,
    rib_depth=0.28,
    highlight_strength=0.22,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"white"` | 织物颜色。 |
| `rib_spacing` | `int` | `10` | 罗纹中心间距。 |
| `rib_depth` | `float` | `0.28` | 罗纹凹槽暗度。 |
| `highlight_strength` | `float` | `0.22` | 罗纹凸起亮度。 |

### `FishnetSpec`

菱形网袜。

```python
zp.FishnetSpec(
    color="black",
    cell_size=30,
    line_width=2,
    angle=45.0,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `color` | `ColorLike` | `"black"` | 网格颜色。 |
| `cell_size` | `int` | `30` | 菱形网格像素尺寸。 |
| `line_width` | `int` | `2` | 网线像素宽度。 |
| `angle` | `float` | `45.0` | 网格旋转角度，单位为度。 |

### `PolkaDotSpec`

双色波点袜。

```python
zp.PolkaDotSpec(
    palette=zp.PaletteSpec(preset="candy"),
    dot_radius=5,
    dot_spacing=24,
    staggered=True,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `palette` | `PaletteSpec` | `PaletteSpec(preset="candy")` | `color_a` 用于圆点，`color_b` 用于底色。 |
| `dot_radius` | `int` | `5` | 圆点半径。 |
| `dot_spacing` | `int` | `24` | 圆点中心间距。 |
| `staggered` | `bool` | `True` | 是否让相邻点阵行错开。 |

### `LaceTopSpec`

带蕾丝袜口的袜子。

```python
zp.LaceTopSpec(
    base_style="sheer",
    lace_height=46,
    motif_scale=14,
    lace_opacity=0.72,
)
```

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `base_style` | `"opaque" \| "sheer"` | `"sheer"` | 基础袜子渲染风格。 |
| `lace_height` | `int` | `46` | 蕾丝带像素高度。 |
| `motif_scale` | `int` | `14` | 重复花纹像素尺寸。 |
| `lace_opacity` | `float` | `0.72` | 蕾丝覆盖透明度。 |

---

## 低层纹理渲染

### `render_sock_texture()`

```python
zp.render_sock_texture(
    leg,
    spec,
    coverage_ratio=0.72,
)
```

将程序化袜子纹理渲染到 Pillow RGBA 腿部图片上。

| 参数 | 说明 |
| --- | --- |
| `leg` | RGBA Pillow 图片。 |
| `spec` | 任意 `SockTextureSpec`。 |
| `coverage_ratio` | 袜子覆盖比例。`0.0` 表示不穿袜，`1.0` 表示完全覆盖。 |

返回新的 RGBA 图片。源图片中的透明像素不会被修改。

---

## 低层 Matplotlib 绘制

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

在 Matplotlib 坐标轴上绘制一条带纹理的腿。

| 参数 | 说明 |
| --- | --- |
| `ax` | 目标 Matplotlib 坐标轴。 |
| `leg` | Pillow 图片或 `LegAsset`。 |
| `x` | 水平中心位置，使用近似像素的图表坐标。 |
| `value` | 袜子覆盖比例。 |
| `scale` | 统一缩放比例。 |
| `texture` | 纹理规格。不传时使用 `OpaqueSpec()`。 |
| `baseline` | 图片底部的 y 坐标。 |
| `zorder` | Matplotlib z-order。 |

返回 `AxesImage` artist。

---

## 素材 API

### `load_default_assets()`

```python
library = zp.load_default_assets()
```

从包资源中加载内置腿部素材库。

当前内置素材包含 13 对来源双腿 / 26 条单腿 PNG。所有腿部图片高度均为 720 像素。

### `open_leg()`

```python
image = zp.open_leg(library.assets["leg_10_l"])
```

将打包腿部素材打开为 RGBA Pillow 图片。

### `LegAssetLibrary`

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `assets` | `dict[str, LegAsset]` | 所有腿部素材，按 asset id 索引。 |
| `pairs` | `dict[int, SourcePair]` | 原始 pair 元数据，按 pair id 索引。 |

方法：

```python
library.assets_by_side("l")
library.assets_by_side("r")
```

### `LegAsset`

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `asset_id` | `str` | 例如 `"leg_10_l"`。 |
| `side` | `str` | `"l"` 或 `"r"`。 |
| `relative_path` | `str` | 在打包 split assets 下的相对路径。 |
| `resource` | `Traversable` | `importlib.resources` 资源句柄。 |
| `source_pair_id` | `int` | 来源 manifest 中的 pair id。 |
| `width` | `int` | 图片宽度，单位像素。 |
| `height` | `int` | 图片高度，当前始终为 720。 |

### `SourcePair`

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `pair_id` | `int` | pair 标识。 |
| `left_asset_id` | `str` | 左腿素材 id。 |
| `right_asset_id` | `str` | 右腿素材 id。 |
| `original_pair_gap` | `int` | 原始左右腿连通块之间的像素间距。 |

---

## 纹理预设

便捷预设构造器位于 `zettaiplot.textures.presets`。

```python
from zettaiplot.textures.presets import (
    sheer_black,
    opaque_white,
    school_stripes,
    classic_fishnet,
    lace_sheer_black,
)
```

| 函数 | 返回 |
| --- | --- |
| `sheer_black()` | `SheerSpec(color="black", denier=36, ...)` |
| `opaque_white()` | `OpaqueSpec(color="white", opacity=0.84, ...)` |
| `school_stripes()` | `HorizontalStripesSpec(palette=PaletteSpec(preset="school"), ...)` |
| `classic_fishnet()` | `FishnetSpec(color="black", cell_size=30, ...)` |
| `lace_sheer_black()` | `LaceTopSpec(base_style="sheer", ...)` |

---

## 工具函数

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

在 `#FDEAE4` 背景上生成一个小矩形图例纹理样本。

---

## 完整示例

### 自定义单系列纹理

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

### 每个图例项使用不同纹理

```python
import matplotlib.pyplot as plt
import zettaiplot as zp

data = {
    "A 班": [80, 120, 95],
    "B 班": [60, 140, 110],
}

container = zp.sockbar(
    data,
    label=["第一周", "第二周", "第三周"],
    hue_textures={
        "A 班": zp.OpaqueSpec(color="black"),
        "B 班": zp.HorizontalStripesSpec(
            palette=zp.PaletteSpec(preset="school"),
        ),
    },
    legend_kwargs={"ncol": 2},
)

plt.tight_layout()
plt.show()
```

### 控制重叠

```python
zp.sockbar(
    {
        "A": [10, 12, 14],
        "B": [8, 16, 11],
        "C": [13, 9, 18],
    },
    label=["第一天", "第二天", "第三天"],
    hue_inner_gap=-20,
)
```

### 手动渲染纹理

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

### 手动绘制单条腿

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

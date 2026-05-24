# Agent Instructions for ZettaiPlot

## 1. Context & Tech Stack
- **Language**: Python 3.12
- **Package Manager**: `uv`
- **Linter/Formatter**: `Ruff`

## 2. Environment Commands
- **Install**: `uv sync`
- **Add Dependency**: `uv add <package>`
- **Run Tests**: `uv run pytest`
- **Linting**: `uv run ruff check --fix`
- **Check Types**: `uv run pyright` (或 mypy)

## 3. Coding Standards (Strict)
### Typing (Python 3.12+)
- **Generic Syntax**: 必须使用 PEP 695 语法。例如：`def get_first[T](items: list[T]) -> T: ...`
- **No Any**: 非必要不使用 `Any`，如无法确定类型可以使用 `object` 或 `Protocol`。
- **Type Aliases**: 优先使用 `type Name = str | int`。

### Documentation
- **Style**: 遵循 Google Python Style Guide。
- **Docstrings**: 所有公共函数、类、模块必须包含 Docstrings。
- **Comments**: 不要解释代码显而易见的功能，仅在逻辑复杂或涉及特殊业务规则时添加说明。
- **Language**: Docstrings 使用 English ，其余注释使用中文。
- **Algorithm Comments**: 凡涉及图形学计算（如圆柱体扭曲、边缘富集效应），必须在代码注释中明示数学公式的推导逻辑。

## 4. Project Structure
AI Agent 在操作文件时建议遵循以下结构，若需要增改应询问是否允许：
- `src/ZettaiPlot/`: 源代码核心。
  - `assets/`: 必要素材，将打包到库中
- `tests/`: 测试文件，结构必须与 `src/` 保持 1:1 镜像。
- `scripts/`: 临时维护脚本。
- `assets/`: 原始/临时素材

## 5. While Planing

在计划时，最重要的不是具体技术路径，而是规划好需要实现什么效果，最终构建出来是什么样的，对外接口是什么样的——这些比内部如何工作更重要。

## 6. About the Project

Please Read and update `project.md` in real time.

# Agent Instructions for ZettaiPlot

## 1. Context & Tech Stack
- **Language**: Python 3.12+ (Prioritize modern syntax)
- **Package Manager**: `uv`
- **Linter/Formatter**: `Ruff`
- **Type Checker**: `Pyright` (Basic mode with strict rule add-ons)

## 2. Environment Commands
- **Add Dependency**: `uv add <package>`
- **Run Tests**: `uv run pytest`
- **Lint & Format**: `uv run ruff check --fix` and `uv run ruff format`
- **Type Check**: `uv run pyright`

## 3. Coding Standards & Type Safety

### Typing & Static Analysis (Performance-First & Pragmatic)

- **Trust with Autonomy**: We trust your capability to write clean Python 3.12. Do not over-engineer type definitions for purely internal, localized, or self-contained logic where the type is clear from the immediate context.
- **Generic Syntax**: MUST use PEP 695 syntax. (e.g., `def get_first[T](items: list[T]) -> T: ...`)
- **Type Aliases**: MUST use PEP 695 `type` statement. (e.g., `type Name = str | int`)
- **No Implicit/Blanket Any**: Avoid explicit `Any` where possible. Use `object` or `Protocol` for structural typing.
- **Strict Restrictions on `typing.cast`**: 
  Do NOT abuse `typing.cast` to quiet the compiler. At runtime, `typing.cast` is a regular Python function call. **It MUST be completely avoided inside high-frequency loops or hot paths** (e.g., texture rendering, coordinate transformations), as its function-call overhead is unacceptable in performance-critical code.
- **Zero-Overhead Policy for Hot Paths (Critical)**:
  Inside high-frequency loops, rendering pipelines, or heavy math calculations, **execution speed takes absolute priority over static analysis satisfaction**.
  - *No In-Loop Safety Checks*: Avoid placing runtime safety checks (such as `isinstance()`, `hasattr()`, or `assert`) *inside* hot loops, as they introduce severe dynamic overhead.
  - *Hoist or Suppress*: Always attempt to hoist validations *before/outside* the loop. If validation cannot be cleanly hoisted and Pyright still complains, **you MUST favor static type suppression (`# pyright: ignore`) over introducing runtime safety checks**.
- **Reasonable Type Suppression**: 
  When Pyright emits a warning on a standard Python dynamic pattern (e.g., parsing complex JSON, dictionary unpacking, or inside utility tools in `scripts/`), and adding explicit typing would result in anti-patterns, excessive boilerplate, or runtime degradation:
  - You are permitted to use local suppression: `# pyright: ignore[rule_name]`.
  - Avoid blanket `# type: ignore`. Always target the specific rule and leave a brief comment if the reason isn't self-evident.

### Documentation & Comments
- **Style**: Strictly follow the Google Python Style Guide.
- **Docstrings**: Required for all public modules, classes, and functions. 
- **Algorithm Clarity**: For any graphics computing or coordinate transformations (e.g., cylinder warping, edge enrichment effects), you MUST provide the mathematical formulas and derivation logic within the inline Chinese comments.
- **No Redundant Comments**: Do not explain *what* the code does if it is self-evident. Explain *why* it was designed that way or the underlying constraints.

## 4. Project Structure
Do not alter the project topology without explicit confirmation. Follow this layout:
- `src/zettaiplot/`: Core source code (Package name is lowercase per PEP 8).
  - `assets/`: Built-in asset files packaged into the library.
- `tests/`: Unit tests, mirroring the `src/zettaiplot/` structure 1:1.
- `scripts/`: Offline utility, maintenance, and asset preview scripts.
- `assets/`: Raw or temporary source assets (not packaged into distribution).

## 5. Architectural Principle: Planning over Implementation
When designing features or refactoring:
- Prioritize **end-state effects**, **public APIs**, and **interface boundaries** over internal implementation mechanics.
- Define what the system achieves and its external contract *before* writing the inner loop.

## 6. Project Knowledge Synchronization
- Read and update `project.md` in real-time as the project evolves to keep architectural context fresh.
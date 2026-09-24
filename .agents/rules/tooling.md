# Tooling & Environment Invariants

- Always run Python commands, scripts, and test suites using `uv`:
  - `uv run pytest`
  - `uv run python <script>`
- When native C++ sources in `src/` are modified, rebuild with `cmake --build build` and copy the resulting `_tkblend*.so` into `.venv/lib/python3.12/site-packages/tkblend/` and `tkblend/`.

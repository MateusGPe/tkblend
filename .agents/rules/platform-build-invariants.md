# Multiplatform Build & Packaging Invariants

This rule documents critical invariants, hard-won fixes, and regression prevention guidelines across Linux, macOS, and Windows CI/CD, cibuildwheel, CMake, and native C++ extension workflows for `tkblend`.

---

## 1. 🍎 macOS (`macos-14` ARM64 / `macos-15-intel` x86_64 / delocate)

1. **Static FreeType Compilation**:
   - **Rule**: FreeType must always be built from source statically via `FetchContent` on `APPLE` with `BUILD_SHARED_LIBS=OFF`.
   - **Why**: Homebrew's `freetype` dylibs are compiled with `MACOSX_DEPLOYMENT_TARGET >= 14.0`. Linking dynamic Homebrew FreeType causes `delocate-wheel` to reject the wheel for deployment targets `10.15` (Intel) and `11.0` (ARM64).

2. **Static Tcl/Tk Stubs**:
   - **Rule**: Link only against static stub libraries (`libtkstub8.6.a`, `libtclstub8.6.a`) via `brew install tcl-tk` and `CMAKE_PREFIX_PATH=$(brew --prefix tcl-tk)`.
   - **Why**: Never dynamically link `Tk.framework` or `Tcl.framework` at build time to ensure wheels load across different Python distributions and Tk versions.

3. **Dynamic Symbol Resolution for Tk Cocoa Internals**:
   - **Rule**: Resolve Cocoa Tk symbols like `TkMacOSXGetCGContextForDrawable` dynamically at runtime via `dlsym(RTLD_DEFAULT, "TkMacOSXGetCGContextForDrawable")`.
   - **Why**: Direct linker references or `__attribute__((weak_import))` still require build-time framework linking on older runner images, causing build failures.

4. **No Unsafe ObjC Window Shaping**:
   - **Rule**: `is_window_shaping_supported()`, `apply_round_rect_shape()`, and `clear_window_shape()` must return `false` on macOS in `src/window_shape.cpp`.
   - **Why**: In Aqua Cocoa Tk, `widget.winfo_id()` returns a pointer to Tk's internal C struct `MacDrawable`, NOT an Objective-C `NSView*`. Casting this pointer to `NSView*` and calling ObjC selectors (`[view isKindOfClass:...]`) causes an immediate segmentation fault (`EXC_BAD_ACCESS`). Child Tk widgets share the top-level `TKContentView` and rely on Blend2D canvas clipping.

---

## 2. 🪟 Windows (`windows-latest` / MSVC / delvewheel)

1. **CMake Prefix Propagation to cibuildwheel**:
   - **Rule**: Always pass `CMAKE_PREFIX_PATH` in both the GitHub Actions step `env:` and via `CIBW_ENVIRONMENT_WINDOWS: "CMAKE_PREFIX_PATH='${{ steps.tcltk.outputs.environment-path }}/Library'"`.
   - **Why**: `cibuildwheel` spawns isolated build subshells that do not inherit `$GITHUB_ENV`.

2. **Excluding Tcl/Tk DLLs in delvewheel**:
   - **Rule**: Maintain `--exclude tcl86t.dll --exclude tk86t.dll` in `tool.cibuildwheel.windows.repair-wheel-command`.
   - **Why**: Prevents delvewheel from vendoring host Tcl/Tk DLLs into the wheel, allowing host Python's Tkinter to provide them at runtime.

3. **Headless & Standalone Test Virtualenv Isolation**:
   - **Rule**: All Tkinter imports in `tkblend/__init__.py` must be wrapped in `try/except ImportError`. The C++ extension `_tkblend` is always imported directly.
   - **Why**: cibuildwheel's clean Windows test virtualenvs do not bundle `_tkinter.pyd`. Guarding imports allows the smoke test `python -c "from tkblend import _tkblend; print('C++ extension loaded successfully')"` to verify binary integrity without crashing with `ModuleNotFoundError: No module named 'tkinter'`.

4. **Target Installation Destination**:
   - **Rule**: Configure `install(TARGETS _tkblend LIBRARY DESTINATION tkblend RUNTIME DESTINATION tkblend ARCHIVE DESTINATION tkblend)` in `CMakeLists.txt`.
   - **Why**: Ensures Windows `.pyd` files are placed inside the `tkblend/` package folder.

---

## 3. 🐧 Linux (`manylinux_2_28` / x86_64 / aarch64 / auditwheel)

1. **Docker Container Dependencies**:
   - **Rule**: Declare `yum install -y tcl-devel tk-devel xorg-x11-server-Xvfb xorg-x11-xinit` under `tool.cibuildwheel.linux.before-all`.
   - **Why**: manylinux container environments run in clean isolation from the host runner.

2. **Virtual Display Server for Tests**:
   - **Rule**: Run test suites using `xvfb-run -a pytest {project}/tests`.
   - **Why**: Tkinter requires a running X11 display server to initialize widgets in headless CI runners.

---

## 4. 🛠️ Local Development & Testing

- Always run Python commands and test suites using `uv`:
  ```bash
  uv run pytest
  uv run python <script>
  ```
- When native C++ sources in `src/` are modified, rebuild the native extension with `cmake --build build` and copy the compiled `_tkblend*.so` / `_tkblend*.pyd` into `tkblend/` and the active `.venv` environment.

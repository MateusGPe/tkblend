#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "================================================================="
echo " Building tkblend with ASan (Address) & UBSan (UndefinedBehavior)"
echo "================================================================="

# Clean any existing build artifacts to ensure fresh sanitizer instrumentation
rm -rf build/
find tkblend/ -name "_tkblend*.so" -delete 2>/dev/null || true

# Recompile with ENABLE_SANITIZERS=ON
if command -v uv >/dev/null 2>&1; then
    uv pip install --reinstall --no-deps -e . --no-build-isolation -Ccmake.define.ENABLE_SANITIZERS=ON -Ccmake.define.CMAKE_BUILD_TYPE=RelWithDebInfo -v
else
    python -m pip install --force-reinstall --no-deps -e . --no-build-isolation -Ccmake.define.ENABLE_SANITIZERS=ON -Ccmake.define.CMAKE_BUILD_TYPE=RelWithDebInfo -v
fi

# Configure Sanitizer environment variables
export ASAN_OPTIONS="detect_leaks=0:abort_on_error=1:alloc_dealloc_mismatch=0:disable_coredump=0"
export UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
export PYTHONMALLOC=malloc

# Detect libasan path if needed for CPython binary preloading on Linux
if [[ "$(uname -s)" == "Linux" ]]; then
    LIBASAN="$(gcc -print-file-name=libasan.so 2>/dev/null || true)"
    LIBSTDCXX="$(gcc -print-file-name=libstdc++.so 2>/dev/null || true)"
    if [[ -f "${LIBASAN}" ]]; then
        PRELOAD="${LIBASAN}"
        if [[ -f "${LIBSTDCXX}" ]]; then
            PRELOAD="${PRELOAD}:${LIBSTDCXX}"
        fi
        export LD_PRELOAD="${PRELOAD}:${LD_PRELOAD:-}"
        echo "Preloaded ASan & libstdc++ runtime: ${PRELOAD}"
    fi
fi

echo "================================================================="
echo " Running Test Suite under ASan & UBSan"
echo "================================================================="

if [[ -f "${PROJECT_ROOT}/.venv/bin/pytest" ]]; then
    PYTEST_BIN="${PROJECT_ROOT}/.venv/bin/pytest"
else
    PYTEST_BIN="pytest"
fi

if command -v xvfb-run >/dev/null 2>&1 && [[ "$(uname -s)" == "Linux" ]]; then
    xvfb-run -a "${PYTEST_BIN}" -v
else
    "${PYTEST_BIN}" -v
fi

echo "================================================================="
echo " ✅ ASan & UBSan checks PASSED with zero errors!"
echo "================================================================="

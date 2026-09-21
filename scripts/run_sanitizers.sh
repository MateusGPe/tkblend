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

# Recompile with ENABLE_SANITIZERS=ON and ENABLE_NANOBIND_LEAK_CHECK=ON
if command -v uv >/dev/null 2>&1; then
    uv pip install --reinstall --no-deps -e . --no-build-isolation \
        -Ccmake.define.ENABLE_SANITIZERS=ON \
        -Ccmake.define.ENABLE_NANOBIND_LEAK_CHECK=ON \
        -Ccmake.define.CMAKE_BUILD_TYPE=RelWithDebInfo -v
else
    python -m pip install --force-reinstall --no-deps -e . --no-build-isolation \
        -Ccmake.define.ENABLE_SANITIZERS=ON \
        -Ccmake.define.ENABLE_NANOBIND_LEAK_CHECK=ON \
        -Ccmake.define.CMAKE_BUILD_TYPE=RelWithDebInfo -v
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
echo " Running Test Suite under ASan, UBSan & Nanobind Leak Checker"
echo "================================================================="

LOG_FILE="${PROJECT_ROOT}/sanitizers.log"
rm -f "${LOG_FILE}"

RUNNER=()
if command -v xvfb-run >/dev/null 2>&1 && [[ "$(uname -s)" == "Linux" ]]; then
    RUNNER+=(xvfb-run -a)
fi

if command -v uv >/dev/null 2>&1; then
    CMD=("${RUNNER[@]}" uv run pytest -v)
elif [[ -f "${PROJECT_ROOT}/.venv/bin/pytest" ]]; then
    CMD=("${RUNNER[@]}" "${PROJECT_ROOT}/.venv/bin/pytest" -v)
else
    CMD=("${RUNNER[@]}" pytest -v)
fi

echo "Executing: ${CMD[*]}"
set +e
"${CMD[@]}" 2>&1 | tee "${LOG_FILE}"
TEST_EXIT_CODE=${PIPESTATUS[0]}
set -e

echo "================================================================="
echo " Checking for Sanitizer Violations & Nanobind Leaks in Log..."
echo "================================================================="

LEAK_COUNT=$(grep -c "nanobind: leaked" "${LOG_FILE}" || true)
ASAN_COUNT=$(grep -c "AddressSanitizer" "${LOG_FILE}" || true)
UBSAN_COUNT=$(grep -c "runtime error:" "${LOG_FILE}" || true)

if [[ ${TEST_EXIT_CODE} -ne 0 ]]; then
    echo "❌ Test suite failed with exit code ${TEST_EXIT_CODE}!"
    exit "${TEST_EXIT_CODE}"
fi

if [[ ${LEAK_COUNT} -gt 0 ]]; then
    echo "❌ Nanobind memory leaks detected! (${LEAK_COUNT} occurrences)"
    grep -E "nanobind: leaked|leaked instance|leaked type" "${LOG_FILE}" || true
    exit 1
fi

if [[ ${ASAN_COUNT} -gt 0 ]]; then
    echo "❌ AddressSanitizer errors detected! (${ASAN_COUNT} occurrences)"
    grep "AddressSanitizer" "${LOG_FILE}" || true
    exit 1
fi

if [[ ${UBSAN_COUNT} -gt 0 ]]; then
    echo "❌ UndefinedBehaviorSanitizer errors detected! (${UBSAN_COUNT} occurrences)"
    grep "runtime error:" "${LOG_FILE}" || true
    exit 1
fi

echo "================================================================="
echo " ✅ ASan, UBSan & Nanobind checks PASSED with zero errors/leaks!"
echo "================================================================="

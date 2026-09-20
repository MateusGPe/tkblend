#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "================================================================="
echo " Building tkblend with Code Coverage Instrumentation (gcov/gcovr)"
echo "================================================================="

# Clean build and coverage directories
rm -rf build/coverage
mkdir -p build/coverage/python_html build/coverage/cpp_html

# Clean stale coverage and gcda files
find . -name "*.gcda" -delete 2>/dev/null || true
find . -name "*.gcno" -delete 2>/dev/null || true
rm -f .coverage .coverage.* coverage.xml

# Recompile with ENABLE_COVERAGE=ON
if command -v uv >/dev/null 2>&1; then
    uv pip install --reinstall --no-deps -e . --no-build-isolation -Ccmake.define.ENABLE_COVERAGE=ON -Ccmake.define.CMAKE_BUILD_TYPE=Debug -v
else
    python -m pip install --force-reinstall --no-deps -e . --no-build-isolation -Ccmake.define.ENABLE_COVERAGE=ON -Ccmake.define.CMAKE_BUILD_TYPE=Debug -v
fi

echo "================================================================="
echo " Running Pytest with Python Code Coverage (pytest-cov)"
echo "================================================================="

RUNNER="pytest"
if command -v uv >/dev/null 2>&1; then
    RUNNER="uv run pytest"
fi

if command -v xvfb-run >/dev/null 2>&1 && [[ "$(uname -s)" == "Linux" ]]; then
    xvfb-run -a ${RUNNER} --cov=tkblend \
        --cov-report=html:build/coverage/python_html \
        --cov-report=xml:build/coverage/python_cov.xml \
        --cov-report=term-missing \
        --cov-fail-under=90 \
        -v
else
    ${RUNNER} --cov=tkblend \
        --cov-report=html:build/coverage/python_html \
        --cov-report=xml:build/coverage/python_cov.xml \
        --cov-report=term-missing \
        --cov-fail-under=90 \
        -v
fi

echo "================================================================="
echo " Generating C++ Coverage Report with gcovr"
echo "================================================================="

GCOVR="gcovr"
if command -v uv >/dev/null 2>&1 && uv run which gcovr >/dev/null 2>&1; then
    GCOVR="uv run gcovr"
fi

if command -v gcovr >/dev/null 2>&1 || (command -v uv >/dev/null 2>&1 && uv run which gcovr >/dev/null 2>&1); then
    ${GCOVR} \
        --root . \
        --filter 'src/' \
        --exclude-unreachable-branches \
        --exclude-throw-branches \
        --print-summary \
        --html-details build/coverage/cpp_html/index.html \
        --xml build/coverage/cpp_cov.xml \
        --fail-under-line 85
    echo "C++ HTML Report: build/coverage/cpp_html/index.html"
else
    echo "Warning: gcovr not found in PATH or uv. Install gcovr (uv pip install gcovr) for C++ HTML/XML coverage reports."
fi

echo "================================================================="
echo " ✅ Code coverage completed successfully!"
echo " Python Report: build/coverage/python_html/index.html"
echo "================================================================="

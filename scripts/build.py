#!/usr/bin/env python3
"""
Cross-platform build script for tkblend.
Compiles the C++ extension module for local development and testing.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def run_command(cmd, cwd=ROOT_DIR):
    print(f"==> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Build tkblend C++ extension")
    parser.add_argument(
        "--editable", "-e",
        action="store_true",
        default=True,
        help="Install in editable mode for local development (default: True)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before compiling"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose compiler output"
    )
    args = parser.parse_args()

    if args.clean:
        print("==> Cleaning previous build artifacts...")
        import shutil
        for path in [ROOT_DIR / "build", ROOT_DIR / "_skbuild"]:
            if path.exists():
                shutil.rmtree(path)
                print(f"    Removed {path}")

    cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    if args.verbose:
        cmd.append("-v")

    run_command(cmd)
    print("\n[SUCCESS] tkblend built and installed successfully!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Cross-platform distribution builder for tkblend.
Builds source distributions (sdist) and wheels locally using `build`.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"

def run_command(cmd, cwd=ROOT_DIR):
    print(f"==> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Build tkblend source and binary distributions")
    parser.add_argument(
        "--sdist-only",
        action="store_true",
        help="Only build source distribution (sdist)"
    )
    parser.add_argument(
        "--wheel-only",
        action="store_true",
        help="Only build binary wheel"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Clean dist/ directory before building (default: True)"
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Keep existing files in dist/"
    )
    args = parser.parse_args()

    # Ensure build is installed
    try:
        import build
    except ImportError:
        print("==> Installing 'build' package...")
        run_command([sys.executable, "-m", "pip", "install", "build"])

    if args.clean and DIST_DIR.exists():
        print(f"==> Cleaning {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "build", "--outdir", str(DIST_DIR)]
    if args.sdist_only:
        cmd.append("--sdist")
    elif args.wheel_only:
        cmd.append("--wheel")

    run_command(cmd)

    # Check dist packages with twine if installed
    twine_path = shutil.which("twine")
    if twine_path:
        print("\n==> Checking distribution packages with twine...")
        subprocess.run([sys.executable, "-m", "twine", "check", f"{DIST_DIR}/*"], cwd=ROOT_DIR)

    # List produced files
    print("\n" + "=" * 60)
    print("Generated Distribution Files in dist/:")
    print("=" * 60)
    for file in sorted(DIST_DIR.iterdir()):
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            size_kb = file.stat().st_size / 1024
            if size_mb >= 1.0:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_str = f"{size_kb:.1f} KB"
            print(f" - {file.name:<45} ({size_str})")
    print("=" * 60)
    print("[SUCCESS] Distribution packages created successfully!")

if __name__ == "__main__":
    main()

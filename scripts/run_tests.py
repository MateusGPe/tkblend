#!/usr/bin/env python3
"""
Cross-platform test runner for tkblend.
Handles virtual framebuffers (xvfb) on headless Linux environments automatically.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description="Run tkblend test suite")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose test output"
    )
    parser.add_argument(
        "-k", "--filter",
        type=str,
        default="",
        help="Run tests matching given keyword expression"
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Extra arguments forwarded to pytest"
    )
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest"]
    if args.verbose:
        cmd.append("-v")
    if args.filter:
        cmd.extend(["-k", args.filter])
    if args.extra_args:
        cmd.extend(args.extra_args)

    # Linux headless display handling
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        xvfb_path = shutil.which("xvfb-run")
        if xvfb_path:
            print("==> No DISPLAY detected. Using xvfb-run for virtual display...")
            cmd = [xvfb_path, "-a"] + cmd
        else:
            print(
                "WARNING: No DISPLAY variable set and xvfb-run not found. "
                "Tkinter tests requiring UI may fail.",
                file=sys.stderr
            )

    print(f"==> Running tests: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()

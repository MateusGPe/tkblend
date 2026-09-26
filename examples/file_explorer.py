"""
tkblend File Explorer Example (Forwarder).
Re-exports FileExplorerApp from examples.old.file_explorer.
"""

from __future__ import annotations

from examples.old.file_explorer import (
    FileExplorerApp,
    FILE_CATEGORIES,
    main,
)

__all__ = [
    "FileExplorerApp",
    "FILE_CATEGORIES",
    "main",
]

if __name__ == "__main__":
    main()

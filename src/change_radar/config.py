"""Static configuration for the current project phase."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
}

FALLBACK_IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".turbo",
}

MAX_FILE_SIZE_BYTES = 512_000
DEFAULT_DB_DIRNAME = ".change-radar"
DEFAULT_DB_FILENAME = "index.db"


def default_db_path(repo_root: Path) -> Path:
    """Return the default SQLite path for a repository."""
    return repo_root / DEFAULT_DB_DIRNAME / DEFAULT_DB_FILENAME

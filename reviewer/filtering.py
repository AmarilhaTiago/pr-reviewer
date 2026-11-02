"""Drop files that should not be reviewed (lockfiles, build output, binaries...)."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import PurePosixPath

from reviewer.diff import FileDiff

DEFAULT_IGNORE: list[str] = [
    "*.lock",
    "package-lock.json",
    "composer.lock",
    "dist/**",
    "*.min.js",
    "*.svg",
    "*/migrations/0*_auto_*.py",
]


def parse_patterns(csv: str) -> list[str]:
    return [p.strip() for p in csv.split(",") if p.strip()]


def _matches(path: str, patterns: Iterable[str]) -> bool:
    name = PurePosixPath(path).name
    return any(fnmatch(path, p) or fnmatch(name, p) for p in patterns)


def filter_files(
    files: Iterable[FileDiff], patterns: Iterable[str] = DEFAULT_IGNORE
) -> tuple[list[FileDiff], list[FileDiff]]:
    patterns = list(patterns)
    kept: list[FileDiff] = []
    ignored: list[FileDiff] = []
    for f in files:
        (ignored if f.is_binary or _matches(f.path, patterns) else kept).append(f)
    return kept, ignored

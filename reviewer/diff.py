"""Parser for unified diffs (as produced by ``git diff`` / GitHub)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["added", "modified", "deleted", "renamed"]

_FILE_HEADER = re.compile(r"^diff --git a/(.*) b/(.*)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class DiffLine:
    kind: Literal["+", "-", " "]
    text: str
    new_number: int | None  # line number in the new file; None for removed lines


@dataclass
class Hunk:
    header: str
    new_start: int
    lines: list[DiffLine] = field(default_factory=list)

    @property
    def raw(self) -> str:
        body = "\n".join(f"{line.kind}{line.text}" for line in self.lines)
        return f"{self.header}\n{body}" if body else self.header

    @property
    def numbered(self) -> str:
        """Like ``raw`` but every added/context line carries its line number in the new file,
        so the model does not have to count from the hunk header."""
        rows = [self.header]
        for line in self.lines:
            number = "" if line.new_number is None else str(line.new_number)
            rows.append(f"{number:>5} {line.kind}{line.text}")
        return "\n".join(rows)


@dataclass
class FileDiff:
    path: str
    old_path: str | None = None
    status: Status = "modified"
    is_binary: bool = False
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def added_lines(self) -> dict[int, str]:
        return {
            line.new_number: line.text
            for hunk in self.hunks
            for line in hunk.lines
            if line.kind == "+" and line.new_number is not None
        }


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: Hunk | None = None
    new_no = 0

    for raw in text.splitlines():
        header = _FILE_HEADER.match(raw)
        if header:
            old, new = header.groups()
            current = FileDiff(path=new, old_path=old if old != new else None)
            files.append(current)
            hunk = None
            continue
        if current is None:
            continue

        if hunk is None or raw.startswith("@@"):
            hunk_header = _HUNK_HEADER.match(raw)
            if hunk_header:
                hunk = Hunk(header=raw, new_start=int(hunk_header.group(1)))
                current.hunks.append(hunk)
                new_no = hunk.new_start
                continue
            if hunk is None:
                _apply_file_metadata(current, raw)
                continue

        if raw.startswith("\\"):  # "\ No newline at end of file"
            continue
        kind = raw[:1] if raw[:1] in "+-" else " "
        content = raw[1:] if raw else ""
        if kind == "-":
            hunk.lines.append(DiffLine("-", content, None))
        else:
            hunk.lines.append(DiffLine(kind, content, new_no))
            new_no += 1
    return files


def _apply_file_metadata(file: FileDiff, line: str) -> None:
    if line.startswith("new file mode"):
        file.status = "added"
    elif line.startswith("deleted file mode"):
        file.status = "deleted"
    elif line.startswith("rename from "):
        file.status = "renamed"
        file.old_path = line.removeprefix("rename from ")
    elif line.startswith("rename to "):
        file.path = line.removeprefix("rename to ")
    elif line.startswith("Binary files") or line.startswith("GIT binary patch"):
        file.is_binary = True

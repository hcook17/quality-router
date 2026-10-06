"""Unified-diff parsing: which new-side lines did a change add or modify."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(text: str) -> dict[str, set[int]]:
    """Map new-side path -> set of added line numbers. Deleted files are skipped."""
    changed: dict[str, set[int]] = {}
    path: str | None = None
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:].strip().split("\t", 1)[0]
            if target == "/dev/null":
                path = None
            else:
                path = target[2:] if target.startswith("b/") else target
                changed.setdefault(path, set())
            continue
        if raw.startswith("--- ") or raw.startswith("diff --git"):
            continue
        hunk = _HUNK.match(raw)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if path is None or new_line == 0:
            continue
        if raw.startswith("+"):
            changed[path].add(new_line)
            new_line += 1
        elif raw.startswith("-"):
            continue
        elif raw.startswith("\\"):
            continue
        else:
            new_line += 1
    return {p: lines for p, lines in changed.items() if lines}


def git_diff(base: str, cwd: Path, pathspecs: list[str] | None = None) -> str:
    """`git diff --unified=0 <base>...HEAD`, argv list, no shell."""
    argv = ["git", "-C", str(cwd), "diff", "--unified=0", "--no-color", f"{base}...HEAD"]
    if pathspecs:
        argv += ["--", *pathspecs]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git diff failed for base {base!r}")
    return proc.stdout


def load_diff(diff_file: str | None, base: str | None, cwd: Path, stdin_text: str | None,
              pathspecs: list[str] | None = None) -> dict[str, set[int]]:
    """Resolve the diff source: --diff FILE, --diff - (stdin), or --base REF (git)."""
    if diff_file == "-":
        return parse_unified_diff(stdin_text or "")
    if diff_file:
        return parse_unified_diff(Path(diff_file).read_text(encoding="utf-8"))
    if base:
        return parse_unified_diff(git_diff(base, cwd, pathspecs))
    raise ValueError("provide --base REF or --diff FILE|-")

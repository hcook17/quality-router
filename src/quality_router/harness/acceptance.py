"""Acceptance lock: approved acceptance tests and their spec, pinned by hash.

Evidence: 2605.17242 (requirement-derived acceptance tests, human-approved,
then looped against: gains only when the verifier is reliable), P15
(self-consistent wrong tests when the coding agent writes them), 2609.00069
(agents tamper with their own harness), 2608.23550 (prose rules are not
controls). Approve, then implement: the lock lands in its own commit,
reviewed by the spec owner; later commits leave it and every locked file
untouched. `qr gate acceptance` checks hashes and commit order; the policy
hook blocks the edit before it happens.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from quality_router.harness.report import GateResult
from quality_router.harness.specdoc import DEFAULT_ID_PATTERN, parse_spec

LOCK_PATH = ".quality-router/acceptance.lock.json"
LOCK_VERSION = 1
IMPLEMENTATION_GLOBS = ("**/src/main/**", "src/main/**")


class AcceptanceError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path, root: Path) -> str:
    return Path(os.path.relpath(path.resolve(), root.resolve())).as_posix()


def _ids_in(text: str, id_pattern: str) -> list[str]:
    bounded = re.compile(r"(?<![\w-])(" + id_pattern + r")(?![\w.])")
    return sorted({m.group(1) for m in bounded.finditer(text)})


def build_lock(root: Path, specs: list[Path], tests: list[Path], owned: list[str] | None,
               id_pattern: str = DEFAULT_ID_PATTERN, approved_by: str = "") -> dict[str, Any]:
    """Lock document for `specs` + `tests`; raises when an owned criterion has no locked test."""
    missing = [str(p) for p in [*specs, *tests] if not p.is_file()]
    if missing:
        raise AcceptanceError(f"not found: {missing}")
    if not tests:
        raise AcceptanceError("no test files to lock")
    spec_entries: dict[str, dict[str, Any]] = {}
    defined: list[str] = []
    for spec in specs:
        doc = parse_spec(spec, id_pattern)
        ids = [c.id for c in doc.criteria]
        defined.extend(ids)
        spec_entries[_rel(spec, root)] = {"sha256": sha256_file(spec), "criteria": ids}
    wanted = list(dict.fromkeys(owned or defined))
    unknown = sorted(set(wanted) - set(defined))
    if unknown:
        raise AcceptanceError(f"criteria not in spec: {unknown}")
    test_entries: dict[str, dict[str, Any]] = {}
    covered: set[str] = set()
    for test in tests:
        ids = [i for i in _ids_in(test.read_text(encoding="utf-8", errors="replace"), id_pattern)
               if i in defined]
        covered.update(ids)
        test_entries[_rel(test, root)] = {"sha256": sha256_file(test), "criteria": ids}
    uncovered = [ac for ac in wanted if ac not in covered]
    if uncovered:
        raise AcceptanceError(f"owned criteria with no locked test: {uncovered}")
    return {
        "version": LOCK_VERSION,
        "id_pattern": id_pattern,
        "owned": wanted,
        "specs": spec_entries,
        "tests": test_entries,
        "approved_by": approved_by,
        "locked_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def write_lock(root: Path, lock: dict[str, Any]) -> Path:
    path = root / LOCK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_lock(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AcceptanceError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != LOCK_VERSION:
        raise AcceptanceError(f"{path}: not a version-{LOCK_VERSION} acceptance lock")
    for key in ("specs", "tests"):
        entries = data.get(key)
        if not isinstance(entries, dict) or not all(
                isinstance(v, dict) and isinstance(v.get("sha256"), str) for v in entries.values()):
            raise AcceptanceError(f"{path}: `{key}` must map path -> {{sha256, criteria}}")
    return data


def find_lock(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / LOCK_PATH
        if candidate.is_file():
            return candidate
    return None


def locked_files(lock_path: Path) -> set[Path]:
    """Absolute paths the lock protects: locked tests, specs, and the lock itself."""
    root = lock_path.parent.parent
    lock = load_lock(lock_path)
    paths = {lock_path.resolve()}
    for key in ("tests", "specs"):
        paths.update((root / rel).resolve() for rel in lock[key])
    return paths


def _is_implementation(path: str) -> bool:
    posix = PurePosixPath(path)
    return any(posix.full_match(glob) for glob in IMPLEMENTATION_GLOBS)


def _git(root: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=False)
    return proc.stdout if proc.returncode == 0 else None


def _commit_paths(root: Path, commit: str) -> list[str]:
    out = _git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit)
    return [line for line in (out or "").splitlines() if line]


def _check_history(root: Path, base: str | None, result: GateResult) -> None:
    """Approve, then implement: the lock commit has no src/main change and none precede it."""
    prefix = (_git(root, "rev-parse", "--show-prefix") or "").strip()
    lock_in_git = prefix + LOCK_PATH
    if base is None:
        last = (_git(root, "log", "-1", "--format=%H", "--", LOCK_PATH) or "").strip()
        commits = [last] if last else []
    else:
        listed = _git(root, "rev-list", "--reverse", f"{base}..HEAD")
        if listed is None:
            raise AcceptanceError(f"cannot list commits {base}..HEAD (fetch the base, "
                                  "or use fetch-depth: 0)")
        commits = listed.split()
    paths = {c: _commit_paths(root, c) for c in commits}
    locking = [c for c in commits if lock_in_git in paths[c]]
    if not locking:
        if base is None:
            result.add("warning", "lock_history_unavailable",
                       "no commit for the lock (untracked, not a git repo, or shallow clone)",
                       LOCK_PATH)
        return
    last = locking[-1]
    result.summary["lock_commit"] = last[:12]
    if any(_is_implementation(p) for p in paths[last]):
        result.add("error", "lock_commit_has_implementation",
                   f"{last[:12]} changes src/main with the lock; approve tests in their own "
                   "commit, then implement", LOCK_PATH)
    if base is None:
        return
    earlier = commits[:commits.index(last)]
    implemented = [c[:12] for c in earlier if any(_is_implementation(p) for p in paths[c])]
    if implemented:
        result.add("error", "implementation_before_lock",
                   f"lock re-written after implementation commits {implemented}; tests must be "
                   "approved before the code they check", LOCK_PATH)
    result.add("info", "acceptance_relocked",
               f"{last[:12]} changes the lock in this range; needs spec-owner review "
               "(CODEOWNERS on the lock)", LOCK_PATH)


def gate_acceptance(root: Path, base: str | None = None, strict: bool = False) -> GateResult:
    result = GateResult(gate="acceptance", strict=strict)
    lock_path, lock_rel = root / LOCK_PATH, LOCK_PATH
    if not lock_path.is_file():
        result.add("warning", "no_acceptance_lock",
                   f"no {lock_rel}; scaffold acceptance tests and run `qr spec lock`")
        result.summary.update({"locked_tests": 0, "locked_specs": 0})
        return result
    lock = load_lock(lock_path)
    for rel, entry in lock["specs"].items():
        path = root / rel
        if not path.is_file():
            result.add("warning", "spec_not_checked_out",
                       "locked spec not readable here; check out the coordination repo", rel)
        elif sha256_file(path) != entry["sha256"]:
            result.add("error", "spec_changed_since_lock",
                       "spec differs from the approved version; re-scaffold, review, re-lock "
                       "in a spec-only change", rel)
    for rel, entry in lock["tests"].items():
        path = root / rel
        if not path.is_file():
            result.add("error", "locked_test_missing", "approved acceptance test was removed", rel)
        elif sha256_file(path) != entry["sha256"]:
            result.add("error", "locked_test_modified",
                       f"approved acceptance test changed ({', '.join(entry.get('criteria', []))});"
                       " fix the code, not the test", rel)
    _check_history(root, base, result)
    result.summary.update({
        "locked_tests": len(lock["tests"]),
        "locked_specs": len(lock["specs"]),
        "owned": lock.get("owned", []),
        "approved_by": lock.get("approved_by", ""),
    })
    return result

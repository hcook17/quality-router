"""Team-owned agent regression evaluation: leak-free task workspaces + per-host reports.

Evidence: 2607.03691 (35 releases of one harness, model fixed: 52-131% token
swings functional CI missed; 12.3% run-to-run flips), 2606.12344 / 2607.22585
(harness choice moves resolve rate up to ~24 pp and tokens up to ~40x),
2609.08149 / 2606.12344 (future git objects, visible tests and code-host
egress inflate scores). The unit of evaluation is host + host version + model.

`qr eval` never launches an agent. The host runs the task in the prepared
workspace; CI applies the hidden tests and appends one JSON line per run.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import shutil
import statistics
import subprocess
import tarfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from quality_router.harness.report import GateResult

REQUIRED_RUN_KEYS = ("task", "host", "model", "resolved")


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=not binary, check=False)
    if proc.returncode != 0:
        err = proc.stderr.decode() if binary else proc.stderr
        raise RuntimeError(err.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def _safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = []
    for member in archive.getmembers():
        parts = PurePosixPath(member.name).parts
        if member.name.startswith("/") or ".." in parts or member.issym() or member.islnk():
            continue
        members.append(member)
    return members


def prepare_task(repo: Path, base: str, hidden: list[str], out: Path, task_id: str,
                 prompt: str | None) -> dict[str, Any]:
    """Snapshot `base` with no history, move hidden test paths out of the workspace."""
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} is not empty")
    commit = str(_git(repo, "rev-parse", "--verify", f"{base}^{{commit}}")).strip()
    workspace = out / "workspace"
    hidden_dir = out / "hidden"
    workspace.mkdir(parents=True)
    blob = _git(repo, "archive", "--format=tar", commit, binary=True)
    with tarfile.open(fileobj=io.BytesIO(bytes(blob))) as archive:
        archive.extractall(workspace, members=_safe_members(archive), filter="data")
    moved: dict[str, str] = {}
    for rel in hidden:
        source = workspace / rel
        if not source.exists():
            raise FileNotFoundError(f"hidden path {rel} not present at {commit[:12]}")
        target = hidden_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        moved[rel] = _digest(target)
    _git(workspace, "init", "-q")
    _git(workspace, "add", "-A")
    _git(workspace, "-c", "user.name=qr-eval", "-c", "user.email=qr-eval@localhost",
         "commit", "-q", "--no-verify", "-m", f"task {task_id} base snapshot")
    manifest = {
        "task": task_id,
        "source_repo": repo.name,
        "base_commit": commit,
        "hidden": moved,
        "prompt": prompt or "",
        "controls": {
            "history": "single snapshot commit; no future objects or remotes",
            "hidden_tests": "moved outside workspace; apply only when scoring",
            "egress": "enforce with .quality-router/policy.json egress_allow and the host sandbox",
        },
    }
    (out / "task.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    for file in files:
        sha.update(str(file.relative_to(path.parent)).encode())
        sha.update(file.read_bytes())
    return sha.hexdigest()


@dataclass
class GroupStats:
    key: str
    runs: int
    tasks: int
    resolved: int
    rate: float
    ci_low: float
    ci_high: float
    tokens_median: float | None
    tokens_per_resolved: float | None
    tool_calls_median: float | None
    flip_rate: float


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def group_key(run: dict[str, Any]) -> str:
    version = run.get("host_version") or "?"
    return f"{run['host']}@{version}/{run['model']}"


def load_runs(path: Path) -> list[dict[str, Any]]:
    runs = []
    for nr, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        run = json.loads(line)
        missing = [k for k in REQUIRED_RUN_KEYS if k not in run]
        if missing:
            raise ValueError(f"{path}:{nr}: missing {missing}")
        runs.append(run)
    return runs


def summarize(runs: list[dict[str, Any]]) -> list[GroupStats]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[group_key(run)].append(run)
    stats = []
    for key in sorted(groups):
        members = groups[key]
        resolved = sum(1 for r in members if r["resolved"])
        tokens = [float(r["tokens"]) for r in members if r.get("tokens") is not None]
        calls = [float(r["tool_calls"]) for r in members if r.get("tool_calls") is not None]
        by_task: dict[str, set[bool]] = defaultdict(set)
        for r in members:
            by_task[str(r["task"])].add(bool(r["resolved"]))
        repeated = [outcomes for task, outcomes in by_task.items()
                    if sum(1 for r in members if str(r["task"]) == task) > 1]
        flips = sum(1 for outcomes in repeated if len(outcomes) > 1)
        low, high = wilson(resolved, len(members))
        stats.append(GroupStats(
            key=key,
            runs=len(members),
            tasks=len(by_task),
            resolved=resolved,
            rate=resolved / len(members),
            ci_low=low,
            ci_high=high,
            tokens_median=statistics.median(tokens) if tokens else None,
            tokens_per_resolved=sum(tokens) / resolved if tokens and resolved else None,
            tool_calls_median=statistics.median(calls) if calls else None,
            flip_rate=flips / len(repeated) if repeated else 0.0,
        ))
    return stats


def eval_report(runs: list[dict[str, Any]], baseline: str | None, max_token_increase: float,
                max_rate_drop: float) -> GateResult:
    result = GateResult(gate="eval-report")
    stats = summarize(runs)
    table = {s.key: s for s in stats}
    for s in stats:
        result.summary[s.key] = {
            "runs": s.runs, "tasks": s.tasks, "resolved": s.resolved,
            "resolve_rate": round(s.rate, 4),
            "resolve_rate_ci95": [round(s.ci_low, 4), round(s.ci_high, 4)],
            "tokens_median": s.tokens_median, "tokens_per_resolved": s.tokens_per_resolved,
            "tool_calls_median": s.tool_calls_median, "flip_rate": round(s.flip_rate, 4),
        }
        if s.tasks < 20:
            result.add("info", "small_suite",
                       f"{s.key}: {s.tasks} tasks; differences under ~15 pp are noise", s.key)
    if baseline is None:
        return result
    if baseline not in table:
        result.add("error", "baseline_missing", f"no runs for baseline {baseline!r}")
        return result
    base = table[baseline]
    for s in stats:
        if s.key == baseline:
            continue
        drop = base.rate - s.rate
        overlap = s.ci_high >= base.ci_low and base.ci_high >= s.ci_low
        if drop > max_rate_drop and not overlap:
            result.add("error", "resolve_rate_regression",
                       f"{s.key}: {s.rate:.1%} vs baseline {base.rate:.1%} (CIs disjoint)", s.key)
        elif drop > max_rate_drop:
            result.add("warning", "resolve_rate_drop",
                       f"{s.key}: {s.rate:.1%} vs {base.rate:.1%}; within noise, rerun", s.key)
        if base.tokens_per_resolved and s.tokens_per_resolved:
            increase = s.tokens_per_resolved / base.tokens_per_resolved - 1
            if increase > max_token_increase:
                result.add("error", "token_regression",
                           f"{s.key}: tokens per resolved task +{increase:.0%} vs baseline", s.key)
    return result

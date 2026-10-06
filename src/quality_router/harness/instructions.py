"""Lint agent instruction files (AGENTS.md, CLAUDE.md, copilot/cursor rules).

Evidence: 2608.23550 (about 4-16% of CLAUDE.md security rules have an
enforcing host control -> prose is not policy), 2606.21926 (always-on standards
text did worse than no guidance; selective loading did best -> keep the file
short). The stale-reference and bloat checks rest on hypothesis-only papers
(2606.09090, 2606.15828, 2607.27250): cheap and deterministic, not proven.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from quality_router.harness.report import GateResult

INSTRUCTION_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    ".cursorrules",
    "GEMINI.md",
)
RULE_GLOBS = (".cursor/rules/*.mdc", ".cursor/rules/*.md", ".github/instructions/*.md")
CANONICAL = "AGENTS.md"
BUILD_OUTPUT_DIRS = ("target", "build", "out", "dist", "node_modules", ".gradle")

_BACKTICK = re.compile(r"`([^`\n]+)`")
_PATHLIKE = re.compile(r"^(?:\./)?[\w.@-]+(?:/[\w.@*-]+)+/?$|^[\w-]+\.(?:md|java|kt|xml|yml|yaml|"
                       r"json|toml|gradle|kts|properties|sh|ps1|py|sql|avsc)$")
_FQCN = re.compile(r"^(?:[a-z][a-z0-9_]*\.){2,}[A-Z]\w*$")
_PROHIBITION = re.compile(r"\b(never|do not|don't|must not|must never|forbidden|not allowed)\b",
                          re.IGNORECASE)
_SECURITY = re.compile(
    r"\b(push|force|secret|token|credential|password|\.env|prod(uction)?|phi|pii|hipaa|ferpa|"
    r"delete|rm -rf|drop table|migrat\w*|main branch|deploy|curl|wget|network|egress|"
    r"log(s|ging)?)\b",
    re.IGNORECASE,
)
_LINT_LEAK = re.compile(
    r"\b(indent(ation)?|tabs? vs\.? spaces|\d+ spaces|line length|max(imum)? line|trailing "
    r"whitespace|import order|sort imports|brace style|camelCase|snake_case|semicolons?)\b",
    re.IGNORECASE,
)
_IMPORT_LINE = re.compile(r"^\s*@AGENTS\.md\s*$|see\s+`?AGENTS\.md`?|follow\s+`?AGENTS\.md`?",
                          re.IGNORECASE | re.MULTILINE)


def find_instruction_files(root: Path) -> list[Path]:
    found = [root / name for name in INSTRUCTION_FILES if (root / name).is_file()]
    for pattern in RULE_GLOBS:
        found.extend(sorted(root.glob(pattern)))
    return found


def _policy_patterns(root: Path) -> list[str]:
    policy = root / ".quality-router" / "policy.json"
    if not policy.is_file():
        return []
    try:
        data = json.loads(policy.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [str(p) for key in ("deny_commands", "deny_paths") for p in data.get(key, [])]


def _reference_exists(root: Path, ref: str) -> bool:
    ref = ref.strip().rstrip("/").removeprefix("./")
    if any(ch in ref for ch in "*?<>{}$"):
        return True
    head, _, _ = ref.partition("/")
    if head in BUILD_OUTPUT_DIRS:
        return True
    if _FQCN.match(ref):
        rel = ref.replace(".", "/") + ".java"
        return any(root.glob(f"**/{rel}"))
    if (root / ref).exists():
        return True
    looks_like_file = "." in ref.rsplit("/", 1)[-1]
    return not ((root / head).is_dir() or looks_like_file)


def lint_instructions(root: Path, max_lines: int = 150, strict: bool = False) -> GateResult:
    result = GateResult(gate="instructions", strict=strict)
    files = find_instruction_files(root)
    policy = _policy_patterns(root)
    result.summary["files"] = [str(p.relative_to(root)) for p in files]
    if not files:
        result.add("warning", "no_instruction_file",
                   f"no {CANONICAL}; add a short one with build/test commands and module map")
        return result
    for path in files:
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > max_lines:
            result.add("warning", "context_bloat",
                       f"{len(lines)} lines > {max_lines}; move procedures into on-demand docs",
                       rel)
        in_fence = False
        for nr, line in enumerate(lines, start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for ref in _BACKTICK.findall(line):
                token = ref.strip()
                if " " in token or not (_PATHLIKE.match(token) or _FQCN.match(token)):
                    continue
                if not _reference_exists(root, token):
                    result.add("error", "stale_reference",
                               f"`{token}` does not exist at HEAD", rel, nr)
            if _PROHIBITION.search(line) and _SECURITY.search(line):
                covered = any(p and p.lower().strip("*/ ") in line.lower() for p in policy)
                if not covered:
                    result.add("warning", "prose_only_rule",
                               "security prohibition with no matching .quality-router/policy.json "
                               "entry; prose is not enforced", rel, nr)
            if _LINT_LEAK.search(line):
                result.add("info", "lint_leakage",
                           "style rule; enforce with Spotless/Checkstyle instead of prose", rel, nr)
    _check_divergence(root, files, result)
    return result


def _check_divergence(root: Path, files: list[Path], result: GateResult) -> None:
    canonical = root / CANONICAL
    if not canonical.is_file():
        others = [p for p in files if p.suffix in (".md", "") and p.name != CANONICAL]
        if len(others) > 1:
            result.add("warning", "no_canonical_instructions",
                       f"{len(others)} host instruction files and no {CANONICAL}")
        return
    for path in files:
        if path == canonical or path.parent.name == "rules" or path.parent.name == "instructions":
            continue
        text = path.read_text(encoding="utf-8")
        if not _IMPORT_LINE.search(text):
            result.add("warning", "divergent_instructions",
                       f"does not import {CANONICAL}; host files drift (stamp `@{CANONICAL}`)",
                       str(path.relative_to(root)))

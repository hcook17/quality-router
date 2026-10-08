"""Portable agent policy: one JSON file, enforced through host hooks by a deterministic CLI.

Evidence: 2608.23550 (only about 4-16% of CLAUDE.md security rules have an
enforcing control: prose is "write-only"), 2609.22259 (declared forbidden
operations stopped mutating SQL), 2609.08149 (code-host egress blocking
closes leakage), 2607.07405 (a read-only deterministic predicate in front of
writes; audit each gate's precision). The LLM proposes; `qr policy` allows or
denies.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Any

POLICY_PATH = ".quality-router/policy.json"
ROLE_PATH = ".quality-router/role"
ROLE_ENV = "QR_ROLE"
HARNESS_FILES = (POLICY_PATH, ROLE_PATH, ".quality-router/acceptance.lock.json")
HOLDOUT_READER = "test-author"
TEST_SOURCE_GLOBS = ["**/src/test/**", "**/src/testFixtures/**", "**/src/*Test/**",
                     "**/src/it/**"]

DEFAULT_POLICY: dict[str, Any] = {
    "version": 1,
    "deny_commands": [
        {"pattern": r"\bgit\s+push\b.*(\s--force\b|\s-f\b|\s--force-with-lease\b)",
         "reason": "force push rewrites shared history"},
        {"pattern": r"\bgit\s+reset\s+--hard\s+origin/", "reason": "discards remote-tracked work"},
        {"pattern": r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(/|~|\$HOME)(\s|$)",
         "reason": "recursive delete of a root or home directory"},
        {"pattern": r"\b(mvnw?|gradlew?)\b.*\b(deploy|publish)\b",
         "reason": "artifact publish belongs to CI, not the agent"},
        {"pattern": r"\b(kubectl|helm)\b.*\b(apply|delete|upgrade|install)\b",
         "reason": "cluster mutation belongs to CI/CD"},
        {"pattern": r"\b(psql|mysql|sqlcmd)\b.*\b(drop|truncate|delete\s+from)\b",
         "reason": "destructive SQL against a live database"},
        {"pattern": r"\bGITNEXUS_HOOKS=0\b", "reason": "use the gitnexus off-marker instead"},
        {"pattern": r"\bqr\s+spec\s+lock\b",
         "reason": "locking acceptance tests is the human approval step"},
    ],
    "deny_paths": [
        "**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/*.p12", "**/*.jks",
        "**/secrets/**", "**/.aws/**", "**/.ssh/**", "**/id_rsa*",
        "**/src/test/resources/phi/**", "**/data/phi/**",
    ],
    "protected_branches": ["main", "master", "release/*"],
    "egress_allow": [
        "repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org", "services.gradle.org",
        "localhost", "127.0.0.1", "host.docker.internal",
    ],
    "roles": {
        "spec-author": {"write_allow": ["specs/**", "docs/**", "**/*.md"]},
        "test-author": {"write_allow": [*TEST_SOURCE_GLOBS, "specs/**"]},
        "implementer": {},
        "reviewer": {"write_allow": []},
    },
}

SHELL_TOOLS = ("Bash", "Shell", "run_terminal_cmd", "shell")
FILE_TOOLS = ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Delete", "read_file",
              "edit_file", "delete_file")
READ_TOOLS = ("Read", "read_file")
_SHELL_WRITE = re.compile(
    r"(?:^|[;&|(]|\s)(?:rm|mv|cp|tee|truncate|dd|install|ln|chmod|patch|"
    r"sed\s+(?:-\w+\s+)*-i|perl\s+-\w*i|git\s+(?:rm|mv|checkout|restore|apply|stash))\b|>"
)
_SPEC_LOCK_COMMAND = re.compile(r"\bqr\s+spec\s+lock\b")
_URL = re.compile(r"\b(?:https?|ftp|ssh|git)://(?:[^@/\s]+@)?([A-Za-z0-9.-]+)")
_SCP_LIKE = re.compile(r"(?:^|\s)[\w.-]+@([A-Za-z0-9.-]+):")
_NETWORK_TOOLS = ("curl", "wget", "nc", "ncat", "scp", "rsync", "ssh", "ftp", "telnet")
_SED_SCRIPT = re.compile(r"^[sy]([/|#,]).*\1.*\1[a-zA-Z0-9]*$")


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str = ""
    rule: str = ""


@dataclass(frozen=True)
class Role:
    """What one SDD role may do. `write_allow=None`: no write limit; `[]`: no writes."""

    write_allow: list[str] | None = None
    read_deny: list[str] = field(default_factory=list)
    deny_commands: list[tuple[re.Pattern[str], str]] = field(default_factory=list)


def _commands(items: Any, where: str) -> list[tuple[re.Pattern[str], str]]:
    if not isinstance(items, list):
        raise ValueError(f"{where} must be a list")
    commands = []
    for item in items:
        pattern, reason = ((item, "denied by policy") if isinstance(item, str)
                           else (item["pattern"], item.get("reason", "denied by policy")))
        try:
            commands.append((re.compile(pattern, re.IGNORECASE), reason))
        except re.error as exc:
            raise ValueError(f"{where}: bad pattern {pattern!r}: {exc}") from exc
    return commands


def _globs(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a list of globs")
    return [str(p) for p in value]


def _roles(data: Any) -> dict[str, Role]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("roles must be an object mapping a role name to its rules")
    roles = {}
    for name, rules in data.items():
        if not isinstance(rules, dict):
            raise ValueError(f"role {name!r} must be an object")
        write_allow = rules.get("write_allow")
        roles[str(name)] = Role(
            write_allow=None if write_allow is None else _globs(write_allow,
                                                                f"{name}.write_allow"),
            read_deny=_globs(rules.get("read_deny") or [], f"{name}.read_deny"),
            deny_commands=_commands(rules.get("deny_commands") or [], f"{name}.deny_commands"),
        )
    return roles


def _glob_match(posix: PurePosixPath, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if posix.full_match(pattern) or posix.full_match(pattern.removeprefix("**/")):
            return pattern
    return None


def _rel_posix(path: Path, root: Path) -> PurePosixPath:
    try:
        path = path.relative_to(root.resolve())
    except ValueError:
        pass
    return PurePosixPath(path.as_posix().lstrip("/"))


@dataclass
class Policy:
    deny_commands: list[tuple[re.Pattern[str], str]] = field(default_factory=list)
    deny_paths: list[str] = field(default_factory=list)
    protected_branches: list[str] = field(default_factory=list)
    egress_allow: list[str] | None = None
    roles: dict[str, Role] = field(default_factory=dict)
    declared: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        egress = data.get("egress_allow")
        return cls(
            deny_commands=_commands(data.get("deny_commands") or [], "deny_commands"),
            deny_paths=[str(p) for p in data.get("deny_paths") or []],
            protected_branches=[str(b) for b in data.get("protected_branches") or []],
            egress_allow=None if egress is None else [str(h).lower() for h in egress],
            roles=_roles(data.get("roles")),
            declared=True,
        )

    @classmethod
    def load(cls, path: Path) -> Policy:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def check_path(self, path: str, root: Path) -> Decision:
        candidate = Path(path)
        if candidate.is_absolute():
            candidate = candidate.resolve()
        posix = _rel_posix(candidate, root)
        pattern = _glob_match(posix, self.deny_paths)
        if pattern is not None:
            return Decision(False, f"path {posix} matches deny_paths {pattern!r}", "deny_paths")
        return Decision(True)

    def check_command(self, command: str, root: Path) -> Decision:
        for regex, reason in self.deny_commands:
            if regex.search(command):
                return Decision(False, f"{reason} (deny_commands {regex.pattern!r})",
                                "deny_commands")
        try:
            tokens = shlex.split(command, posix=True)
        except ValueError:
            tokens = command.split()
        push = _protected_push(tokens, self.protected_branches)
        if push:
            return Decision(False, f"push to protected branch {push!r}; open a PR instead",
                            "protected_branches")
        for token in tokens:
            if token.startswith("-") or "=" in token and not token.startswith(("./", "/")):
                continue
            if "/" in token or token.startswith("."):
                decision = self.check_path(token, root)
                if not decision.allow:
                    return decision
        if self.egress_allow is not None:
            for host in _hosts(command, tokens):
                if not any(fnmatch(host, allowed) for allowed in self.egress_allow):
                    return Decision(False, f"egress to {host} not in egress_allow",
                                    "egress_allow")
        return Decision(True)


def _protected_push(tokens: list[str], protected: list[str]) -> str:
    for i, token in enumerate(tokens):
        if token != "git" or i + 1 >= len(tokens) or tokens[i + 1] != "push":
            continue
        args = [t for t in tokens[i + 2:] if not t.startswith("-")]
        for ref in args[1:]:
            target = ref.split(":", 1)[-1].removeprefix("+").removeprefix("refs/heads/")
            if any(fnmatch(target, branch) for branch in protected):
                return target
    return ""


def _hosts(command: str, tokens: list[str]) -> list[str]:
    hosts = [m.group(1).lower() for m in _URL.finditer(command)]
    hosts += [m.group(1).lower() for m in _SCP_LIKE.finditer(command)]
    for i, token in enumerate(tokens):
        if PurePosixPath(token).name in ("ssh", "telnet", "nc", "ncat") and i + 1 < len(tokens):
            target = next((t for t in tokens[i + 1:] if not t.startswith("-")), "")
            if target and "://" not in target:
                hosts.append(target.split("@")[-1].split(":")[0].lower())
    return hosts


def resolve_role(root: Path, explicit: str | None, environ: Mapping[str, str]) -> str | None:
    """`--role`, else `QR_ROLE`, else the first non-empty line of `.quality-router/role`."""
    if explicit and explicit.strip():
        return explicit.strip()
    env = (environ.get(ROLE_ENV) or "").strip()
    if env:
        return env
    path = root / ROLE_PATH
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                return line.strip()
    return None


def load_policy(root: Path, explicit: str | None) -> tuple[Policy, Path]:
    path = Path(explicit) if explicit else root / POLICY_PATH
    if not path.is_file():
        raise FileNotFoundError(f"no policy at {path}; run `qr init --policy`")
    return Policy.load(path), path


# --------------------------------------------------------------------------- #
# Host hook adapter (stdin JSON -> decision)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class HookEvent:
    kind: str
    value: str
    cwd: str = ""
    access: str = "read"


def _payload_cwd(payload: dict[str, Any]) -> str:
    roots = payload.get("workspace_roots")
    first_root = roots[0] if isinstance(roots, list) and roots else ""
    return str(payload.get("cwd") or first_root or "")


def parse_hook_event(payload: dict[str, Any]) -> HookEvent | None:
    """Normalize Claude Code PreToolUse and Cursor hook payloads."""
    if "tool_name" in payload:
        tool = str(payload.get("tool_name", ""))
        raw = payload.get("tool_input") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"command": raw}
        if not isinstance(raw, dict):
            raw = {}
        cwd = str(raw.get("working_directory") or _payload_cwd(payload))
        if tool in SHELL_TOOLS and "command" in raw:
            return HookEvent("command", str(raw["command"]), cwd)
        if tool in FILE_TOOLS:
            access = "read" if tool in READ_TOOLS else "write"
            for key in ("file_path", "path", "target_file", "notebook_path"):
                if key in raw:
                    return HookEvent("path", str(raw[key]), cwd, access)
        return None
    if "command" in payload and "mcp_server_name" not in payload:
        return HookEvent("command", str(payload["command"]), _payload_cwd(payload))
    if "file_path" in payload:
        return HookEvent("path", str(payload["file_path"]), _payload_cwd(payload))
    return None


def _absolute(value: str, cwd: Path) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else cwd / path).resolve()


def check_locked(event: HookEvent, locked: set[Path], root: Path) -> Decision:
    """Writes to approved acceptance tests/specs/lock are denied; reads stay allowed."""
    cwd = Path(event.cwd) if event.cwd else root
    reason = "approved acceptance file (qr spec lock); fix the code, not the test"
    if event.kind == "path":
        if event.access == "write" and _absolute(event.value, cwd) in locked:
            return Decision(False, f"{event.value}: {reason}", "acceptance_lock")
        return Decision(True)
    if _SPEC_LOCK_COMMAND.search(event.value):
        return Decision(False, "`qr spec lock` is the human approval step, not an agent action",
                        "acceptance_lock")
    if not _SHELL_WRITE.search(event.value):
        return Decision(True)
    try:
        tokens = shlex.split(event.value, posix=True)
    except ValueError:
        tokens = event.value.split()
    for token in tokens:
        for part in re.split(r"[<>|;&]+", token):
            if part and not part.startswith("-") and _absolute(part, cwd) in locked:
                return Decision(False, f"{part}: {reason}", "acceptance_lock")
    return Decision(True)


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _operands(command: str) -> list[str]:
    """Every non-option word, split at shell operators (for exact-path checks)."""
    return [part for token in _shell_tokens(command) for part in re.split(r"[<>|;&]+", token)
            if part and not part.startswith("-")]


def _path_words(command: str) -> list[tuple[str, bool]]:
    """Path-like words as (word, is_program); sed scripts, options and URLs are skipped."""
    words: list[tuple[str, bool]] = []
    expect_program, redirect = True, False
    for token in _shell_tokens(command):
        for piece in re.split(r"([<>|;&]+)", token):
            if not piece:
                continue
            if re.fullmatch(r"[<>|;&]+", piece):
                if "<" in piece or ">" in piece:
                    redirect = True
                else:
                    expect_program = True
                continue
            program = expect_program and not redirect
            if program and re.fullmatch(r"[A-Za-z_]\w*=.*", piece):
                continue
            expect_program = expect_program and not program and not redirect
            redirect = False
            if (piece.startswith("-") or "://" in piece or _SED_SCRIPT.match(piece)
                    or not ("/" in piece or piece.startswith((".", "~")))):
                continue
            words.append((piece, program))
    return words


def _check_harness(event: HookEvent, root: Path, cwd: Path) -> Decision:
    protected = {(root / rel).resolve() for rel in HARNESS_FILES}
    reason = "harness file; policy, role and lock change only through a reviewed commit"
    if event.kind == "path":
        if event.access == "write" and _absolute(event.value, cwd) in protected:
            return Decision(False, f"{event.value}: {reason}", "harness_file")
        return Decision(True)
    if _SHELL_WRITE.search(event.value):
        for part in _operands(event.value):
            if _absolute(part, cwd) in protected:
                return Decision(False, f"{part}: {reason}", "harness_file")
    return Decision(True)


def _check_holdout(event: HookEvent, holdout: set[Path], cwd: Path) -> Decision:
    reason = "held-out acceptance test; only the test-author role may see it"
    values = [event.value] if event.kind == "path" else _operands(event.value)
    for value in values:
        if _absolute(value, cwd) in holdout:
            return Decision(False, f"{value}: {reason}", "holdout")
    return Decision(True)


def _check_role(event: HookEvent, name: str, role: Role, root: Path, cwd: Path) -> Decision:
    if event.kind == "path":
        posix = _rel_posix(_absolute(event.value, cwd), root)
        writes = [posix] if event.access == "write" else []
        reads = [posix]
    else:
        words = _path_words(event.value)
        reads = [_rel_posix(_absolute(w, cwd), root) for w, _ in words]
        writes = ([_rel_posix(_absolute(w, cwd), root) for w, program in words if not program]
                  if _SHELL_WRITE.search(event.value) else [])
    for posix in reads:
        pattern = _glob_match(posix, role.read_deny)
        if pattern is not None:
            return Decision(False, f"role {name} may not read {posix} (read_deny {pattern!r})",
                            "role_read_deny")
    if role.write_allow is not None:
        for posix in writes:
            if _glob_match(posix, role.write_allow) is None:
                return Decision(False, f"role {name} may only write {role.write_allow}; "
                                f"{posix} is outside", "role_write_allow")
    return Decision(True)


def decide(event: HookEvent | None, policy: Policy, root: Path,
           locked: set[Path] | None = None, role: str | None = None,
           holdout: set[Path] | None = None) -> Decision:
    if event is None:
        return Decision(True)
    active = None
    if role is not None:
        active = policy.roles.get(role)
        if active is None:
            return Decision(False, f"unknown role {role!r}; declare it under roles in "
                            f"{POLICY_PATH}", "unknown_role")
    cwd = Path(event.cwd) if event.cwd else root
    if locked:
        decision = check_locked(event, locked, root)
        if not decision.allow:
            return decision
    checks = []
    if policy.declared:
        checks.append(lambda: _check_harness(event, root, cwd))
    if holdout and role != HOLDOUT_READER:
        checks.append(lambda: _check_holdout(event, holdout, cwd))
    if active is not None:
        checks.append(lambda: _check_role(event, role, active, root, cwd))
    for check in checks:
        decision = check()
        if not decision.allow:
            return decision
    if event.kind == "path":
        return policy.check_path(event.value, root)
    decision = policy.check_command(event.value, root)
    if decision.allow and active is not None:
        for regex, reason in active.deny_commands:
            if regex.search(event.value):
                return Decision(False, f"{reason} (role {role} deny_commands {regex.pattern!r})",
                                "role_deny_commands")
    return decision


def audit(path: Path, host: str, event: HookEvent | None, decision: Decision) -> None:
    record = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "host": host,
        "kind": event.kind if event else "other",
        "value": event.value if event else "",
        "allow": decision.allow,
        "rule": decision.rule,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def hook_response(host: str, decision: Decision) -> tuple[int, str, str]:
    """(exit code, stdout, stderr) in the host's protocol."""
    if host == "cursor":
        body: dict[str, str] = {"permission": "allow" if decision.allow else "deny"}
        if not decision.allow:
            body["user_message"] = f"qr policy: {decision.reason}"
            body["agent_message"] = f"Blocked by .quality-router/policy.json: {decision.reason}"
        return 0, json.dumps(body) + "\n", ""
    if decision.allow:
        return 0, "", ""
    return 2, "", f"Blocked by .quality-router/policy.json: {decision.reason}\n"


# --------------------------------------------------------------------------- #
# Host wiring stamps (idempotent JSON merge; never mcp.json)
# --------------------------------------------------------------------------- #

CURSOR_HOOK_COMMAND = "qr policy hook --host cursor"
CLAUDE_HOOK_COMMAND = "qr policy hook --host claude-code"


def stamp_policy(root: Path) -> bool:
    path = root / POLICY_PATH
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_POLICY, indent=2) + "\n", encoding="utf-8")
    return True


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object; refusing to merge")
    return data


def stamp_cursor_hooks(root: Path) -> bool:
    path = root / ".cursor" / "hooks.json"
    data = _read_json(path)
    data.setdefault("version", 1)
    hooks = data.setdefault("hooks", {})
    wanted = {
        "beforeShellExecution": {"command": CURSOR_HOOK_COMMAND, "failClosed": True},
        "beforeReadFile": {"command": CURSOR_HOOK_COMMAND, "failClosed": True},
        "preToolUse": {"command": CURSOR_HOOK_COMMAND, "matcher": "Write|Delete",
                       "failClosed": True},
    }
    changed = False
    for event, entry in wanted.items():
        entries = hooks.setdefault(event, [])
        if not any(isinstance(e, dict) and e.get("command") == CURSOR_HOOK_COMMAND
                   for e in entries):
            entries.append(entry)
            changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def stamp_claude_hooks(root: Path) -> bool:
    path = root / ".claude" / "settings.json"
    data = _read_json(path)
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for group in pre:
        for hook in group.get("hooks", []) if isinstance(group, dict) else []:
            if hook.get("command") == CLAUDE_HOOK_COMMAND:
                return False
    pre.append({
        "matcher": "Bash|Read|Edit|MultiEdit|Write|NotebookEdit",
        "hooks": [{"type": "command", "command": CLAUDE_HOOK_COMMAND}],
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


HOST_HOOK_STAMPS = {"cursor": stamp_cursor_hooks, "claude-code": stamp_claude_hooks}

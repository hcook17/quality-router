"""Portable agent policy: one JSON file, enforced through host hooks by a deterministic CLI.

Evidence: 2608.23550 (only ~4.4% of CLAUDE.md security rules have an
enforcing control: prose is "write-only"), 2609.22259 (declared forbidden
operations stopped all mutating SQL), 2609.08149 (code-host egress blocking
closes leakage), 2609.09798 (classifier guardrails get bypassed -> decide
deterministically). The LLM proposes; `qr policy` allows or denies.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Any

POLICY_PATH = ".quality-router/policy.json"

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
}

SHELL_TOOLS = ("Bash", "Shell", "run_terminal_cmd", "shell")
FILE_TOOLS = ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Delete", "read_file",
              "edit_file", "delete_file")
_URL = re.compile(r"\b(?:https?|ftp|ssh|git)://(?:[^@/\s]+@)?([A-Za-z0-9.-]+)")
_SCP_LIKE = re.compile(r"(?:^|\s)[\w.-]+@([A-Za-z0-9.-]+):")
_NETWORK_TOOLS = ("curl", "wget", "nc", "ncat", "scp", "rsync", "ssh", "ftp", "telnet")


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str = ""
    rule: str = ""


@dataclass
class Policy:
    deny_commands: list[tuple[re.Pattern[str], str]] = field(default_factory=list)
    deny_paths: list[str] = field(default_factory=list)
    protected_branches: list[str] = field(default_factory=list)
    egress_allow: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        commands = []
        for item in data.get("deny_commands") or []:
            pattern, reason = ((item, "denied by policy") if isinstance(item, str)
                               else (item["pattern"], item.get("reason", "denied by policy")))
            commands.append((re.compile(pattern, re.IGNORECASE), reason))
        egress = data.get("egress_allow")
        return cls(
            deny_commands=commands,
            deny_paths=[str(p) for p in data.get("deny_paths") or []],
            protected_branches=[str(b) for b in data.get("protected_branches") or []],
            egress_allow=None if egress is None else [str(h).lower() for h in egress],
        )

    @classmethod
    def load(cls, path: Path) -> Policy:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def check_path(self, path: str, root: Path) -> Decision:
        candidate = Path(path)
        if candidate.is_absolute():
            try:
                candidate = candidate.resolve().relative_to(root.resolve())
            except ValueError:
                pass
        posix = PurePosixPath(candidate.as_posix().lstrip("/"))
        for pattern in self.deny_paths:
            bare = pattern.removeprefix("**/")
            if posix.full_match(pattern) or posix.full_match(bare):
                return Decision(False, f"path {posix} matches deny_paths {pattern!r}",
                                "deny_paths")
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
            for key in ("file_path", "path", "target_file", "notebook_path"):
                if key in raw:
                    return HookEvent("path", str(raw[key]), cwd)
        return None
    if "command" in payload and "mcp_server_name" not in payload:
        return HookEvent("command", str(payload["command"]), _payload_cwd(payload))
    if "file_path" in payload:
        return HookEvent("path", str(payload["file_path"]), _payload_cwd(payload))
    return None


def decide(event: HookEvent | None, policy: Policy, root: Path) -> Decision:
    if event is None:
        return Decision(True)
    if event.kind == "command":
        return policy.check_command(event.value, root)
    return policy.check_path(event.value, root)


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

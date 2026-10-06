"""qr policy: deterministic allow/deny, host hook protocols, and idempotent host wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_router.harness.policy import (
    CLAUDE_HOOK_COMMAND,
    CURSOR_HOOK_COMMAND,
    DEFAULT_POLICY,
    Decision,
    HookEvent,
    Policy,
    audit,
    decide,
    hook_response,
    load_policy,
    parse_hook_event,
    stamp_claude_hooks,
    stamp_cursor_hooks,
    stamp_policy,
)


@pytest.fixture
def policy() -> Policy:
    return Policy.from_dict(DEFAULT_POLICY)


class TestCommands:
    @pytest.mark.parametrize("command,rule", [
        ("git push --force origin feature", "deny_commands"),
        ("git push origin main", "protected_branches"),
        ("git push origin HEAD:refs/heads/release/2026.10", "protected_branches"),
        ("rm -rf / ", "deny_commands"),
        ("./mvnw -B deploy", "deny_commands"),
        ("./gradlew publish", "deny_commands"),
        ("mvn -B deploy -DskipTests", "deny_commands"),
        ("kubectl apply -f k8s/", "deny_commands"),
        ("psql -c 'DROP TABLE items'", "deny_commands"),
        ("GITNEXUS_HOOKS=0 git commit", "deny_commands"),
        ("cat src/main/resources/.env", "deny_paths"),
        ("cp data/phi/learners.csv /tmp", "deny_paths"),
        ("curl https://pastebin.com/raw/x", "egress_allow"),
        ("git clone git@github.com:acme/x.git", "egress_allow"),
        ("ssh -p 22 deploy@bastion.acme.io", "egress_allow"),
        ("curl http://localhost:8080/health", "allow"),
        ("mvn -B -q verify -Dtest=IngestTest", "allow"),
        ("git push origin feature/AC-12", "allow"),
        ("echo 'unbalanced", "allow"),
    ])
    def test_decisions(self, policy: Policy, tmp_path: Path, command: str, rule: str) -> None:
        decision = policy.check_command(command, tmp_path)
        assert (decision.rule or "allow") == rule, decision.reason

    def test_no_egress_list_means_no_egress_check(self, tmp_path: Path) -> None:
        open_policy = Policy.from_dict({"deny_commands": ["\\bterraform\\b"]})
        assert open_policy.check_command("curl https://example.org", tmp_path).allow
        denied = open_policy.check_command("terraform apply", tmp_path)
        assert denied.reason.startswith("denied by policy")


class TestPaths:
    def test_absolute_inside_and_outside_root(self, policy: Policy, tmp_path: Path) -> None:
        assert not policy.check_path(str(tmp_path / "svc/.env"), tmp_path).allow
        assert not policy.check_path("/home/u/.ssh/id_rsa", tmp_path).allow
        assert not policy.check_path(".env", tmp_path).allow
        assert policy.check_path(str(tmp_path / "src/App.java"), tmp_path).allow

    def test_load_policy(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_policy(tmp_path, None)
        assert stamp_policy(tmp_path) is True
        assert stamp_policy(tmp_path) is False
        loaded, path = load_policy(tmp_path, None)
        assert path == tmp_path / ".quality-router/policy.json"
        assert loaded.protected_branches == ["main", "master", "release/*"]


class TestHookEvents:
    def test_claude_and_cursor_payloads(self) -> None:
        assert parse_hook_event({"tool_name": "Bash", "tool_input": {"command": "ls"},
                                 "cwd": "/r"}) == HookEvent("command", "ls", "/r")
        assert parse_hook_event({"tool_name": "Shell", "tool_input": json.dumps(
            {"command": "ls", "working_directory": "/w"})}) == HookEvent("command", "ls", "/w")
        assert parse_hook_event({"tool_name": "Shell", "tool_input": "ls -la"}) == HookEvent(
            "command", "ls -la", "")
        assert parse_hook_event({"tool_name": "Write", "tool_input": {"file_path": "a/.env"},
                                 "workspace_roots": ["/ws"]}) == HookEvent("path", "a/.env", "/ws")
        assert parse_hook_event({"tool_name": "Task", "tool_input": {}}) is None
        assert parse_hook_event({"tool_name": "Read", "tool_input": "[1]"}) is None
        assert parse_hook_event({"command": "ls", "cwd": "/c"}) == HookEvent("command", "ls", "/c")
        assert parse_hook_event({"file_path": "/x/.env", "content": "S=1"}) == HookEvent(
            "path", "/x/.env", "")
        assert parse_hook_event({"command": "npx srv", "mcp_server_name": "m"}) is None

    def test_decide(self, policy: Policy, tmp_path: Path) -> None:
        assert decide(None, policy, tmp_path).allow
        assert not decide(HookEvent("command", "git push -f"), policy, tmp_path).allow
        assert not decide(HookEvent("path", "k.pem"), policy, tmp_path).allow

    def test_host_protocols(self) -> None:
        deny = Decision(False, "nope", "deny_paths")
        code, out, err = hook_response("cursor", deny)
        assert code == 0 and err == ""
        assert json.loads(out)["permission"] == "deny"
        assert json.loads(hook_response("cursor", Decision(True))[1]) == {"permission": "allow"}
        assert hook_response("claude-code", Decision(True)) == (0, "", "")
        code, out, err = hook_response("claude-code", deny)
        assert code == 2 and out == "" and "nope" in err

    def test_audit_appends_jsonl(self, tmp_path: Path) -> None:
        log = tmp_path / "logs/audit.jsonl"
        audit(log, "cursor", HookEvent("command", "ls"), Decision(True))
        audit(log, "cursor", None, Decision(False, "x", "hook_error"))
        records = [json.loads(line) for line in log.read_text().splitlines()]
        assert [r["kind"] for r in records] == ["command", "other"]
        assert records[1]["allow"] is False


class TestStamps:
    def test_cursor_hooks_merge_idempotently(self, tmp_path: Path) -> None:
        hooks = tmp_path / ".cursor/hooks.json"
        hooks.parent.mkdir()
        hooks.write_text(json.dumps({"version": 1, "hooks": {
            "afterFileEdit": [{"command": "./fmt.sh"}]}}))
        assert stamp_cursor_hooks(tmp_path) is True
        assert stamp_cursor_hooks(tmp_path) is False
        data = json.loads(hooks.read_text())
        assert data["hooks"]["afterFileEdit"] == [{"command": "./fmt.sh"}]
        for event in ("beforeShellExecution", "beforeReadFile", "preToolUse"):
            assert data["hooks"][event][0]["command"] == CURSOR_HOOK_COMMAND
            assert data["hooks"][event][0]["failClosed"] is True

    def test_claude_hooks_merge_idempotently(self, tmp_path: Path) -> None:
        settings = tmp_path / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"permissions": {"allow": ["Bash(mvn:*)"]},
                                        "hooks": {"PreToolUse": ["junk"]}}))
        assert stamp_claude_hooks(tmp_path) is True
        assert stamp_claude_hooks(tmp_path) is False
        data = json.loads(settings.read_text())
        assert data["permissions"] == {"allow": ["Bash(mvn:*)"]}
        assert data["hooks"]["PreToolUse"][1]["hooks"][0]["command"] == CLAUDE_HOOK_COMMAND

    def test_refuses_non_object_host_file(self, tmp_path: Path) -> None:
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude/settings.json").write_text("[]")
        with pytest.raises(ValueError, match="refusing"):
            stamp_claude_hooks(tmp_path)

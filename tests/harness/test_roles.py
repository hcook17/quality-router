"""Phase 7 roles (specs/phase-7-roles-holdout.md AC-7.1..AC-7.7): `roles` in policy.json, the
active role, role write/read/command limits, write-protected harness files, and the default roles
that `qr init --policy` stamps."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from quality_router.cli import run
from quality_router.harness.policy import Decision, HookEvent, Policy, decide
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE

ROLES: dict[str, Any] = {
    "test-author": {"write_allow": ["**/src/test/**", "specs/**"], "read_deny": []},
    "implementer": {"read_deny": ["holdout/**"]},
    "reviewer": {"write_allow": [], "deny_commands": [r"\bgit\s+commit\b"]},
}
VISIBLE = "src/test/java/ATest.java"
MAIN = "src/main/java/A.java"
HOLDOUT = "holdout/ItemHoldoutTest.java"
POLICY_FILE = ".quality-router/policy.json"
ROLE_FILE = ".quality-router/role"
LOCK_FILE = ".quality-router/acceptance.lock.json"


@pytest.fixture(autouse=True)
def no_role_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QR_ROLE", raising=False)


def write_policy(root: Path, roles: Any = ROLES) -> Path:
    """Policy file under `root`; `roles=None` leaves the key out."""
    data: dict[str, Any] = {"version": 1, "deny_paths": ["**/.env"]}
    if roles is not None:
        data["roles"] = roles
    path = root / POLICY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Checkout (also the cwd) whose policy declares the spec's example roles."""
    work = tmp_path / "svc"
    work.mkdir()
    write_policy(work)
    monkeypatch.chdir(work)
    return work


def decide_as(root: Path, role: str | None, kind: str, value: str,
              access: str = "read") -> Decision:
    policy = Policy.load(root / POLICY_FILE)
    return decide(HookEvent(kind, value, str(root), access), policy, root, role=role)


def assert_decision(decision: Decision, expected: str) -> None:
    """`expected` is `allow`, `deny` (any rule) or `deny <rule>`."""
    if expected == "allow":
        assert decision.allow, decision
        return
    assert not decision.allow, decision
    if expected != "deny":
        assert decision.rule == expected.removeprefix("deny "), decision


def event_argv(kind: str, value: str, access: str) -> list[str]:
    if kind == "command":
        return ["--command", value]
    return ["--path", value, *(["--write"] if access == "write" else [])]


def check(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = run(["policy", "check", *argv, "--json"])
    return code, json.loads(capsys.readouterr().out)


def denied(payload: dict[str, Any]) -> list[str]:
    return [f["code"] for f in payload["findings"] if f["level"] == "error"]


def assert_check(capsys: pytest.CaptureFixture[str], expected: str, *argv: str) -> None:
    code, payload = check(capsys, *argv)
    if expected == "allow":
        assert (code, denied(payload)) == (EXIT_PASS, []), payload
    elif expected == "deny":
        assert code == EXIT_FAIL and len(denied(payload)) == 1, payload
    else:
        rule = expected.removeprefix("deny ")
        assert (code, denied(payload)) == (EXIT_FAIL, [f"denied_{rule}"]), payload


def hook(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any], host: str = "claude-code",
         *extra: str) -> int:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    return run(["policy", "hook", "--host", host, *extra])


def claude(root: Path, tool: str, **tool_input: str) -> dict[str, Any]:
    return {"tool_name": tool, "tool_input": tool_input, "cwd": str(root)}


def audited_rule(audit: Path) -> str:
    return json.loads(audit.read_text().splitlines()[-1])["rule"]


class TestRolesDeclared:
    """AC-7.1 Roles are declared in policy.json: `roles` is optional; a malformed value fails
    closed."""

    def test_roles_load_into_policy(self) -> None:
        policy = Policy.from_dict({"roles": {
            "reviewer": {"write_allow": []},
            "implementer": {"read_deny": ["holdout/**"]},
            "test-author": {"write_allow": ["**/src/test/**"],
                            "deny_commands": [r"\bgit\s+push\b"]},
        }})
        assert set(policy.roles) == {"reviewer", "implementer", "test-author"}
        assert policy.roles["reviewer"].write_allow == []
        assert policy.roles["reviewer"].read_deny == []
        assert policy.roles["implementer"].write_allow is None
        assert policy.roles["implementer"].read_deny == ["holdout/**"]
        assert policy.roles["test-author"].write_allow == ["**/src/test/**"]

    def test_roles_absent(self) -> None:
        assert not Policy.from_dict({"deny_paths": ["**/.env"]}).roles

    @pytest.mark.parametrize("roles,argv,code", [
        (None, ["--path", MAIN], EXIT_PASS),
        ({"reviewer": {"write_allow": []}}, ["--path", "README.md"], EXIT_PASS),
        (["reviewer"], ["--path", "README.md"], EXIT_USAGE),
        ({"reviewer": "x"}, ["--path", "README.md"], EXIT_USAGE),
        ({"r": {"deny_commands": ["("]}}, ["--path", "README.md"], EXIT_USAGE),
    ], ids=["absent", "reviewer-write-nothing", "list", "role-not-object", "bad-regex"])
    def test_policy_check_exit(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                               roles: Any, argv: list[str], code: int) -> None:
        write_policy(tmp_path, roles)
        monkeypatch.chdir(tmp_path)
        assert run(["policy", "check", *argv]) == code

    @pytest.mark.parametrize("roles", [
        ["reviewer"], {"reviewer": "x"}, {"r": {"deny_commands": ["("]}},
    ], ids=["list", "role-not-object", "bad-regex"])
    def test_policy_hook_denies(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                capsys: pytest.CaptureFixture[str], roles: Any) -> None:
        write_policy(tmp_path, roles)
        monkeypatch.chdir(tmp_path)
        assert hook(monkeypatch, claude(tmp_path, "Read", file_path="README.md")) == 2
        capsys.readouterr()
        assert hook(monkeypatch, {"command": "ls", "cwd": str(tmp_path)}, "cursor") == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"


RESOLUTION = [
    ("test-author", "implementer", "reviewer", "test-author"),
    (None, "implementer", "reviewer", "implementer"),
    (None, None, "reviewer", "reviewer"),
    (None, None, None, None),
]


class TestActiveRole:
    """AC-7.2 The active role comes from --role, then QR_ROLE, then the first non-empty line of
    .quality-router/role, else none; an unknown role is denied with `unknown_role`."""

    @pytest.mark.parametrize("flag,env,role_file,active",
                             [*RESOLUTION, ("ghost", None, None, "ghost")])
    def test_resolve_role(self, root: Path, flag: str | None, env: str | None,
                          role_file: str | None, active: str | None) -> None:
        from quality_router.harness.policy import resolve_role

        if role_file is not None:
            (root / ROLE_FILE).write_text(role_file + "\n")
        environ = {"QR_ROLE": env} if env else {}
        assert resolve_role(root, flag, environ) == active

    def test_role_file_first_non_empty_line(self, root: Path) -> None:
        from quality_router.harness.policy import resolve_role

        (root / ROLE_FILE).write_text("\n\nreviewer\nimplementer\n")
        assert resolve_role(root, None, {}) == "reviewer"

    @pytest.mark.parametrize("flag,env,role_file,active", RESOLUTION)
    def test_policy_check_reports_role(self, root: Path, monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str], flag: str | None,
                                       env: str | None, role_file: str | None,
                                       active: str | None) -> None:
        if env:
            monkeypatch.setenv("QR_ROLE", env)
        if role_file:
            (root / ROLE_FILE).write_text(role_file + "\n")
        code, payload = check(capsys, "--path", "README.md", *(["--role", flag] if flag else []))
        assert code == EXIT_PASS
        assert payload["summary"]["role"] == (active or "")

    def test_unknown_role_denied(self, root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert_check(capsys, "deny unknown_role", "--role", "ghost", "--path", "README.md")
        assert_decision(decide_as(root, "ghost", "command", "ls"), "deny unknown_role")
        assert_decision(decide_as(root, "ghost", "path", "README.md"), "deny unknown_role")

    @pytest.mark.parametrize("kind,value,access,expected", [
        ("path", MAIN, "write", "allow"),
        ("path", HOLDOUT, "read", "allow"),
        ("command", "git commit -m x", "read", "allow"),
        ("command", f"cp x.java {MAIN}", "read", "allow"),
        ("path", "config/.env", "read", "deny deny_paths"),
    ])
    def test_no_role_decides_as_before(self, root: Path, kind: str, value: str, access: str,
                                       expected: str) -> None:
        event = HookEvent(kind, value, str(root), access)
        policy = Policy.load(root / POLICY_FILE)
        assert_decision(decide(event, policy, root), expected)
        assert_decision(decide(event, policy, root, role=None), expected)

    def test_hook_takes_flag_then_env_then_file(self, root: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
        write = claude(root, "Write", file_path=MAIN)
        assert hook(monkeypatch, write) == EXIT_PASS
        (root / ROLE_FILE).write_text("reviewer\n")
        assert hook(monkeypatch, write) == 2
        monkeypatch.setenv("QR_ROLE", "implementer")
        assert hook(monkeypatch, write) == EXIT_PASS
        assert hook(monkeypatch, write, "claude-code", "--role", "test-author") == 2

    def test_hook_unknown_role(self, root: Path, monkeypatch: pytest.MonkeyPatch,
                               tmp_path: Path) -> None:
        audit = tmp_path / "audit.jsonl"
        read = claude(root, "Read", file_path="README.md")
        assert hook(monkeypatch, read, "claude-code", "--role", "ghost",
                    "--audit", str(audit)) == 2
        assert audited_rule(audit) == "unknown_role"


WRITE_ALLOW = [
    ("test-author", "path", VISIBLE, "write", "allow"),
    ("test-author", "path", MAIN, "write", "deny role_write_allow"),
    ("test-author", "path", MAIN, "read", "allow"),
    ("test-author", "command", f"cp x.java {MAIN}", "read", "deny role_write_allow"),
    ("reviewer", "path", "README.md", "write", "deny role_write_allow"),
    ("implementer", "path", MAIN, "write", "allow"),
]


class TestWriteAllow:
    """AC-7.3 `write_allow` limits where a role may write (file tools and shell writes); reads
    are not limited."""

    @pytest.mark.parametrize("role,kind,value,access,expected", WRITE_ALLOW)
    def test_decide(self, root: Path, role: str, kind: str, value: str, access: str,
                    expected: str) -> None:
        assert_decision(decide_as(root, role, kind, value, access), expected)

    @pytest.mark.parametrize("role,kind,value,access,expected", WRITE_ALLOW)
    def test_policy_check(self, root: Path, capsys: pytest.CaptureFixture[str], role: str,
                          kind: str, value: str, access: str, expected: str) -> None:
        assert_check(capsys, expected, "--role", role, *event_argv(kind, value, access))

    def test_hook(self, root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("QR_ROLE", "test-author")
        audit = tmp_path / "audit.jsonl"
        assert hook(monkeypatch, claude(root, "Write", file_path=VISIBLE)) == EXIT_PASS
        assert hook(monkeypatch, claude(root, "Read", file_path=MAIN)) == EXIT_PASS
        assert hook(monkeypatch, claude(root, "Write", file_path=MAIN), "claude-code",
                    "--audit", str(audit)) == 2
        assert audited_rule(audit) == "role_write_allow"
        assert hook(monkeypatch, claude(root, "Bash", command=f"cp x.java {MAIN}"),
                    "claude-code", "--audit", str(audit)) == 2
        assert audited_rule(audit) == "role_write_allow"


READ_DENY = [
    ("implementer", "path", HOLDOUT, "read", "deny role_read_deny"),
    ("implementer", "command", f"cat {HOLDOUT}", "read", "deny role_read_deny"),
    ("implementer", "path", VISIBLE, "read", "allow"),
    ("test-author", "path", HOLDOUT, "read", "allow"),
]


class TestReadDeny:
    """AC-7.4 `read_deny` hides paths from a role, for file tools and shell commands."""

    @pytest.mark.parametrize("role,kind,value,access,expected", READ_DENY)
    def test_decide(self, root: Path, role: str, kind: str, value: str, access: str,
                    expected: str) -> None:
        assert_decision(decide_as(root, role, kind, value, access), expected)

    @pytest.mark.parametrize("role,kind,value,access,expected", READ_DENY)
    def test_policy_check(self, root: Path, capsys: pytest.CaptureFixture[str], role: str,
                          kind: str, value: str, access: str, expected: str) -> None:
        assert_check(capsys, expected, "--role", role, *event_argv(kind, value, access))

    def test_hook(self, root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        audit = tmp_path / "audit.jsonl"
        monkeypatch.setenv("QR_ROLE", "implementer")
        assert hook(monkeypatch, claude(root, "Read", file_path=HOLDOUT), "claude-code",
                    "--audit", str(audit)) == 2
        assert audited_rule(audit) == "role_read_deny"
        assert hook(monkeypatch, claude(root, "Read", file_path=VISIBLE)) == EXIT_PASS
        monkeypatch.setenv("QR_ROLE", "test-author")
        assert hook(monkeypatch, claude(root, "Read", file_path=HOLDOUT)) == EXIT_PASS


ROLE_COMMANDS = [
    ("reviewer", "git commit -m x", "deny role_deny_commands"),
    ("implementer", "git commit -m x", "allow"),
    ("reviewer", "git log -1", "allow"),
]


class TestRoleCommands:
    """AC-7.5 Roles add command rules: a role's `deny_commands` apply after the top-level ones."""

    @pytest.mark.parametrize("role,command,expected", ROLE_COMMANDS)
    def test_decide(self, root: Path, role: str, command: str, expected: str) -> None:
        assert_decision(decide_as(root, role, "command", command), expected)

    @pytest.mark.parametrize("role,command,expected", ROLE_COMMANDS)
    def test_policy_check(self, root: Path, capsys: pytest.CaptureFixture[str], role: str,
                          command: str, expected: str) -> None:
        assert_check(capsys, expected, "--role", role, "--command", command)

    def test_hook(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QR_ROLE", "reviewer")
        assert hook(monkeypatch, claude(root, "Bash", command="git commit -m x")) == 2
        assert hook(monkeypatch, claude(root, "Bash", command="git log -1")) == EXIT_PASS


HARNESS = [
    (None, "path", POLICY_FILE, "write", "deny harness_file"),
    ("implementer", "command", f"echo reviewer > {ROLE_FILE}", "read", "deny harness_file"),
    ("test-author", "path", LOCK_FILE, "write", "deny"),
    (None, "path", POLICY_FILE, "read", "allow"),
]


class TestHarnessFiles:
    """AC-7.6 The harness's own files (policy, role file, lock) are write-protected for every
    role and with no role; reads are allowed."""

    @pytest.mark.parametrize("role,kind,value,access,expected", HARNESS)
    def test_decide(self, root: Path, role: str | None, kind: str, value: str, access: str,
                    expected: str) -> None:
        assert_decision(decide_as(root, role, kind, value, access), expected)

    @pytest.mark.parametrize("role,kind,value,access,expected", HARNESS)
    def test_policy_check(self, root: Path, capsys: pytest.CaptureFixture[str],
                          role: str | None, kind: str, value: str, access: str,
                          expected: str) -> None:
        role_argv = ["--role", role] if role else []
        assert_check(capsys, expected, *role_argv, *event_argv(kind, value, access))

    def test_hook(self, root: Path, monkeypatch: pytest.MonkeyPatch,
                  capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        audit = tmp_path / "audit.jsonl"
        assert hook(monkeypatch, claude(root, "Write", file_path=ROLE_FILE), "claude-code",
                    "--audit", str(audit)) == 2
        assert audited_rule(audit) == "harness_file"
        assert hook(monkeypatch, claude(root, "Read", file_path=POLICY_FILE)) == EXIT_PASS
        monkeypatch.setenv("QR_ROLE", "implementer")
        cursor_write = {"tool_name": "Write", "tool_input": {"file_path": POLICY_FILE},
                        "workspace_roots": [str(root)]}
        capsys.readouterr()
        assert hook(monkeypatch, cursor_write, "cursor") == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"


class TestDefaultRoles:
    """AC-7.7 A new policy stamped by `qr init --policy` declares four default roles; an
    existing policy is not changed."""

    @pytest.fixture
    def stamped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        monkeypatch.chdir(tmp_path)
        assert run(["init", "--policy"]) == 0
        return tmp_path

    def test_roles_written(self, stamped: Path) -> None:
        roles = json.loads((stamped / POLICY_FILE).read_text())["roles"]
        assert set(roles) == {"spec-author", "test-author", "implementer", "reviewer"}
        assert sorted(roles["spec-author"]["write_allow"]) == sorted(
            ["specs/**", "docs/**", "**/*.md"])
        assert sorted(roles["test-author"]["write_allow"]) == sorted(
            ["**/src/test/**", "**/src/testFixtures/**", "**/src/*Test/**", "**/src/it/**",
             "specs/**"])
        assert "write_allow" not in roles["implementer"]
        assert roles["reviewer"]["write_allow"] == []

    @pytest.mark.parametrize("role,path,code", [
        ("spec-author", "specs/item-v2.md", EXIT_PASS),
        ("spec-author", MAIN, EXIT_FAIL),
        ("test-author", "src/integrationTest/java/AIT.java", EXIT_PASS),
        ("implementer", MAIN, EXIT_PASS),
        ("reviewer", "specs/item-v2.md", EXIT_FAIL),
    ])
    def test_decisions(self, stamped: Path, role: str, path: str, code: int) -> None:
        assert run(["policy", "check", "--role", role, "--write", "--path", path]) == code

    def test_existing_policy_unchanged(self, tmp_path: Path,
                                       monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        policy = write_policy(tmp_path, None)
        before = policy.read_bytes()
        assert run(["init", "--policy"]) == 0
        assert policy.read_bytes() == before

"""Held-out checks for phase 7 roles (specs/phase-7-roles-holdout.md AC-1..AC-7).

Self-contained: pytest, the stdlib and quality_router only.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from quality_router.cli import run

TOP: dict[str, Any] = {
    "version": 1,
    "deny_commands": [{"pattern": r"\bgit\s+push\b.*\s--force\b", "reason": "no force push"}],
    "deny_paths": ["**/.env"],
}
ROLES: dict[str, Any] = {
    "test-author": {"write_allow": ["**/src/test/**", "**/src/testFixtures/**", "specs/**"]},
    "implementer": {"read_deny": ["**/secret-tests/**", "qa/hidden/**"]},
    "reviewer": {"write_allow": [], "deny_commands": [
        {"pattern": r"\bgit\s+(commit|merge)\b", "reason": "reviewers comment; they do not commit"},
        r"\bgit\s+push\b",
    ]},
    "docs": {"write_allow": ["**/*.md", "docs/**"]},
    "ops": {"write_allow": [".quality-router/**", "ops/**"]},
}
MAIN = "src/main/java/com/acme/Item.java"
TEST = "src/test/java/com/acme/ItemTest.java"
HIDDEN = "qa/hidden/ItemHiddenTest.java"
POLICY_FILE = ".quality-router/policy.json"
ROLE_FILE = ".quality-router/role"
LOCK_FILE = ".quality-router/acceptance.lock.json"
EXIT_PASS, EXIT_FAIL, EXIT_USAGE = 0, 1, 2


@pytest.fixture(autouse=True)
def _clear_role_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QR_ROLE", raising=False)


def _policy_data(roles: Any = ROLES) -> dict[str, Any]:
    data = dict(TOP)
    if roles is not None:
        data["roles"] = roles
    return data


def _write_policy(root: Path, roles: Any = ROLES) -> Path:
    path = root / POLICY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_policy_data(roles), indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def ws(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = (tmp_path / "work").resolve()
    root.mkdir()
    _write_policy(root)
    monkeypatch.chdir(root)
    return root


def _decide(root: Path, role: str | None, kind: str, value: str, access: str = "read"):
    from quality_router.harness.policy import HookEvent, Policy, decide

    policy = Policy.load(root / POLICY_FILE)
    return decide(HookEvent(kind, value, str(root), access), policy, root, role=role)


def _expect(decision: Any, expected: str) -> None:
    if expected == "allow":
        assert decision.allow, decision
    elif expected == "deny":
        assert not decision.allow, decision
    else:
        assert not decision.allow, decision
        assert decision.rule == expected, decision


def _check_json(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = run(["policy", "check", *argv, "--json"])
    return code, json.loads(capsys.readouterr().out)


def _errors(payload: dict[str, Any]) -> list[str]:
    return [f["code"] for f in payload["findings"] if f["level"] == "error"]


def _hook(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any], host: str,
          *extra: str) -> int:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    return run(["policy", "hook", "--host", host, *extra])


def _cursor_permission(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
                       payload: dict[str, Any], *extra: str) -> str:
    capsys.readouterr()
    assert _hook(monkeypatch, payload, "cursor", *extra) == 0
    return json.loads(capsys.readouterr().out)["permission"]


def _claude_rule(monkeypatch: pytest.MonkeyPatch, audit: Path, payload: dict[str, Any],
                 *extra: str) -> tuple[int, str]:
    code = _hook(monkeypatch, payload, "claude-code", "--audit", str(audit), *extra)
    return code, json.loads(audit.read_text().splitlines()[-1])["rule"]


def _claude(root: Path, tool: str, **tool_input: str) -> dict[str, Any]:
    return {"tool_name": tool, "tool_input": tool_input, "cwd": str(root)}


def _cursor_write(root: Path, path: str) -> dict[str, Any]:
    return {"tool_name": "Write", "tool_input": {"file_path": path},
            "workspace_roots": [str(root)]}


def _cursor_read(root: Path, path: str) -> dict[str, Any]:
    return {"file_path": path, "content": "", "workspace_roots": [str(root)]}


def _cursor_shell(root: Path, command: str) -> dict[str, Any]:
    return {"command": command, "cwd": str(root)}


# --------------------------------------------------------------------------- #
# AC-1
# --------------------------------------------------------------------------- #

def test_ac1_roles_parse_with_dict_and_string_command_forms() -> None:
    """AC-1: roles map names to objects; missing write_allow is None, missing read_deny is
    empty, deny_commands accepts the top-level shapes (strings and pattern/reason objects)."""
    from quality_router.harness.policy import Policy

    policy = Policy.from_dict(_policy_data())
    assert set(policy.roles) == set(ROLES)
    assert policy.roles["reviewer"].write_allow == []
    assert policy.roles["implementer"].write_allow is None
    assert policy.roles["implementer"].read_deny == ["**/secret-tests/**", "qa/hidden/**"]
    assert policy.roles["docs"].read_deny == []
    assert policy.roles["ops"].write_allow == [".quality-router/**", "ops/**"]


def test_ac1_empty_roles_object_is_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    """AC-1: an empty roles object is well formed; naming a role it lacks is unknown_role."""
    _write_policy(tmp_path, {})
    monkeypatch.chdir(tmp_path)
    assert run(["policy", "check", "--path", "README.md"]) == EXIT_PASS
    code, payload = _check_json(capsys, "--role", "reviewer", "--path", "README.md")
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_unknown_role"])


MALFORMED = [
    "reviewer",
    {"reviewer": ["write_allow"]},
    {"r": {"deny_commands": [{"pattern": "(", "reason": "x"}]}},
    {"ok": {"write_allow": []}, "r": {"deny_commands": [r"\bok\b", "[unclosed"]}},
]
MALFORMED_IDS = ["string", "role-is-list", "dict-form-bad-regex", "second-role-bad-regex"]


@pytest.mark.parametrize("roles", MALFORMED, ids=MALFORMED_IDS)
def test_ac1_malformed_roles_policy_check_exits_2(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch,
                                                  roles: Any) -> None:
    """AC-1: a malformed roles value makes `qr policy check` exit 2, with or without a role."""
    _write_policy(tmp_path, roles)
    monkeypatch.chdir(tmp_path)
    assert run(["policy", "check", "--command", "ls"]) == EXIT_USAGE
    monkeypatch.setenv("QR_ROLE", "ok")
    assert run(["policy", "check", "--path", "README.md"]) == EXIT_USAGE


@pytest.mark.parametrize("roles", MALFORMED, ids=MALFORMED_IDS)
def test_ac1_malformed_roles_hook_denies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str], roles: Any) -> None:
    """AC-1: a malformed roles value makes `qr policy hook` deny (Claude Code and Cursor)."""
    _write_policy(tmp_path, roles)
    monkeypatch.chdir(tmp_path)
    assert _hook(monkeypatch, _claude(tmp_path, "Bash", command="ls"), "claude-code") == 2
    assert _cursor_permission(monkeypatch, capsys, _cursor_shell(tmp_path, "ls")) == "deny"
    assert _cursor_permission(monkeypatch, capsys,
                              _cursor_write(tmp_path, "notes/a.txt")) == "deny"


# --------------------------------------------------------------------------- #
# AC-2
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("explicit,environ,role_file,active", [
    ("reviewer", {"QR_ROLE": "docs"}, "implementer\n", "reviewer"),
    (None, {"QR_ROLE": "docs"}, "implementer\n", "docs"),
    (None, {}, "implementer\n", "implementer"),
    (None, {"OTHER": "x"}, None, None),
    (None, {}, "\n  \n\t\n  reviewer  \nimplementer\n", "reviewer"),
    (None, {}, "\n\n\n", None),
], ids=["flag", "env", "file", "none", "blank-lines-and-padding", "only-blank-lines"])
def test_ac2_resolve_role(ws: Path, explicit: str | None, environ: dict[str, str],
                          role_file: str | None, active: str | None) -> None:
    """AC-2: flag, then QR_ROLE, then the first non-empty line of the role file, else none."""
    from quality_router.harness.policy import resolve_role

    if role_file is not None:
        (ws / ROLE_FILE).write_text(role_file)
    assert resolve_role(ws, explicit, environ) == active


def test_ac2_resolve_role_reads_given_environ(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-2: QR_ROLE is taken from the environ argument."""
    from quality_router.harness.policy import resolve_role

    monkeypatch.setenv("QR_ROLE", "implementer")
    (ws / ROLE_FILE).write_text("reviewer\n")
    assert resolve_role(ws, None, {}) == "reviewer"
    assert resolve_role(ws, None, {"QR_ROLE": "docs"}) == "docs"


def test_ac2_resolve_role_file_under_given_root(tmp_path: Path) -> None:
    """AC-2: the role file is <root>/.quality-router/role for the root passed in."""
    from quality_router.harness.policy import resolve_role

    a, b = tmp_path / "a", tmp_path / "b"
    for root, name in ((a, "docs"), (b, "ops")):
        (root / ".quality-router").mkdir(parents=True)
        (root / ROLE_FILE).write_text(name + "\n")
    assert resolve_role(a, None, {}) == "docs"
    assert resolve_role(b, None, {}) == "ops"
    assert resolve_role(tmp_path, None, {}) is None


def test_ac2_check_summary_env_beats_file(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    """AC-2: policy check summary `role` follows env over file and flag over env."""
    (ws / ROLE_FILE).write_text("docs\n")
    assert _check_json(capsys, "--path", "README.md")[1]["summary"]["role"] == "docs"
    monkeypatch.setenv("QR_ROLE", "ops")
    assert _check_json(capsys, "--path", "README.md")[1]["summary"]["role"] == "ops"
    code, payload = _check_json(capsys, "--path", "README.md", "--role", "implementer")
    assert code == EXIT_PASS and payload["summary"]["role"] == "implementer"


def test_ac2_check_summary_empty_when_no_role(ws: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-2: with no flag, no QR_ROLE and a blank role file, summary role is ''."""
    (ws / ROLE_FILE).write_text("\n\n")
    code, payload = _check_json(capsys, "--write", "--path", MAIN)
    assert code == EXIT_PASS and payload["summary"]["role"] == ""


def test_ac2_check_reads_role_file_under_root_flag(ws: Path, tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    """AC-2: `qr policy check --root R` reads R/.quality-router/role, not the cwd's."""
    (ws / ROLE_FILE).write_text("test-author\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    code, payload = _check_json(capsys, "--root", str(ws), "--write", "--path", MAIN)
    assert payload["summary"]["role"] == "test-author"
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_write_allow"])


def test_ac2_unknown_role_from_env_and_file(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str],
                                            tmp_path: Path) -> None:
    """AC-2: a role missing from roles is denied unknown_role whichever source named it."""
    monkeypatch.setenv("QR_ROLE", "qa-lead")
    code, payload = _check_json(capsys, "--command", "git log -1")
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_unknown_role"])
    monkeypatch.delenv("QR_ROLE")
    (ws / ROLE_FILE).write_text("intern\n")
    audit = tmp_path / "audit.jsonl"
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Read", file_path="README.md")) \
        == (2, "unknown_role")
    assert _cursor_permission(monkeypatch, capsys, _cursor_shell(ws, "ls")) == "deny"


def test_ac2_hook_flag_overrides_env(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    """AC-2: `qr policy hook --role` beats QR_ROLE, which beats the role file."""
    (ws / ROLE_FILE).write_text("implementer\n")
    write = _claude(ws, "Write", file_path=MAIN)
    assert _hook(monkeypatch, write, "claude-code") == EXIT_PASS
    monkeypatch.setenv("QR_ROLE", "reviewer")
    assert _hook(monkeypatch, write, "claude-code") == 2
    assert _hook(monkeypatch, write, "claude-code", "--role", "implementer") == EXIT_PASS
    monkeypatch.setenv("QR_ROLE", "implementer")
    assert _cursor_permission(monkeypatch, capsys, _cursor_write(ws, MAIN),
                              "--role", "test-author") == "deny"


@pytest.mark.parametrize("kind,value,access,expected", [
    ("path", "README.md", "write", "allow"),
    ("path", MAIN, "write", "allow"),
    ("path", HIDDEN, "read", "allow"),
    ("command", "git commit -m wip", "read", "allow"),
    ("command", f"echo x > {MAIN}", "read", "allow"),
    ("command", "git push --force origin feat", "read", "deny_commands"),
    ("path", "svc/.env", "read", "deny_paths"),
])
def test_ac2_no_role_decides_as_before(ws: Path, kind: str, value: str, access: str,
                                       expected: str) -> None:
    """AC-2: with no role, role limits do not apply and top-level rules still do."""
    _expect(_decide(ws, None, kind, value, access), expected)


# --------------------------------------------------------------------------- #
# AC-3
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("role,value,access,expected", [
    ("test-author", "svc-a/src/test/java/ATest.java", "write", "allow"),
    ("test-author", "src/testFixtures/java/Fixture.java", "write", "allow"),
    ("test-author", "specs/item-v3.md", "write", "allow"),
    ("test-author", "docs/specs/item-v3.md", "write", "role_write_allow"),
    ("test-author", "build.gradle", "write", "role_write_allow"),
    ("test-author", "build.gradle", "read", "allow"),
    ("reviewer", "specs/item-v3.md", "write", "role_write_allow"),
    ("reviewer", MAIN, "read", "allow"),
    ("docs", "README.md", "write", "allow"),
    ("docs", "services/ingest/README.md", "write", "allow"),
    ("docs", "docs/img/flow.png", "write", "allow"),
    ("docs", "src/A.java", "write", "role_write_allow"),
    ("implementer", "build.gradle", "write", "allow"),
])
def test_ac3_file_writes(ws: Path, role: str, value: str, access: str, expected: str) -> None:
    """AC-3: write_allow globs match relative to the root; a leading **/ matches at the root."""
    _expect(_decide(ws, role, "path", value, access), expected)


@pytest.mark.parametrize("rel,expected", [
    (MAIN, "role_write_allow"),
    (TEST, "allow"),
    ("specs/a.md", "allow"),
])
def test_ac3_absolute_paths_inside_root(ws: Path, rel: str, expected: str) -> None:
    """AC-3: an absolute path inside the root is matched relative to the root."""
    _expect(_decide(ws, "test-author", "path", str(ws / rel), "write"), expected)


@pytest.mark.parametrize("command", [
    f"echo x > {MAIN}",
    f"echo x >> {MAIN}",
    f"echo x >{MAIN}",
    f"printf x | tee {MAIN}",
    f"sed -i 's/a/b/' {MAIN}",
    f"perl -pi -e 's/a/b/' {MAIN}",
    f"mv {TEST} {MAIN}",
    f"rm {MAIN}",
    f"git checkout -- {MAIN}",
    f"truncate -s 0 {MAIN}",
])
def test_ac3_shell_writes_outside_denied(ws: Path, command: str) -> None:
    """AC-3: shell write verbs and redirects with a path outside write_allow are denied."""
    _expect(_decide(ws, "test-author", "command", command), "role_write_allow")


@pytest.mark.parametrize("command", [
    "cp src/test/java/com/acme/ItemTest.java src/test/java/com/acme/ItemCopyTest.java",
    "rm -f src/test/java/com/acme/OldTest.java",
    "cat src/test/java/com/acme/ItemTest.java > src/test/java/com/acme/ItemTwoTest.java",
    "mv src/test/java/com/acme/ItemTest.java specs/item-notes.md",
])
def test_ac3_shell_writes_inside_allowed(ws: Path, command: str) -> None:
    """AC-3: shell writes whose path arguments are all inside write_allow are allowed."""
    _expect(_decide(ws, "test-author", "command", command), "allow")


@pytest.mark.parametrize("command", [f"cat {MAIN}", "grep -rn TODO src/main/java"])
def test_ac3_shell_reads_not_limited(ws: Path, command: str) -> None:
    """AC-3: reads are not limited by write_allow."""
    _expect(_decide(ws, "test-author", "command", command), "allow")


def test_ac3_empty_write_allow_and_no_key(ws: Path) -> None:
    """AC-3: write_allow [] denies every write (redirect target too); no key means no limit."""
    _expect(_decide(ws, "reviewer", "command", "echo hi > README.md"), "role_write_allow")
    _expect(_decide(ws, "reviewer", "command", "rm docs/old/x.md"), "role_write_allow")
    _expect(_decide(ws, "implementer", "command", f"echo x > {MAIN}"), "allow")


def test_ac3_policy_check_and_cursor_hook(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    """AC-3: policy check and the Cursor hook apply write_allow for the active role."""
    code, payload = _check_json(capsys, "--role", "test-author", "--write", "--path",
                                str(ws / MAIN))
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_write_allow"])
    code, payload = _check_json(capsys, "--role", "test-author", "--command", f"rm {MAIN}")
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_write_allow"])
    monkeypatch.setenv("QR_ROLE", "test-author")
    assert _cursor_permission(monkeypatch, capsys, _cursor_write(ws, MAIN)) == "deny"
    assert _cursor_permission(monkeypatch, capsys, _cursor_write(ws, TEST)) == "allow"
    assert _cursor_permission(monkeypatch, capsys,
                              _cursor_shell(ws, f"echo x >> {MAIN}")) == "deny"
    assert _cursor_permission(monkeypatch, capsys, _cursor_read(ws, str(ws / MAIN))) == "allow"


def test_ac3_claude_hook_rule(ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-3: the Claude Code hook denies with rule role_write_allow."""
    monkeypatch.setenv("QR_ROLE", "test-author")
    audit = tmp_path / "audit.jsonl"
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Edit", file_path=str(ws / MAIN))) \
        == (2, "role_write_allow")
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Bash", command=f"tee {MAIN}")) \
        == (2, "role_write_allow")
    assert _hook(monkeypatch, _claude(ws, "Write", file_path=TEST), "claude-code") == EXIT_PASS


# --------------------------------------------------------------------------- #
# AC-4
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("role,kind,value,access,expected", [
    ("implementer", "path", HIDDEN, "write", "role_read_deny"),
    ("implementer", "path", "secret-tests/ItemSecretTest.java", "read", "role_read_deny"),
    ("implementer", "path", "mod/secret-tests/ItemSecretTest.java", "read", "role_read_deny"),
    ("implementer", "command", f"head -n 5 {HIDDEN}", "read", "role_read_deny"),
    ("implementer", "command", f"cp {HIDDEN} /tmp/copy.java", "read", "role_read_deny"),
    ("implementer", "command", f"grep -n assert ./{HIDDEN}", "read", "role_read_deny"),
    ("implementer", "command", f"wc -l < {HIDDEN}", "read", "role_read_deny"),
    ("implementer", "path", "qa/visible/ItemTest.java", "read", "allow"),
    ("implementer", "path", "docs/secret-tests.md", "read", "allow"),
    ("test-author", "path", HIDDEN, "read", "allow"),
    (None, "path", HIDDEN, "read", "allow"),
])
def test_ac4_read_deny(ws: Path, role: str | None, kind: str, value: str, access: str,
                       expected: str) -> None:
    """AC-4: read_deny globs deny reads, writes and shell commands naming a matching path."""
    _expect(_decide(ws, role, kind, value, access), expected)


def test_ac4_absolute_path(ws: Path) -> None:
    """AC-4: an absolute path inside the root matches read_deny."""
    _expect(_decide(ws, "implementer", "path", str(ws / HIDDEN)), "role_read_deny")
    _expect(_decide(ws, "implementer", "command", f"cat {ws / HIDDEN}"), "role_read_deny")


def test_ac4_hooks(ws: Path, monkeypatch: pytest.MonkeyPatch,
                   capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """AC-4: Cursor and Claude Code hooks hide read_deny paths from the active role."""
    monkeypatch.setenv("QR_ROLE", "implementer")
    assert _cursor_permission(monkeypatch, capsys, _cursor_read(ws, str(ws / HIDDEN))) == "deny"
    audit = tmp_path / "audit.jsonl"
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Read", file_path=HIDDEN)) \
        == (2, "role_read_deny")
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Bash", command=f"cat {HIDDEN}")) \
        == (2, "role_read_deny")
    code, payload = _check_json(capsys, "--path", HIDDEN)
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_read_deny"])


# --------------------------------------------------------------------------- #
# AC-5
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("role,command,expected", [
    ("reviewer", "git merge feature/x", "role_deny_commands"),
    ("reviewer", "git commit --amend --no-edit", "role_deny_commands"),
    ("reviewer", "git push origin feat", "role_deny_commands"),
    ("reviewer", "git push --force origin feat", "deny_commands"),
    ("reviewer", "git status", "allow"),
    ("implementer", "git merge feature/x", "allow"),
    ("implementer", "git push --force origin feat", "deny_commands"),
    (None, "git commit -m wip", "allow"),
])
def test_ac5_role_commands(ws: Path, role: str | None, command: str, expected: str) -> None:
    """AC-5: a role's deny_commands (string or pattern/reason form) apply after the top-level
    ones."""
    _expect(_decide(ws, role, "command", command), expected)


def test_ac5_cli_and_hooks(ws: Path, monkeypatch: pytest.MonkeyPatch,
                           capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """AC-5: policy check reports denied_role_deny_commands; hooks deny the command."""
    code, payload = _check_json(capsys, "--role", "reviewer", "--command", "git merge main")
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_deny_commands"])
    monkeypatch.setenv("QR_ROLE", "reviewer")
    code, payload = _check_json(capsys, "--command", "git commit -m wip")
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_role_deny_commands"])
    assert _cursor_permission(monkeypatch, capsys, _cursor_shell(ws, "git commit -m wip")) \
        == "deny"
    audit = tmp_path / "audit.jsonl"
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Bash", command="git merge x")) \
        == (2, "role_deny_commands")
    assert _hook(monkeypatch, _claude(ws, "Bash", command="git diff"), "claude-code") == 0


# --------------------------------------------------------------------------- #
# AC-6
# --------------------------------------------------------------------------- #

HARNESS_SHELL = [
    f"rm {POLICY_FILE}",
    f"sed -i 's/force/x/' {POLICY_FILE}",
    f"echo implementer >> {ROLE_FILE}",
    f"printf test-author | tee {ROLE_FILE}",
    f"cp /tmp/p.json {POLICY_FILE}",
    f"mv {ROLE_FILE} /tmp/role.bak",
    f"echo '{{}}' > {LOCK_FILE}",
]


@pytest.mark.parametrize("role", [None, "implementer"])
@pytest.mark.parametrize("command", HARNESS_SHELL)
def test_ac6_shell_writes_denied(ws: Path, role: str | None, command: str) -> None:
    """AC-6: shell writes to the policy, role file or lock are denied with harness_file."""
    _expect(_decide(ws, role, "command", command), "harness_file")


@pytest.mark.parametrize("role", [None, "implementer"])
@pytest.mark.parametrize("rel", [POLICY_FILE, ROLE_FILE, LOCK_FILE])
def test_ac6_file_writes_denied(ws: Path, role: str | None, rel: str) -> None:
    """AC-6: file-tool writes (relative and absolute) to harness files are harness_file, also
    when no lock exists yet."""
    _expect(_decide(ws, role, "path", rel, "write"), "harness_file")
    _expect(_decide(ws, role, "path", str(ws / rel), "write"), "harness_file")


def test_ac6_write_allow_cannot_unprotect(ws: Path) -> None:
    """AC-6: a role whose write_allow covers .quality-router/** still cannot write them."""
    for rel in (POLICY_FILE, ROLE_FILE, LOCK_FILE):
        _expect(_decide(ws, "ops", "path", rel, "write"), "harness_file")
    _expect(_decide(ws, "ops", "command", f"echo ops > {ROLE_FILE}"), "harness_file")
    _expect(_decide(ws, "ops", "path", "ops/run.sh", "write"), "allow")


@pytest.mark.parametrize("role", ["reviewer", "test-author", "docs"])
def test_ac6_every_role_denied(ws: Path, role: str) -> None:
    """AC-6: every role is denied writing the harness files."""
    for rel in (POLICY_FILE, ROLE_FILE):
        _expect(_decide(ws, role, "path", rel, "write"), "deny")


@pytest.mark.parametrize("role", [None, "implementer", "reviewer", "test-author"])
def test_ac6_reads_allowed(ws: Path, role: str | None) -> None:
    """AC-6: reading the harness files is allowed."""
    (ws / ROLE_FILE).write_text("\n")
    for rel in (POLICY_FILE, ROLE_FILE, LOCK_FILE):
        _expect(_decide(ws, role, "path", rel, "read"), "allow")
    _expect(_decide(ws, role, "command", f"cat {POLICY_FILE} {ROLE_FILE}"), "allow")


def test_ac6_cli_and_hooks(ws: Path, monkeypatch: pytest.MonkeyPatch,
                           capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """AC-6: policy check and both hooks protect the harness files; reads pass."""
    code, payload = _check_json(capsys, "--write", "--path", ROLE_FILE)
    assert (code, _errors(payload)) == (EXIT_FAIL, ["denied_harness_file"])
    code, payload = _check_json(capsys, "--path", ROLE_FILE)
    assert code == EXIT_PASS
    monkeypatch.setenv("QR_ROLE", "implementer")
    audit = tmp_path / "audit.jsonl"
    assert _claude_rule(monkeypatch, audit, _claude(ws, "Edit", file_path=POLICY_FILE)) \
        == (2, "harness_file")
    assert _cursor_permission(monkeypatch, capsys,
                              _cursor_write(ws, str(ws / ROLE_FILE))) == "deny"
    assert _cursor_permission(monkeypatch, capsys,
                              _cursor_shell(ws, f"echo reviewer > {ROLE_FILE}")) == "deny"
    assert _hook(monkeypatch, _claude(ws, "Read", file_path=POLICY_FILE), "claude-code") == 0


def test_ac6_no_policy_file_hook_stays_disconnected(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-6: protection applies when a policy file is found; with none the hook allows."""
    monkeypatch.chdir(tmp_path)
    write = _claude(tmp_path, "Write", file_path=ROLE_FILE)
    assert _hook(monkeypatch, write, "claude-code") == 0


# --------------------------------------------------------------------------- #
# AC-7
# --------------------------------------------------------------------------- #

@pytest.fixture
def stamped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "fresh"
    root.mkdir()
    monkeypatch.chdir(root)
    assert run(["init", "--policy", "--host", "claude-code"]) == 0
    return root


def test_ac7_default_roles(stamped: Path) -> None:
    """AC-7: a new policy declares exactly spec-author, test-author, implementer, reviewer."""
    roles = json.loads((stamped / POLICY_FILE).read_text())["roles"]
    assert sorted(roles) == ["implementer", "reviewer", "spec-author", "test-author"]
    assert set(roles["spec-author"]["write_allow"]) == {"specs/**", "docs/**", "**/*.md"}
    assert len(roles["spec-author"]["write_allow"]) == 3
    assert set(roles["test-author"]["write_allow"]) == {
        "**/src/test/**", "**/src/testFixtures/**", "**/src/*Test/**", "**/src/it/**",
        "specs/**"}
    assert len(roles["test-author"]["write_allow"]) == 5
    assert "write_allow" not in roles["implementer"]
    assert roles["reviewer"]["write_allow"] == []


@pytest.mark.parametrize("role,path,code", [
    ("spec-author", "README.md", EXIT_PASS),
    ("spec-author", "services/ingest/NOTES.md", EXIT_PASS),
    ("spec-author", "docs/adr/0007-roles.txt", EXIT_PASS),
    ("spec-author", "build.gradle", EXIT_FAIL),
    ("test-author", TEST, EXIT_PASS),
    ("test-author", "lib/src/testFixtures/java/Fixtures.java", EXIT_PASS),
    ("test-author", "src/it/java/ItemIT.java", EXIT_PASS),
    ("test-author", "svc/src/integrationTest/java/ItemIT.java", EXIT_PASS),
    ("test-author", "specs/item-v3.md", EXIT_PASS),
    ("test-author", MAIN, EXIT_FAIL),
    ("test-author", "README.md", EXIT_FAIL),
    ("implementer", "build.gradle", EXIT_PASS),
    ("reviewer", "README.md", EXIT_FAIL),
    ("reviewer", TEST, EXIT_FAIL),
])
def test_ac7_default_role_decisions(stamped: Path, capsys: pytest.CaptureFixture[str],
                                    role: str, path: str, code: int) -> None:
    """AC-7: the stamped roles decide writes as their write_allow says."""
    got, payload = _check_json(capsys, "--role", role, "--write", "--path", path)
    assert got == code
    if code == EXIT_FAIL:
        assert _errors(payload) == ["denied_role_write_allow"]


def test_ac7_stamped_policy_drives_hook(stamped: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-7: the hook enforces the stamped roles."""
    monkeypatch.setenv("QR_ROLE", "test-author")
    assert _hook(monkeypatch, _claude(stamped, "Write", file_path=MAIN), "claude-code") == 2
    assert _hook(monkeypatch, _claude(stamped, "Write", file_path="src/it/java/XIT.java"),
                 "claude-code") == 0


def test_ac7_existing_policy_not_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-7: re-running init leaves an existing policy byte-identical, with or without roles."""
    monkeypatch.chdir(tmp_path)
    policy = _write_policy(tmp_path, None)
    before = policy.read_bytes()
    assert run(["init", "--policy", "--host", "cursor"]) == 0
    assert policy.read_bytes() == before
    assert "roles" not in json.loads(policy.read_text())
    custom = tmp_path / "custom"
    custom.mkdir()
    monkeypatch.chdir(custom)
    assert run(["init", "--policy"]) == 0
    data = json.loads((custom / POLICY_FILE).read_text())
    data["roles"] = {"solo": {"write_allow": ["**"]}}
    (custom / POLICY_FILE).write_text(json.dumps(data))
    edited = (custom / POLICY_FILE).read_bytes()
    assert run(["init", "--policy"]) == 0
    assert (custom / POLICY_FILE).read_bytes() == edited

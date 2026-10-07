# Phase 7: enforced SDD roles and held-out acceptance tests

Contract: `src/quality_router/harness/policy.py` (roles, harness files,
holdout hiding) and `src/quality_router/harness/acceptance.py` (holdout
lock and gate).

Problem: the spec-driven flow relies on separate steps (spec, tests,
implementation), but nothing stops the implementing agent from writing
or reading tests, editing the policy file, or seeing every test it is
judged by. Tests written after seeing the code lose 8–18 points of fault
detection (2607.05139); agents near 97% on visible tests pass hidden
validators less than half the time (2608.19799).

Out of scope: running builds, launching agents, copying holdout files
into CI (the build does that), Python test layouts.

Interfaces: `Policy.roles` maps a name to a role with `write_allow`
(`list[str] | None`), `read_deny` (`list[str]`) and `deny_commands`.
`resolve_role(root, explicit, environ) -> str | None`.
`decide(event, policy, root, locked=None, role=None, holdout=None)`.
`build_lock(..., holdout=None)` and `gate_holdout(root, reports, base=None,
strict=False) -> GateResult` (gate name `holdout`). Rules are reported in
`Decision.rule` and as `denied_<rule>` codes by `qr policy check`.

### AC-1 Roles are declared in policy.json

`roles` is optional and maps a role name to an object with optional
`write_allow`, `read_deny` and `deny_commands` (same shape as the
top-level list). No `write_allow` key means no role write limit; an empty
list means the role may write nothing. A malformed `roles` value makes
`qr policy check` exit 2 and `qr policy hook` deny.

| roles value | `policy check` exit |
| --- | --- |
| absent | 0 for an allowed path |
| `{"reviewer": {"write_allow": []}}` | 0 for an allowed read |
| `["reviewer"]` | 2 |
| `{"reviewer": "x"}` | 2 |
| `{"r": {"deny_commands": ["("]}}` | 2 |

### AC-2 The active role comes from flag, environment, then file

The role is `--role NAME` on `qr policy check` and `qr policy hook`, else
the `QR_ROLE` environment variable, else the first non-empty line of
`<root>/.quality-router/role`, else none. With no role, decisions are
the same as before this phase. A role name missing from `roles` is denied
with rule `unknown_role`. `qr policy check` reports the role in its
summary as `role` (empty string when none).

| `--role` | `QR_ROLE` | role file | active role |
| --- | --- | --- | --- |
| `test-author` | `implementer` | `reviewer` | test-author |
| (none) | `implementer` | `reviewer` | implementer |
| (none) | (unset) | `reviewer` | reviewer |
| (none) | (unset) | (absent) | none |
| `ghost` | (unset) | (absent) | denied `unknown_role` |

### AC-3 `write_allow` limits where a role may write

With an active role that has `write_allow`, a file write outside every
glob is denied with rule `role_write_allow`, and so is a shell command
that writes (the verbs and redirects the lock check already detects)
with a path argument outside every glob. Reads are not limited. Globs
match like `deny_paths`: relative to the root, a leading `**/` also
matches at the root.

| role (write_allow) | event | decision |
| --- | --- | --- |
| test-author (`**/src/test/**`, `specs/**`) | write `src/test/java/ATest.java` | allow |
| test-author (same) | write `src/main/java/A.java` | deny `role_write_allow` |
| test-author (same) | read `src/main/java/A.java` | allow |
| test-author (same) | `cp x.java src/main/java/A.java` | deny `role_write_allow` |
| reviewer (`[]`) | write `README.md` | deny `role_write_allow` |
| implementer (no key) | write `src/main/java/A.java` | allow |

### AC-4 `read_deny` hides paths from a role

A file read or write of a path matching a role's `read_deny` glob is
denied with rule `role_read_deny`, and so is any shell command with a
path argument that matches.

| role (read_deny) | event | decision |
| --- | --- | --- |
| implementer (`holdout/**`) | read `holdout/ItemHoldoutTest.java` | deny `role_read_deny` |
| implementer (same) | `cat holdout/ItemHoldoutTest.java` | deny `role_read_deny` |
| implementer (same) | read `src/test/java/ATest.java` | allow |
| test-author (`[]`) | read `holdout/ItemHoldoutTest.java` | allow |

### AC-5 Roles add command rules

A role's `deny_commands` apply after the top-level ones, with rule
`role_deny_commands`.

| role (deny_commands) | command | decision |
| --- | --- | --- |
| reviewer (`\bgit\s+commit\b`) | `git commit -m x` | deny `role_deny_commands` |
| implementer (none) | `git commit -m x` | allow |
| reviewer (same) | `git log -1` | allow |

### AC-6 The harness's own files are write-protected

When a policy file is found, writes to `.quality-router/policy.json`,
`.quality-router/role` and `.quality-router/acceptance.lock.json` are
denied for every role and with no role, rule `harness_file`, by file
tools and by shell write commands. Reads are allowed.

| role | event | decision |
| --- | --- | --- |
| (none) | write `.quality-router/policy.json` | deny `harness_file` |
| implementer | `echo reviewer > .quality-router/role` | deny `harness_file` |
| test-author | write `.quality-router/acceptance.lock.json` | deny |
| (none) | read `.quality-router/policy.json` | allow |

### AC-7 A new policy stamps four default roles

`qr init --policy` writes `roles` into a new policy only:
`spec-author` (`write_allow`: `specs/**`, `docs/**`, `**/*.md`),
`test-author` (`write_allow`: `**/src/test/**`, `**/src/testFixtures/**`,
`**/src/*Test/**`, `**/src/it/**`, `specs/**`), `implementer` (no
`write_allow`) and `reviewer` (`write_allow`: empty). An existing policy
is not changed.

| role | write | decision |
| --- | --- | --- |
| spec-author | `specs/item-v2.md` | allow |
| spec-author | `src/main/java/A.java` | deny |
| test-author | `src/integrationTest/java/AIT.java` | allow |
| implementer | `src/main/java/A.java` | allow |
| reviewer | `specs/item-v2.md` | deny |

### AC-8 The lock records held-out tests by hash

`qr spec lock --holdout PATH...` (paths or globs under `--root`) adds a
`holdout` map to the lock: relative path to `sha256` and the criteria ids
found in the file. Each holdout file must exist, must not also be a
`--tests` file, and must not be tracked by git under the root (a root
that is not a git work tree counts as untracked). A lock without
`--holdout` has no `holdout` key.

| holdout file | `spec lock` exit | lock |
| --- | --- | --- |
| untracked, mentions AC-1 | 0 | `holdout` entry with criteria `["AC-1"]` |
| missing | 2 | not written |
| tracked by git | 2 | not written |
| also passed to `--tests` | 2 | not written |
| (no `--holdout`) | 0 | no `holdout` key |

### AC-9 Held-out tests are hidden from every role but test-author

When the lock has `holdout` entries, reads and writes of those paths, and
shell commands naming them, are denied with rule `holdout` unless the
active role is `test-author`.

| role | event | decision |
| --- | --- | --- |
| (none) | read a holdout path | deny `holdout` |
| implementer | `grep -n assert <holdout path>` | deny `holdout` |
| test-author | read a holdout path | allow |
| implementer | read a locked visible test | allow |

### AC-10 `qr gate holdout` checks held-out tests ran unmodified and passed

`qr gate holdout [--root .] --reports GLOB... [--base REF] [--json]
[--strict]` reads the lock and JUnit XML. A file's tests are the
testcases whose classname equals its file stem, ends with `.` + stem, or
continues with `$` after either.

| situation | finding | exit |
| --- | --- | --- |
| no lock, or no `holdout` key | warning `no_holdout` | 0 (1 with `--strict`) |
| reports pattern matches nothing | `Error: JUnit report not found` on stderr | 2 |
| holdout file absent | error `holdout_missing` | 1 |
| holdout file bytes differ from the lock | error `holdout_modified` | 1 |
| holdout file tracked by git, or touched by a commit in `REF..HEAD` | error `holdout_exposed` | 1 |
| no testcase for the file, or all skipped | error `holdout_not_run` | 1 |
| a testcase failed or errored | error `holdout_failed` naming the methods | 1 |
| all ran and passed | none | 0 |

The summary has exactly `holdout_files`, `holdout_tests`,
`holdout_failed`, `holdout_skipped`, `criteria` (sorted ids from the
lock's holdout entries) and `reports`.

| reports | summary |
| --- | --- |
| one holdout file, 2 passing testcases, AC-1 | `holdout_files=1 holdout_tests=2 holdout_failed=0 holdout_skipped=0 criteria=["AC-1"] reports=1` |

### AC-11 Existing locks and gates behave as before

`qr gate acceptance` ignores the `holdout` key and does not need holdout
files present. Locks without `holdout` load and protect files as before.

| lock | holdout file present | `gate acceptance` |
| --- | --- | --- |
| with `holdout`, visible files unchanged | no | pass |
| without `holdout`, visible files unchanged | (n/a) | pass |

### AC-12 Help shows the new options

| argv | stdout contains |
| --- | --- |
| `gate holdout --help` | `--reports` |
| `policy check --help` | `--role` |
| `spec lock --help` | `--holdout` |
| `gate --help` | `qr gate holdout` |

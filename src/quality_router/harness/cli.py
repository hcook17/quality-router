"""argparse wiring for phase-3 harness commands: gate, lint, spec, contracts, policy, eval."""

from __future__ import annotations

import glob
import json
import re
import sys
import textwrap
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

from quality_router.harness import (
    contracts,
    coverage_gate,
    evalkit,
    instructions,
    oracles,
    spec_trace,
)
from quality_router.harness import policy as policy_mod
from quality_router.harness.gitdiff import load_diff
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE, GateResult

GATE_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr gate diff-coverage --base origin/main --jacoco '**/target/site/jacoco/jacoco.xml'
      qr gate diff-coverage --diff pr.diff --jacoco target/site/jacoco/jacoco.xml --min 0.9
      qr gate test-oracles --base origin/main
      qr gate test-oracles --paths src/test/java/com/acme/IngestTest.java --json

    Exit 0 pass, 1 gate failed, 2 usage error. Reads reports; never runs Maven/Gradle.
    """
)
LINT_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr lint instructions
      qr lint instructions --root ../content-ingest --max-lines 120 --strict --json
    """
)
SPEC_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr spec trace --spec specs/content-ingest.md --tests .
      qr spec trace --spec ../umbrella/specs/item-v2.md --tests ../ingest --tests ../delivery
      qr spec trace --spec specs/x.md --tests . --id-pattern 'CI-\\d+' --strict

    Number acceptance criteria (AC-1 ...) and tag tests with the id
    (@Tag("AC-1"), @DisplayName("AC-1 ..."), or a comment). Tag MUST/SHALL
    lines with an AC id or [check: ArchUnitLayerRules].
    """
)
CONTRACTS_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr contracts diff --old git:origin/main:contracts/content-item.schema.json \\
                        --new contracts/content-item.schema.json
      qr contracts diff --old v1/openapi.json --new build/openapi.json
      qr contracts diff --old old.avsc --new new.avsc --avro-mode backward
      qr contracts check --manifest ../coordination/contracts.json --json

    JSON Schema roles: output (we produce; consumers read) or input (we accept).
    `check` reads every listed checkout and writes nothing.
    """
)
POLICY_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr policy check --command 'git push --force origin main'
      qr policy check --path src/main/resources/.env
      echo '{"command":"curl https://x.io"}' | qr policy hook --host cursor

    Policy: .quality-router/policy.json (stamp with `qr init --policy`).
    No policy file -> hook allows (disconnected no-op). Bad policy or bad
    payload -> hook denies (fail closed).
    """
)
EVAL_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr eval prepare --repo ../content-ingest --base 3f2a9c1 --task-id ING-142 \\
                      --hidden src/test/java/com/acme/ingest/Ing142Test.java --out /tmp/ING-142
      qr eval report --runs runs.jsonl
      qr eval report --runs runs.jsonl --baseline 'claude-code@2.1.0/sonnet-5' --json

    runs.jsonl: one object per run with task, host, host_version, model,
    resolved, tokens, tool_calls. qr never launches an agent.
    """
)


def register(subparsers) -> None:
    _gate(subparsers)
    _lint(subparsers)
    _spec(subparsers)
    _contracts(subparsers)
    _policy(subparsers)
    _eval(subparsers)


def _common(parser: ArgumentParser, strict: bool = True) -> None:
    parser.add_argument("--json", action="store_true", help="Machine-readable result on stdout.")
    if strict:
        parser.add_argument("--strict", action="store_true", help="Warnings also fail the gate.")


def _diff_source(parser: ArgumentParser) -> None:
    parser.add_argument("--base", default=None, help="Diff against REF...HEAD (git).")
    parser.add_argument("--diff", default=None, help="Unified diff file, or - for stdin.")
    parser.add_argument("--cwd", default=".", help="Repository root (default: current dir).")


def _sub(subparsers, name: str, help_text: str, epilog: str) -> ArgumentParser:
    return subparsers.add_parser(name, help=help_text, epilog=epilog,
                                 formatter_class=RawDescriptionHelpFormatter)


def _gate(subparsers) -> None:
    gate = _sub(subparsers, "gate", "Deterministic merge gates over CI artifacts.", GATE_EPILOG)
    gates = gate.add_subparsers(dest="gate_command", required=True)

    cov = _sub(gates, "diff-coverage", "JaCoCo coverage of changed lines (catch blocks apart).",
               GATE_EPILOG)
    _diff_source(cov)
    cov.add_argument("--jacoco", action="append", required=True,
                     help="jacoco.xml path or glob; repeat per module.")
    cov.add_argument("--min", type=float, default=0.8, help="Minimum diff coverage (0-1).")
    cov.add_argument("--catch-min", type=float, default=None,
                     help="Minimum coverage of changed catch-block lines (default: warn only).")
    cov.add_argument("--include-tests", action="store_true", help="Also count src/test lines.")
    _common(cov, strict=False)
    cov.set_defaults(handler=cmd_diff_coverage)

    orc = _sub(gates, "test-oracles", "Changed JUnit tests must assert a value or exception.",
               GATE_EPILOG)
    _diff_source(orc)
    orc.add_argument("--paths", nargs="+", default=None,
                     help="Check every test method in these files instead of a diff.")
    orc.add_argument("--allow-weak", action="store_true",
                     help="Null/boolean-only assertions warn instead of fail.")
    orc.add_argument("--assert-helper", action="append", default=[],
                     help="Project assertion helper counted as strong (repeatable).")
    _common(orc, strict=False)
    orc.set_defaults(handler=cmd_test_oracles)


def _lint(subparsers) -> None:
    lint = _sub(subparsers, "lint", "Lint agent-facing files.", LINT_EPILOG)
    lints = lint.add_subparsers(dest="lint_command", required=True)
    ins = _sub(lints, "instructions",
               "AGENTS.md/CLAUDE.md: bloat, stale refs, prose-only rules.", LINT_EPILOG)
    ins.add_argument("--root", default=".", help="Repository root.")
    ins.add_argument("--max-lines", type=int, default=150, help="Context-bloat threshold.")
    _common(ins)
    ins.set_defaults(handler=cmd_lint_instructions)


def _spec(subparsers) -> None:
    spec = _sub(subparsers, "spec", "Spec checks for spec-driven development.", SPEC_EPILOG)
    specs = spec.add_subparsers(dest="spec_command", required=True)
    trace = _sub(specs, "trace", "Every acceptance criterion and MUST/SHALL maps to a check.",
                 SPEC_EPILOG)
    trace.add_argument("--spec", nargs="+", required=True, help="Spec markdown files or globs.")
    trace.add_argument("--tests", action="append", required=True,
                       help="Test root(s) to search; repeat for other checkouts.")
    trace.add_argument("--id-pattern", default=spec_trace.DEFAULT_ID_PATTERN,
                       help="Regex for criterion ids.")
    trace.add_argument("--max-constraints", type=int, default=10,
                       help="MUST/SHALL count per spec before a constraint-load warning.")
    _common(trace)
    trace.set_defaults(handler=cmd_spec_trace)


def _contracts(subparsers) -> None:
    con = _sub(subparsers, "contracts", "Contract breaking-change checks.", CONTRACTS_EPILOG)
    cons = con.add_subparsers(dest="contracts_command", required=True)
    diff = _sub(cons, "diff", "Classify changes between two contract versions.",
                CONTRACTS_EPILOG)
    diff.add_argument("--old", required=True, help="Path or git:REF:path.")
    diff.add_argument("--new", required=True, help="Path or git:REF:path.")
    diff.add_argument("--role", choices=["output", "input"], default="output")
    diff.add_argument("--avro-mode", choices=["backward", "forward", "full"], default="full")
    diff.add_argument("--cwd", default=".", help="Repository root for git: specs.")
    _common(diff)
    diff.set_defaults(handler=cmd_contracts_diff)

    check = _sub(cons, "check", "Consumers' vendored contracts vs providers (read-only).",
                 CONTRACTS_EPILOG)
    check.add_argument("--manifest", required=True, help="contracts.json in the coordination repo.")
    check.add_argument("--checkouts", default=None,
                       help="Directory the manifest's repo paths are relative to.")
    _common(check)
    check.set_defaults(handler=cmd_contracts_check)


def _policy(subparsers) -> None:
    pol = _sub(subparsers, "policy", "Portable agent policy (deny commands/paths, egress).",
               POLICY_EPILOG)
    pols = pol.add_subparsers(dest="policy_command", required=True)
    check = _sub(pols, "check", "Decide one command or path; exit 1 when denied.", POLICY_EPILOG)
    target = check.add_mutually_exclusive_group(required=True)
    target.add_argument("--command", dest="shell_command", default=None)
    target.add_argument("--path", default=None)
    check.add_argument("--policy", default=None, help="Policy file (default: repo policy).")
    check.add_argument("--root", default=".", help="Repository root.")
    _common(check, strict=False)
    check.set_defaults(handler=cmd_policy_check)

    hook = _sub(pols, "hook", "Host hook adapter: JSON on stdin, host protocol out.",
                POLICY_EPILOG)
    hook.add_argument("--host", choices=["cursor", "claude-code"], required=True)
    hook.add_argument("--policy", default=None, help="Policy file (default: search upward).")
    hook.add_argument("--audit", default=None, help="Append decisions to this JSONL file.")
    hook.set_defaults(handler=cmd_policy_hook)


def _eval(subparsers) -> None:
    ev = _sub(subparsers, "eval", "Team-owned agent regression evaluation.", EVAL_EPILOG)
    evs = ev.add_subparsers(dest="eval_command", required=True)
    prep = _sub(evs, "prepare", "Leak-free task workspace (no history, hidden tests apart).",
                EVAL_EPILOG)
    prep.add_argument("--repo", required=True)
    prep.add_argument("--base", required=True, help="Commit the task starts from.")
    prep.add_argument("--task-id", required=True)
    prep.add_argument("--out", required=True, help="Empty output directory.")
    prep.add_argument("--hidden", action="append", default=[],
                      help="Path withheld from the workspace (repeatable).")
    prep.add_argument("--prompt", default=None, help="Task statement stored in task.json.")
    prep.add_argument("--dry-run", action="store_true", help="Print the plan; write nothing.")
    prep.set_defaults(handler=cmd_eval_prepare)

    rep = _sub(evs, "report", "Resolve rate (Wilson CI), tokens, flips per host@version/model.",
               EVAL_EPILOG)
    rep.add_argument("--runs", required=True, help="runs.jsonl")
    rep.add_argument("--baseline", default=None, help="Group key host@version/model.")
    rep.add_argument("--max-token-increase", type=float, default=0.25)
    rep.add_argument("--max-rate-drop", type=float, default=0.05)
    _common(rep, strict=False)
    rep.set_defaults(handler=cmd_eval_report)


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #

def _emit(result: GateResult, args: Namespace) -> int:
    sys.stdout.write(result.render(getattr(args, "json", False)))
    return result.exit_code()


def _usage(message: str, example: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    print(f"  {example}", file=sys.stderr)
    return EXIT_USAGE


def _expand(patterns: list[str], cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            base = pattern if Path(pattern).is_absolute() else str(cwd / pattern)
            paths.extend(Path(p) for p in sorted(glob.glob(base, recursive=True)))
        else:
            path = Path(pattern)
            paths.append(path if path.is_absolute() else cwd / path)
    return paths


def _changed(args: Namespace, cwd: Path, pathspecs: list[str]) -> dict[str, set[int]] | int:
    stdin_text = sys.stdin.read() if args.diff == "-" else None
    try:
        return load_diff(args.diff, args.base, cwd, stdin_text, pathspecs)
    except ValueError as exc:
        return _usage(str(exc), "qr gate diff-coverage --base origin/main --jacoco <xml>")
    except (OSError, RuntimeError) as exc:
        return _usage(str(exc), "git fetch origin main  # then retry with --base origin/main")


def cmd_diff_coverage(args: Namespace) -> int:
    cwd = Path(args.cwd)
    reports_paths = _expand(args.jacoco, cwd)
    missing = [p for p in reports_paths if not p.is_file()]
    if not reports_paths or missing:
        return _usage(f"JaCoCo report not found: {missing or args.jacoco}",
                      "mvn -B verify  # with jacoco-maven-plugin report goal bound")
    changed = _changed(args, cwd, ["*.java"])
    if isinstance(changed, int):
        return changed
    reports = [coverage_gate.parse_jacoco(p, cwd) for p in reports_paths]
    result = coverage_gate.run_diff_coverage(changed, reports, cwd, args.min, args.catch_min,
                                             args.include_tests)
    result.summary["reports"] = len(reports)
    return _emit(result, args)


def cmd_test_oracles(args: Namespace) -> int:
    cwd = Path(args.cwd)
    files: dict[str, set[int] | None]
    if args.paths:
        files = {str(Path(p)): None for p in args.paths}
    else:
        changed = _changed(args, cwd, ["*.java"])
        if isinstance(changed, int):
            return changed
        files = dict(changed)
    result = oracles.run_test_oracles(files, cwd, args.allow_weak, tuple(args.assert_helper))
    return _emit(result, args)


def cmd_lint_instructions(args: Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        return _usage(f"not a directory: {root}", "qr lint instructions --root .")
    return _emit(instructions.lint_instructions(root, args.max_lines, args.strict), args)


def cmd_spec_trace(args: Namespace) -> int:
    specs = _expand(args.spec, Path.cwd())
    missing = [str(p) for p in specs if not p.is_file()]
    if not specs or missing:
        return _usage(f"spec not found: {missing or args.spec}",
                      "qr spec trace --spec specs/feature.md --tests .")
    tests = [Path(t) for t in args.tests]
    try:
        re.compile(args.id_pattern)
    except re.error as exc:
        return _usage(f"bad --id-pattern: {exc}", "qr spec trace --id-pattern 'AC-\\d+' ...")
    result = spec_trace.trace_spec(specs, tests, args.id_pattern, args.max_constraints,
                                   args.strict)
    return _emit(result, args)


def cmd_contracts_diff(args: Namespace) -> int:
    try:
        result = contracts.run_contract_diff(args.old, args.new, Path(args.cwd), args.role,
                                             args.avro_mode, args.strict)
    except contracts.ContractError as exc:
        return _usage(str(exc), "qr contracts diff --old old.json --new new.json")
    return _emit(result, args)


def cmd_contracts_check(args: Namespace) -> int:
    manifest = Path(args.manifest)
    if not manifest.is_file():
        return _usage(f"manifest not found: {manifest}",
                      "qr contracts check --manifest contracts.json")
    try:
        result = contracts.run_contract_check(
            manifest, Path(args.checkouts) if args.checkouts else None, args.strict)
    except (contracts.ContractError, json.JSONDecodeError, KeyError) as exc:
        return _usage(f"bad manifest or contract: {exc}",
                      "qr contracts check --manifest contracts.json")
    return _emit(result, args)


def cmd_policy_check(args: Namespace) -> int:
    root = Path(args.root)
    try:
        policy, _ = policy_mod.load_policy(root, args.policy)
    except FileNotFoundError as exc:
        return _usage(str(exc), "qr init --policy")
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        return _usage(f"invalid policy: {exc}", "python -m json.tool .quality-router/policy.json")
    if args.shell_command is not None:
        decision = policy.check_command(args.shell_command, root)
    else:
        decision = policy.check_path(args.path, root)
    result = GateResult(gate="policy")
    if not decision.allow:
        result.add("error", f"denied_{decision.rule}", decision.reason)
    result.summary["decision"] = "allow" if decision.allow else "deny"
    return _emit(result, args)


def _find_policy(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / policy_mod.POLICY_PATH
        if candidate.is_file():
            return candidate
    return None


def cmd_policy_hook(args: Namespace) -> int:
    raw = sys.stdin.read()
    deny = policy_mod.Decision(False, "", "hook_error")
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise ValueError("hook payload is not a JSON object")
        event = policy_mod.parse_hook_event(payload)
        start = Path(event.cwd) if event and event.cwd else Path.cwd()
        path = Path(args.policy) if args.policy else _find_policy(start)
        if path is None or not path.is_file():
            decision = policy_mod.Decision(True, "no policy file (disconnected)", "none")
            root = start
        else:
            root = path.parent.parent if path.parent.name == ".quality-router" else start
            decision = policy_mod.decide(event, policy_mod.Policy.load(path), root)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError, OSError) as exc:
        event = None
        decision = policy_mod.Decision(False, f"policy hook failed closed: {exc}", deny.rule)
    if args.audit:
        policy_mod.audit(Path(args.audit), args.host, event, decision)
    code, out, err = policy_mod.hook_response(args.host, decision)
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


def cmd_eval_prepare(args: Namespace) -> int:
    repo, out = Path(args.repo), Path(args.out)
    if not (repo / ".git").exists():
        return _usage(f"not a git checkout: {repo}", "qr eval prepare --repo ../service ...")
    if args.dry_run:
        plan = {"repo": str(repo), "base": args.base, "task": args.task_id, "out": str(out),
                "hidden": args.hidden, "steps": ["git archive base", "move hidden paths",
                                                 "git init single snapshot", "write task.json"]}
        print(f"dry_run={json.dumps(plan, sort_keys=True)}")
        return EXIT_PASS
    try:
        manifest = evalkit.prepare_task(repo, args.base, args.hidden, out, args.task_id,
                                        args.prompt)
    except (FileExistsError, FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_FAIL
    print(f"workspace={out / 'workspace'}")
    print(f"hidden={out / 'hidden'}")
    print(f"base_commit={manifest['base_commit']}")
    return EXIT_PASS


def cmd_eval_report(args: Namespace) -> int:
    runs_path = Path(args.runs)
    if not runs_path.is_file():
        return _usage(f"runs file not found: {runs_path}", "qr eval report --runs runs.jsonl")
    try:
        runs = evalkit.load_runs(runs_path)
    except (ValueError, json.JSONDecodeError) as exc:
        return _usage(str(exc), "one JSON object per line with task, host, model, resolved")
    if not runs:
        return _usage("runs file is empty", "qr eval report --runs runs.jsonl")
    result = evalkit.eval_report(runs, args.baseline, args.max_token_increase, args.max_rate_drop)
    return _emit(result, args)

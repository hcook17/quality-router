"""argparse wiring for harness commands: gate, lint, spec, feedback, contracts, policy, eval."""

from __future__ import annotations

import glob
import json
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

from quality_router.harness import (
    acceptance,
    api_compat,
    contracts,
    coverage_gate,
    evalkit,
    instructions,
    javabuild,
    junit_feedback,
    oracles,
    scaffold,
    spec_trace,
    specdoc,
)
from quality_router.harness import policy as policy_mod
from quality_router.harness.gitdiff import load_diff
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE, GateResult

DEFAULT_JAVA_RELEASE = 17

GATE_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr gate diff-coverage --base origin/main --jacoco '**/target/site/jacoco/jacoco.xml'
      qr gate diff-coverage --diff pr.diff --jacoco target/site/jacoco/jacoco.xml --min 0.9
      qr gate test-oracles --base origin/main
      qr gate test-oracles --paths src/test/java/com/acme/IngestTest.java --json
      qr gate acceptance --base origin/main
      qr gate api-compat --report '**/target/japicmp/*.xml'
      qr gate api-compat --report build/japicmp.xml --level binary --ignore 'com.acme.internal.*'
      qr gate api-compat --report target/japicmp/japicmp.xml --allow-major-bump --strict

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
      qr spec new --title 'Content item v2' --out specs/content-item-v2.md
      qr spec lint --spec specs/content-item-v2.md
      qr spec scaffold --spec specs/content-item-v2.md --package com.acme.normalize \\
          --class ContentItemV2AcceptanceTest --ac AC-1 --ac AC-2 \\
          --bind 'AC-1=new Normalizer().title(input)' \\
          --out src/test/java/com/acme/normalize/ContentItemV2AcceptanceTest.java
      qr spec scaffold --spec specs/content-item-v2.md --package com.acme.normalize \\
          --spring-boot-test --field '@Autowired ContentNormalizer normalizer' \\
          --bind 'AC-1=normalizer.title(title)' --java-release 11 \\
          --out src/test/java/com/acme/normalize/ContentItemV2AcceptanceTest.java
      qr spec lock --spec specs/content-item-v2.md \\
          --tests src/test/java/com/acme/normalize/ContentItemV2AcceptanceTest.java
      qr spec trace --spec ../umbrella/specs/item-v2.md --tests ../ingest --tests ../delivery

    Acceptance-first flow: new -> lint -> scaffold -> bind + review -> lock
    (a spec-only change a human approves) -> implement against the lock.
    `qr gate acceptance` fails if a locked file changed or the lock was
    re-written after implementation; the policy hook blocks the edit first.
    """
)
FEEDBACK_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr feedback junit --reports 'target/surefire-reports/*.xml' --sources src/test/java
      qr feedback junit --reports 'build/test-results/test/*.xml' --sources src/test/java \\
          --spec ../coordination/specs/content-item-v2.md --json

    Reads JUnit XML (Surefire, Gradle, console launcher) after the build ran.
    Prints expected/actual, trimmed app frames, the criterion and the spec's
    example row. Exit 0 no failures, 1 failures, 2 no reports.
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
      qr policy check --write --path src/test/java/com/acme/ItemV2AcceptanceTest.java
      echo '{"command":"curl https://x.io"}' | qr policy hook --host cursor

    Policy: .quality-router/policy.json (stamp with `qr init --policy`).
    No policy file -> hook allows (disconnected no-op). Bad policy or bad
    payload -> hook denies (fail closed). A .quality-router/acceptance.lock.json
    makes locked tests, specs and the lock read-only to the agent.
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
    _feedback(subparsers)
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

    acc = _sub(gates, "acceptance",
               "Locked acceptance tests/spec unchanged; approved before implemented.",
               GATE_EPILOG)
    acc.add_argument("--root", default=".", help="Repository root holding the lock.")
    acc.add_argument("--base", default=None,
                     help="Also check commit order in REF..HEAD: no src/main commit before "
                          "the lock commit (needs history: fetch-depth: 0).")
    _common(acc)
    acc.set_defaults(handler=cmd_gate_acceptance)

    api = _sub(gates, "api-compat",
               "Binary/source breaks in japicmp XML reports (shared Java libraries).",
               GATE_EPILOG)
    api.add_argument("--report", action="append", required=True,
                     help="japicmp XML report path or glob; repeat per module.")
    api.add_argument("--cwd", default=".", help="Root that report paths are relative to.")
    api.add_argument("--level", choices=api_compat.LEVELS, default="both",
                     help="Which incompatibility fails the gate (default: both).")
    api.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                     help="Class name glob whose breaks are info only (repeatable).")
    api.add_argument("--allow-major-bump", action="store_true",
                     help="Breaks are warnings when newVersion has a greater major version.")
    _common(api)
    api.set_defaults(handler=cmd_api_compat)


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

    lint = _sub(specs, "lint", "Testability: examples per criterion, contract, no vague terms.",
                SPEC_EPILOG)
    lint.add_argument("--spec", nargs="+", required=True, help="Spec markdown files or globs.")
    lint.add_argument("--root", action="append", default=[],
                      help="Extra directory to resolve Contract: paths (repeatable).")
    lint.add_argument("--id-pattern", default=specdoc.DEFAULT_ID_PATTERN,
                      help="Regex for criterion ids.")
    _common(lint)
    lint.set_defaults(handler=cmd_spec_lint)

    scaf = _sub(specs, "scaffold", "JUnit 5/6 acceptance tests from the spec's example tables.",
                SPEC_EPILOG)
    scaf.add_argument("--spec", required=True, help="Spec markdown file.")
    scaf.add_argument("--out", required=True, help="Java file to write.")
    scaf.add_argument("--class", dest="class_name", default=None,
                      help="Test class name (default: from --out).")
    scaf.add_argument("--package", default="", help="Java package.")
    scaf.add_argument("--ac", action="append", default=[],
                      help="Only these criteria (repeatable; default: all with examples).")
    scaf.add_argument("--bind", action="append", default=[],
                      help="AC=EXPR, AC.column=EXPR or *=EXPR: Java expression for the output, "
                           "using input column names as String variables.")
    scaf.add_argument("--root", action="append", default=[],
                      help="Extra directory to resolve Contract: paths.")
    scaf.add_argument("--id-pattern", default=specdoc.DEFAULT_ID_PATTERN)
    scaf.add_argument("--java-release", type=int, default=None,
                      help="Java release the test compiles for (default: read from the nearest "
                           "pom.xml/build.gradle, else 17). Below 15 rows use value = {...} "
                           "instead of a text block (Spring Boot 2.7 on Java 8/11).")
    scaf.add_argument("--spring-boot-test", action="store_true",
                      help="Annotate the class @SpringBootTest and import @Autowired, so binds "
                           "can call injected beans (Boot 2.7-4.x).")
    scaf.add_argument("--class-annotation", action="append", default=[],
                      help="Class annotation, e.g. '@SpringBootTest(classes = App.class)' or "
                           "'@ActiveProfiles(\"test\")' (repeatable).")
    scaf.add_argument("--field", action="append", default=[],
                      help="Field declaration, e.g. '@Autowired ContentNormalizer normalizer' "
                           "(repeatable).")
    scaf.add_argument("--import", dest="imports", action="append", default=[],
                      help="Extra import, e.g. com.acme.normalize.ContentNormalizer "
                           "(repeatable).")
    scaf.add_argument("--indent", type=int, default=4,
                      help="Spaces per indent level, to match the repo's formatter (default 4).")
    scaf.add_argument("--force", action="store_true", help="Overwrite an existing file.")
    scaf.add_argument("--dry-run", action="store_true", help="Print the source; write nothing.")
    scaf.set_defaults(handler=cmd_spec_scaffold)

    lock = _sub(specs, "lock", "Pin approved acceptance tests + spec by hash (human step).",
                SPEC_EPILOG)
    lock.add_argument("--root", default=".", help="Repository root (lock goes under it).")
    lock.add_argument("--spec", nargs="+", required=True, help="Spec file(s) the tests come from.")
    lock.add_argument("--tests", nargs="+", required=True, help="Acceptance test files or globs.")
    lock.add_argument("--ac", action="append", default=[],
                      help="Criteria this repo owns (default: all in the spec).")
    lock.add_argument("--id-pattern", default=specdoc.DEFAULT_ID_PATTERN)
    lock.add_argument("--approved-by", default="", help="Recorded in the lock (e.g. reviewer).")
    lock.add_argument("--dry-run", action="store_true", help="Print the lock; write nothing.")
    lock.set_defaults(handler=cmd_spec_lock)

    new = _sub(specs, "new", "Write a short executable-spec template.", SPEC_EPILOG)
    new.add_argument("--title", required=True)
    new.add_argument("--out", required=True)
    new.add_argument("--contract", default="contracts/CHANGE-ME.schema.json",
                     help="Output contract path for the Contract: line.")
    new.add_argument("--dry-run", action="store_true", help="Print the template; write nothing.")
    new.set_defaults(handler=cmd_spec_new)


def _feedback(subparsers) -> None:
    fb = _sub(subparsers, "feedback", "Repair feedback from test reports.", FEEDBACK_EPILOG)
    fbs = fb.add_subparsers(dest="feedback_command", required=True)
    junit = _sub(fbs, "junit", "JUnit XML failures -> criterion-aware feedback.",
                 FEEDBACK_EPILOG)
    junit.add_argument("--reports", nargs="+", required=True, help="JUnit XML files or globs.")
    junit.add_argument("--sources", action="append", default=[],
                       help="Test source root (repeatable), e.g. src/test/java.")
    junit.add_argument("--spec", action="append", default=[],
                       help="Spec file for criterion titles and example rows (repeatable).")
    junit.add_argument("--id-pattern", default=specdoc.DEFAULT_ID_PATTERN)
    junit.add_argument("--max-frames", type=int, default=5,
                       help="Application stack frames kept per failure.")
    _common(junit, strict=False)
    junit.set_defaults(handler=cmd_feedback_junit)


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
    check.add_argument("--write", action="store_true",
                       help="Decide --path as a write (locked acceptance files are read-only).")
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


def cmd_api_compat(args: Namespace) -> int:
    cwd = Path(args.cwd)
    expanded = {pattern: _expand([pattern], cwd) for pattern in args.report}
    paths = [p for matched in expanded.values() for p in matched]
    missing = [pattern for pattern, matched in expanded.items() if not matched]
    missing += [str(p) for p in paths if not p.is_file()]
    if missing:
        return _usage(f"japicmp report not found: {missing}",
                      "mvn -B verify  # with japicmp-maven-plugin, or japicmp --xml-file <path>")
    try:
        reports = [api_compat.parse_japicmp(p) for p in paths]
    except api_compat.ApiCompatError as exc:
        return _usage(str(exc), "qr gate api-compat --report target/japicmp/japicmp.xml")
    result = api_compat.run_api_compat(reports, cwd, args.level, tuple(args.ignore),
                                       args.allow_major_bump, args.strict)
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


def _specs_or_usage(patterns: list[str], example: str) -> list[Path] | int:
    cwd = Path.cwd()
    specs = [p.relative_to(cwd) if p.is_relative_to(cwd) else p for p in _expand(patterns, cwd)]
    missing = [str(p) for p in specs if not p.is_file()]
    if not specs or missing:
        return _usage(f"spec not found: {missing or patterns}", example)
    return specs


def _bad_pattern(pattern: str) -> int | None:
    try:
        re.compile(pattern)
    except re.error as exc:
        return _usage(f"bad --id-pattern: {exc}", "--id-pattern 'AC-\\d+'")
    return None


def cmd_spec_lint(args: Namespace) -> int:
    specs = _specs_or_usage(args.spec, "qr spec lint --spec specs/feature.md")
    if isinstance(specs, int):
        return specs
    bad = _bad_pattern(args.id_pattern)
    if bad is not None:
        return bad
    result = specdoc.lint_spec(specs, [Path(r) for r in args.root], args.id_pattern, args.strict)
    return _emit(result, args)


def _parse_binds(items: list[str]) -> dict[str, str] | None:
    binds: dict[str, str] = {}
    for item in items:
        key, sep, expr = item.partition("=")
        if not sep or not key.strip() or not expr.strip():
            return None
        binds[key.strip()] = expr.strip()
    return binds


def _lint_errors(result: GateResult) -> list[str]:
    return [f.render() for f in result.findings if f.level == "error"]


def _java_release(flag: int | None, out: Path) -> tuple[int, str]:
    if flag is not None:
        return flag, "--java-release"
    found = javabuild.detect_java_release(out)
    if found is None:
        return DEFAULT_JAVA_RELEASE, "default; no release in a pom.xml/build.gradle above --out"
    release, build = found
    return release, f"from {build}"


def cmd_spec_scaffold(args: Namespace) -> int:
    spec, out = Path(args.spec), Path(args.out)
    example = ("qr spec scaffold --spec specs/x.md --class XAcceptanceTest "
               "--out src/test/java/XAcceptanceTest.java")
    if not spec.is_file():
        return _usage(f"spec not found: {spec}", example)
    bad = _bad_pattern(args.id_pattern)
    if bad is not None:
        return bad
    binds = _parse_binds(args.bind)
    if binds is None:
        return _usage(f"bad --bind {args.bind}; use AC-1=EXPR", "--bind 'AC-1=svc.title(input)'")
    class_name = args.class_name or out.stem
    if not re.fullmatch(r"[A-Za-z_$][\w$]*", class_name):
        return _usage(f"not a Java class name: {class_name!r}", "--class ItemV2AcceptanceTest")
    if out.exists() and not args.force and not args.dry_run:
        return _usage(f"{out} exists; pass --force to regenerate (then re-lock)", example)
    lint = specdoc.lint_spec([spec], [Path(r) for r in args.root], args.id_pattern)
    if lint.errors:
        print("Error: spec does not lint clean; fix it first:", file=sys.stderr)
        for line in _lint_errors(lint):
            print(f"  {line}", file=sys.stderr)
        return EXIT_FAIL
    release, release_from = _java_release(args.java_release, out)
    parts = (tuple(args.class_annotation), tuple(args.field), tuple(args.imports))
    context = (scaffold.TestContext.spring_boot_test(*parts) if args.spring_boot_test
               else scaffold.TestContext(*parts))
    try:
        made = scaffold.scaffold_tests(specdoc.parse_spec(spec, args.id_pattern), args.package,
                                       class_name, binds, args.ac or None, release, context,
                                       args.indent)
    except scaffold.ScaffoldError as exc:
        return _usage(str(exc), example)
    if args.dry_run:
        sys.stdout.write(made.source)
        return EXIT_PASS
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(made.source, encoding="utf-8")
    print(f"wrote={out}")
    print(f"java_release={release}  # {release_from}")
    print(f"criteria={','.join(made.criteria)}")
    if made.unbound:
        print(f"unbound={','.join(made.unbound)}  # fill in the bind lines; they fail until then")
    print("next=review and format the file (e.g. spotlessApply), then `qr spec lock` in a "
          "spec-only change; reformatting after the lock fails `qr gate acceptance`")
    return EXIT_PASS


def cmd_spec_lock(args: Namespace) -> int:
    root = Path(args.root)
    example = "qr spec lock --spec specs/x.md --tests src/test/java/XAcceptanceTest.java"
    specs = _specs_or_usage(args.spec, example)
    if isinstance(specs, int):
        return specs
    bad = _bad_pattern(args.id_pattern)
    if bad is not None:
        return bad
    lint = specdoc.lint_spec(specs, [root], args.id_pattern)
    if lint.errors:
        print("Error: refusing to lock a spec that does not lint clean:", file=sys.stderr)
        for line in _lint_errors(lint):
            print(f"  {line}", file=sys.stderr)
        return EXIT_FAIL
    tests = _expand(args.tests, Path.cwd())
    try:
        lock = acceptance.build_lock(root, specs, tests, args.ac or None, args.id_pattern,
                                     args.approved_by)
    except acceptance.AcceptanceError as exc:
        return _usage(str(exc), example)
    if args.dry_run:
        sys.stdout.write(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        return EXIT_PASS
    path = acceptance.write_lock(root, lock)
    print(f"wrote={path}")
    print(f"locked_tests={len(lock['tests'])} owned={','.join(lock['owned'])}")
    print("next=commit the lock with the tests in a spec-only change for human review")
    return EXIT_PASS


def cmd_spec_new(args: Namespace) -> int:
    out = Path(args.out)
    text = specdoc.new_spec(args.title, args.contract)
    if args.dry_run:
        sys.stdout.write(text)
        return EXIT_PASS
    if out.exists():
        return _usage(f"{out} exists; refusing to overwrite", "qr spec new --title T --out new.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote={out}")
    return EXIT_PASS


def cmd_gate_acceptance(args: Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        return _usage(f"not a directory: {root}", "qr gate acceptance --root .")
    try:
        result = acceptance.gate_acceptance(root, args.base, args.strict)
    except acceptance.AcceptanceError as exc:
        return _usage(str(exc), "git fetch origin main  # then: qr gate acceptance --base "
                                "origin/main")
    return _emit(result, args)


def cmd_feedback_junit(args: Namespace) -> int:
    reports = [p for p in _expand(args.reports, Path.cwd()) if p.is_file()]
    if not reports:
        return _usage(f"no JUnit XML reports match {args.reports}",
                      "mvn -B test  # then: qr feedback junit --reports "
                      "'target/surefire-reports/*.xml'")
    bad = _bad_pattern(args.id_pattern)
    if bad is not None:
        return bad
    specs = [Path(s) for s in args.spec]
    missing = [str(s) for s in specs if not s.is_file()]
    if missing:
        return _usage(f"spec not found: {missing}", "--spec ../coordination/specs/x.md")
    try:
        total, failures = junit_feedback.parse_reports(reports, args.max_frames)
    except ET.ParseError as exc:
        return _usage(f"not JUnit XML: {exc}", "--reports 'target/surefire-reports/TEST-*.xml'")
    docs = [specdoc.parse_spec(s, args.id_pattern) for s in specs]
    junit_feedback.enrich(failures, [Path(s) for s in args.sources], docs, args.id_pattern)
    render = junit_feedback.render_json if args.json else junit_feedback.render_text
    sys.stdout.write(render(total, failures))
    return EXIT_FAIL if failures else EXIT_PASS


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
    try:
        locked = _locked_for(root)
    except acceptance.AcceptanceError as exc:
        return _usage(str(exc), "git show origin/main:.quality-router/acceptance.lock.json")
    if args.shell_command is not None:
        event = policy_mod.HookEvent("command", args.shell_command, str(root))
    else:
        event = policy_mod.HookEvent("path", args.path, str(root),
                                     "write" if args.write else "read")
    decision = policy_mod.decide(event, policy, root, locked)
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


def _locked_for(start: Path) -> set[Path]:
    lock = acceptance.find_lock(start.resolve())
    return acceptance.locked_files(lock) if lock else set()


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
        locked = _locked_for(start)
        if (path is None or not path.is_file()) and not locked:
            decision = policy_mod.Decision(True, "no policy file (disconnected)", "none")
        elif path is None or not path.is_file():
            decision = policy_mod.decide(event, policy_mod.Policy(), start, locked)
        else:
            root = path.parent.parent if path.parent.name == ".quality-router" else start
            decision = policy_mod.decide(event, policy_mod.Policy.load(path), root, locked)
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

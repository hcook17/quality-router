# Architecture diagrams

Generated from the code in `src/quality_router/` (Python 3.13, stdlib only).
Five views:
1. who produces `qr`'s inputs and who consumes its outputs;
2. how a command flows through the code;
3. the spec and acceptance-test pipeline;
4. the merge gates;
5. the policy, init and host layer.

Edge labels name the function or artifact that links two boxes.

## 1. Producers and consumers

`qr` reads artifacts other tools produce and writes only results, exit
codes and stamped files. It never runs a build, launches an agent, or sits
between a host and its tools.

```mermaid
flowchart LR
    subgraph producers["Producers: what qr reads"]
        build["Gradle / Maven build<br/>JaCoCo XML, JUnit XML, japicmp XML"]
        git["git<br/>diffs, history, index"]
        specs["Spec markdown<br/>### AC-n + example tables"]
        contracts["Contracts<br/>OpenAPI, JSON Schema, Avro"]
        hooks["Agent host hooks<br/>Claude Code PreToolUse, Cursor hooks<br/>(JSON on stdin)"]
        cfg[".quality-router/<br/>policy.json, role, acceptance.lock.json"]
        coord["Coordination repo<br/>umbrella specs, contracts.json,<br/>held-out tests"]
        runs["Agent eval runs<br/>runs.jsonl"]
    end

    qr(("qr CLI"))

    subgraph consumers["Consumers: what reads qr's output"]
        ci["CI: GitHub Actions / Jenkins<br/>exit 0 pass, 1 fail, 2 usage; --json"]
        hostout["Agent hosts<br/>allow or deny in the host's protocol"]
        people["Developers, spec owner, QA<br/>text reports, repair feedback"]
        files["Files qr stamps in a repo<br/>rule.md, hooks.sh/ps1, policy.json,<br/>.claude/settings.json, .cursor/hooks.json,<br/>qr-harness.yml, .gortex.yaml, lock,<br/>scaffolded JUnit tests, eval workspace"]
    end

    build -->|"gate diff-coverage, api-compat, holdout; feedback junit"| qr
    git -->|"--base REF / --diff; lock history"| qr
    specs -->|"spec lint, scaffold, lock, trace"| qr
    contracts -->|"contracts diff / check"| qr
    hooks -->|"policy hook"| qr
    cfg -->|"policy check / hook; gate acceptance"| qr
    coord -->|"spec trace, contracts check (read-only)"| qr
    runs -->|"eval report"| qr

    qr -->|"GateResult.render()"| ci
    qr -->|"hook_response()"| hostout
    qr -->|"text / JSON"| people
    qr -->|"init, spec scaffold, spec lock, eval prepare"| files
```

## 2. Command flow

```mermaid
flowchart TD
    entry["qr / quality-router<br/>entrypoint() → run(argv)"]
    parser["cli.build_parser()<br/>status, install, init<br/>+ harness.cli.register()"]

    entry --> parser
    parser -->|"init"| init["cmd_init → init.run_init(InitConfig)"]
    parser -->|"status"| status["cmd_status → status_report.report_status(HostBind)"]
    parser -->|"install"| install["cmd_install → install_wrap.prepare_sonar_install,<br/>build_installer_argv, invoke_installer"]
    parser -->|"gate · spec · lint · feedback ·<br/>contracts · eval · policy check"| handlers["harness.cli cmd_* handlers"]
    parser -->|"policy hook"| hook["cmd_policy_hook"]

    init -->|"validate_gortex"| stamps["_write_portable_stamps<br/>ADAPTERS[host].stamp<br/>_write_gortex_config<br/>stamp_policy + HOST_HOOK_STAMPS<br/>ci.stamp_ci"]

    handlers -->|"read artifacts"| parsers["gitdiff.load_diff · coverage_gate.parse_jacoco<br/>api_compat.parse_japicmp · specdoc.parse_spec<br/>junit_feedback.parse_reports · contracts.read_contract<br/>evalkit.load_runs · acceptance.load_lock"]
    parsers -->|"decide"| gates["run_diff_coverage · run_test_oracles · run_api_compat<br/>gate_acceptance · gate_holdout · lint_spec · trace_spec<br/>lint_instructions · run_contract_diff · run_contract_check<br/>eval_report · policy.decide"]
    gates -->|"GateResult"| emit["_emit(result)<br/>GateResult.render(as_json)<br/>GateResult.exit_code()"]

    hook -->|"stdin JSON"| parse["policy.parse_hook_event → HookEvent"]
    parse --> sets["_lock_sets: acceptance.find_lock,<br/>locked_files, holdout_files"]
    sets --> role["policy.resolve_role<br/>--role → QR_ROLE → .quality-router/role"]
    role --> decide["policy.decide(event, Policy, root,<br/>locked, role, holdout) → Decision"]
    decide -->|"--audit"| audit["policy.audit → JSONL"]
    decide --> resp["policy.hook_response(host, decision)<br/>Cursor: JSON on stdout · Claude Code: exit 2 + stderr"]
```

## 3. Spec and acceptance-test pipeline

```mermaid
classDiagram
    class SpecDoc {
        path
        lines
        criteria
        contracts
        duplicates
    }
    class Criterion {
        id
        title
        line
        body
        tables
        has_inline_example()
    }
    class ExampleTable {
        line
        headers
        rows
        row_lines
        ragged
        outputs()
        inputs()
        column_name()
    }
    class specdoc {
        <<module>>
        parse_spec(path, id_pattern) SpecDoc
        lint_spec(specs, roots, id_pattern, strict) GateResult
        new_spec(title, contract) str
        cell_value(cell)
    }
    class scaffold {
        <<module>>
        scaffold_tests(doc, package, class_name, binds, only, java_release, context, indent) Scaffold
        java_identifier(text, fallback)
        method_name(ac)
    }
    class Scaffold {
        source
        criteria
        unbound
    }
    class TestContext {
        annotations
        fields
        imports
        spring_boot_test()
        validate()
    }
    class acceptance {
        <<module>>
        build_lock(root, specs, tests, owned, id_pattern, approved_by, holdout) dict
        write_lock(root, lock)
        load_lock(path) dict
        find_lock(start)
        locked_files(lock_path)
        holdout_files(lock_path)
        gate_acceptance(root, base, strict) GateResult
        gate_holdout(root, reports, base, strict) GateResult
    }
    class spec_trace {
        <<module>>
        collect_test_text(roots)
        trace_spec(specs, test_roots, id_pattern, max_constraints, strict) GateResult
    }
    class junit_feedback {
        <<module>>
        parse_reports(paths, max_frames) Failure list
        enrich(failures, sources, specs, id_pattern)
        render_text(total, failures)
        render_json(total, failures)
    }
    class Failure {
        classname
        method
        kind
        message
        expected
        actual
        frames
        criteria
        example
    }
    class Example {
        spec
        line
        cells
    }
    class GateResult {
        gate
        findings
        summary
        strict
        add(level, code, message, path, line)
        errors()
        warnings()
        passed()
        exit_code()
        render(as_json)
    }
    class Finding {
        level
        code
        message
        path
        line
        render()
    }

    SpecDoc *-- Criterion : criteria
    Criterion *-- ExampleTable : tables
    specdoc ..> SpecDoc : parses
    scaffold ..> SpecDoc : reads example rows
    scaffold ..> TestContext : Spring options
    scaffold ..> Scaffold : returns JUnit source
    acceptance ..> specdoc : parse_spec for the lock
    junit_feedback ..> Failure : produces
    Failure o-- Example : spec row
    junit_feedback ..> SpecDoc : links AC id to row
    junit_feedback ..> scaffold : method_name
    GateResult *-- Finding : findings
    specdoc ..> GateResult : lint
    spec_trace ..> GateResult : trace
    acceptance ..> GateResult : gate acceptance, holdout
```

## 4. Merge gates

```mermaid
classDiagram
    class gitdiff {
        <<module>>
        load_diff(diff_file, base, cwd, stdin_text, pathspecs)
        git_diff(base, cwd, pathspecs)
        parse_unified_diff(text)
    }
    class coverage_gate {
        <<module>>
        parse_jacoco(xml_path, cwd) JacocoReport
        run_diff_coverage(changed, reports, cwd, minimum, catch_minimum, include_tests) GateResult
        is_test_path(path)
    }
    class JacocoReport {
        path
        module_root
        lines
    }
    class LineCov {
        covered_instr
        missed_instr
        covered_branches
        missed_branches
    }
    class javasrc {
        <<module>>
        test_methods(source) TestMethod list
        catch_block_lines(source)
        blank_strings_and_comments(source)
    }
    class TestMethod {
        name
        start_line
        end_line
        body
        annotation_args
    }
    class oracles {
        <<module>>
        classify(method, helpers) OracleVerdict
        run_test_oracles(files, cwd, allow_weak, helpers) GateResult
    }
    class OracleVerdict {
        strong
        weak
        mocks
        custom
        kind()
    }
    class api_compat {
        <<module>>
        parse_japicmp(path) JapicmpReport
        run_api_compat(reports, cwd, level, ignore, allow_major_bump, strict) GateResult
    }
    class JapicmpReport {
        path
        old_version
        new_version
        classes
        changes
    }
    class ApiChange {
        class_name
        target
        kind
        type
        binary_compatible
        source_compatible
    }
    class contracts {
        <<module>>
        read_contract(spec, cwd)
        detect_kind(doc)
        diff_contracts(old, new, role, avro_mode, kind)
        run_contract_diff(old_spec, new_spec, cwd, role, avro_mode, strict) GateResult
        run_contract_check(manifest_path, checkouts, strict) GateResult
    }
    class Change {
        level
        code
        pointer
        message
    }
    class yamlsubset {
        <<module>>
        loads(text)
    }
    class instructions {
        <<module>>
        find_instruction_files(root)
        lint_instructions(root, max_lines, strict) GateResult
    }
    class evalkit {
        <<module>>
        prepare_task(repo, base, hidden, out, task_id, prompt)
        load_runs(path)
        summarize(runs) GroupStats list
        wilson(successes, n, z)
        eval_report(runs, baseline, max_token_increase, max_rate_drop) GateResult
    }
    class GroupStats {
        key
        runs
        tasks
        resolved
        rate
        ci_low
        ci_high
        tokens_per_resolved
        flip_rate
    }
    class GateResult

    coverage_gate ..> gitdiff : changed lines
    coverage_gate ..> javasrc : catch_block_lines
    coverage_gate ..> JacocoReport : parses
    JacocoReport *-- LineCov : lines
    oracles ..> javasrc : test_methods
    oracles ..> coverage_gate : is_test_path
    javasrc ..> TestMethod : produces
    oracles ..> OracleVerdict : per method
    api_compat ..> JapicmpReport : parses
    JapicmpReport *-- ApiChange : changes
    contracts ..> yamlsubset : generated OpenAPI YAML
    contracts ..> Change : classifies
    evalkit ..> GroupStats : per host@version/model
    coverage_gate ..> GateResult
    oracles ..> GateResult
    api_compat ..> GateResult
    contracts ..> GateResult
    instructions ..> GateResult
    evalkit ..> GateResult
```

## 5. Policy, init and host layer

```mermaid
classDiagram
    class Policy {
        deny_commands
        deny_paths
        protected_branches
        egress_allow
        roles
        declared
        from_dict(data) Policy
        load(path) Policy
        check_path(path, root) Decision
        check_command(command, root) Decision
    }
    class Role {
        write_allow
        read_deny
        deny_commands
    }
    class HookEvent {
        kind
        value
        cwd
        access
    }
    class Decision {
        allow
        reason
        rule
    }
    class policy {
        <<module>>
        parse_hook_event(payload) HookEvent
        resolve_role(root, explicit, environ)
        decide(event, policy, root, locked, role, holdout) Decision
        check_locked(event, locked, root) Decision
        hook_response(host, decision)
        audit(path, host, event, decision)
        stamp_policy(root)
        stamp_cursor_hooks(root)
        stamp_claude_hooks(root)
    }
    class InitConfig {
        cwd
        host
        graph
        workspace
        workspace_deps
        no_gitnexus
        policy
        ci
        ci_java
    }
    class init {
        <<module>>
        run_init(config) str
        validate_gortex(config)
        older_gortex_shape(cwd)
    }
    class HostAdapter {
        <<abstract>>
        stamp(cwd)
    }
    class CursorAdapter
    class VsCodeAdapter
    class ClaudeCodeAdapter
    class ci {
        <<module>>
        render_ci(kind, java, java_from)
        stamp_ci(root, kind, java)
        ci_java(root, java)
    }
    class javabuild {
        <<module>>
        detect_java_release(start)
        parse_release(value)
    }
    class HostBind {
        root
        sonar_port
        sonar_mcp_url
        listen_url()
        compose_file()
        installer_script()
    }
    class status_report {
        <<module>>
        report_status(bind, cwd, windows, environ, which, listen)
        host_rows(bind, windows)
        secret_rows(environ)
        gitnexus_rows(cwd, environ)
        constituent_rows(bind, which, windows)
    }
    class install_wrap {
        <<module>>
        prepare_sonar_install(bind)
        build_installer_argv(bind, reset_volume, skip_bootstrap, windows)
        invoke_installer(argv, runner)
    }
    class harness_cli {
        <<module>>
        cmd_policy_check(args)
        cmd_policy_hook(args)
        _lock_sets(start)
    }
    class acceptance {
        <<module>>
        find_lock(start)
        locked_files(lock_path)
        holdout_files(lock_path)
    }

    Policy *-- Role : roles
    policy ..> HookEvent : parses host JSON
    policy ..> Policy : loads policy.json
    policy ..> Decision : decide
    harness_cli ..> acceptance : _lock_sets
    harness_cli ..> policy : resolve_role, decide, hook_response
    init ..> InitConfig : reads
    HostAdapter <|-- CursorAdapter
    HostAdapter <|-- VsCodeAdapter
    HostAdapter <|-- ClaudeCodeAdapter
    init ..> HostAdapter : ADAPTERS[host]
    init ..> policy : stamp_policy, HOST_HOOK_STAMPS
    init ..> ci : stamp_ci
    ci ..> javabuild : JDK from build file
    status_report ..> HostBind : reads
    install_wrap ..> HostBind : local Sonar only
```

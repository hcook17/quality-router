# quality-router

CLI mediator (`qr`) for independent quality constituents: local Sonar CE, Gortex, git hooks, Spectral, Semgrep, arXiv. Constituents stay removable. A disconnected constituent must no-op.

This is **not** an MCP aggregator. This is **not** a local-LLM host in front of those servers. This is **not** locked to Cursor (or any other agent host). Cursor is an optional `--host` stamp adapter.

`qr` is Job B (stamps, install, status, later enable/disable). Cheap vs expensive **model** pick is Job A inside the agent host you already run. The product reports `agent_host_lock=none`.

## Install

```text
uv tool install quality-router
qr --help
qr install --sonar --hooks --no-gitnexus
qr status
cd any-service
qr init --graph gortex
```

Phase 1 is `--help`, `status`, and `install` (wraps `$LOCAL_QUALITY_ROOT` `install.ps1` / `install.sh`). Phase 2 `qr init` is implemented (portable first; optional `--host` / `--graph gortex`). Specs: `docs/design/phase-1-cli.md`, `docs/design/phase-2-init.md`. Architecture lock (one file): `docs/research/architecture-decisions.md`. Do not `irm | iex`. Flags > env > defaults. Default init is portable; do not imply `--host cursor`.

## Harness gates (phase 3)

Deterministic gates for agent-written changes, derived from the arXiv KB in `research/harness-kb/` (`FINDINGS.md`). Your build writes the artifacts; `qr` reads them and exits 0 (pass), 1 (fail) or 2 (usage). It never runs Maven/Gradle and never writes to another repo.

```text
qr init --policy --host claude-code --ci github-maven   # policy.json, hook wiring, CI workflow
qr gate diff-coverage --base origin/main --jacoco '**/target/site/jacoco/jacoco.xml' --catch-min 1.0
qr gate test-oracles --base origin/main
qr lint instructions
qr spec trace --spec ../coordination/specs/item-v2.md --tests . --tests ../content-delivery
qr contracts diff --old git:origin/main:contracts/item.schema.json --new contracts/item.schema.json
qr contracts check --manifest ../coordination/contracts.json --checkouts ..
qr eval prepare --repo . --base 3f2a9c1 --task-id ING-142 --hidden src/test/java/.../Ing142Test.java --out /tmp/ING-142
qr eval report --runs runs.jsonl --baseline 'claude-code@2.1.0/sonnet-5'
```

Spec and evidence map: `docs/design/phase-3-harness.md`. Four-repo demo (ingest → normalize → store → delivery): `examples/content-pipeline/run-demo.sh --qr "uv run qr"`.

## Acceptance-first SDD (phase 4)

The research supports structured acceptance criteria with a precise contract, not SDD as a methodology. So the Spec stage produces examples, and those examples become locked tests that the implementing agent can read but cannot edit.

```text
qr spec new --title 'Content item v2' --out specs/content-item-v2.md
qr spec lint --spec specs/content-item-v2.md                  # examples, contract, no TBD/vague terms
qr spec scaffold --spec specs/content-item-v2.md --package edu.acme.normalize \
  --bind '*=new Normalizer().normalize(new RawPackage("p", "t", "PDF", manifest)).licenseId()' \
  --out src/test/java/edu/acme/normalize/ContentItemV2AcceptanceTest.java
qr spec lock --spec specs/content-item-v2.md --tests 'src/test/java/**/*AcceptanceTest.java' --approved-by qa-lead
qr gate acceptance --base origin/main                         # locked files unchanged; approved before implemented
qr feedback junit --reports 'target/surefire-reports/*.xml' --sources src/test/java --spec specs/content-item-v2.md
```

The steer for each stage, the evidence and the pilot plan are in `docs/design/phase-4-acceptance-first-sdd.md`.

## Spring Boot 2.7–4.x (phase 5)

The same commands work on Boot 2.7 repos (Java 8/11, JUnit 5.8, `javax`) and on Boot 3.x/4.x repos (Java 17+, JUnit 5.9–6, `jakarta`), with Maven or Gradle.

```text
qr spec scaffold ... --spring-boot-test --field '@Autowired ContentNormalizer normalizer' \
  --bind '*=normalizer.normalize(raw(manifest)).licenseId()'   # Java release read from pom.xml/build.gradle
qr spec scaffold ... --java-release 11                          # force @CsvSource(value = {...}) instead of a text block
qr gate test-oracles --base origin/main                         # status-only MockMvc/WebTestClient checks are weak
qr init --ci github-gradle --ci-java 21
```

Version table, binding layers (plain object, bean, MockMvc), verification and upgrade steer: `docs/design/phase-5-spring-boot-2.7-4.x.md`.

## Shared-library API breaks and Gortex settings (phase 6)

```text
qr gate api-compat --report '**/target/japicmp/*.xml'           # binary/source breaks from japicmp XML
qr gate api-compat --report build/japicmp.xml --level binary --ignore 'com.acme.internal.*'
qr gate api-compat --report target/japicmp/japicmp.xml --allow-major-bump --strict
qr init --graph gortex --workspace content-ingest \
  --workspace-dep content-model --module edu.acme:content-model   # embedding off, facade-v1, Java Kafka boundaries
```

`qr init --graph gortex` prints the install-time flags (`gortex install --hook-mode=enrich`, `gortex init --no-skills`) and never runs `gortex`. Why each setting: `research/harness-kb/implementations.md`.

Built test-first, with tests written by a separate agent and locked before implementation. The held-out tests ran by a third agent are in `tests/holdout/`. Criteria: `docs/design/phase-6-api-compat-and-gortex.md`. Lock: `.quality-router/acceptance.lock.json`.

## Layout

| Path | Role |
|------|------|
| `src/quality_router/` | CLI (`qr` / `quality-router`) |
| `AGENTS.md` | Invariants for agents in this tree |
| `docs/design/phase-1-cli.md` | Spec SoT for Phase 1 |
| `docs/design/phase-2-init.md` | Spec SoT for `qr init` |
| `docs/design/phase-3-harness.md` | Spec SoT for the harness gates |
| `docs/design/phase-4-acceptance-first-sdd.md` | Spec SoT for the acceptance-first Spec stage and the SDD steer |
| `docs/research/architecture-decisions.md` | C4 + three-job lock |
| `src/quality_router/harness/` | Gate, lint, spec, feedback, contracts, policy, eval commands |
| `examples/content-pipeline/` | Four-repo Java fixture + `run-demo.sh` |
| `research/harness-kb/` | Reviewed arXiv KB (May–Oct 2026) and `FINDINGS.md` |

Ollama is an optional model backend a host may **opt** at (`:11434`). Hermes (or any other agent runtime) may be the director on your machine; `qr` does not start the Ollama daemon, write LLM base URLs, or `hermes mcp serve`. Neither sits between the host and constituent MCPs.

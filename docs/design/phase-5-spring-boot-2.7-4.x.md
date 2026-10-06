# Phase 5: Spring Boot 2.7–4.x repos

Status: done. Branch `cursor/spring-boot-compat-5429`, on top of phase 4.

The content team's repos span Spring Boot 2.7 to 4.x. That range covers
three Java baselines, two servlet namespaces, two JUnit generations and two
test-module layouts. The phase-3 and phase-4 commands now work across all
of it. `qr` still never runs Maven or Gradle. It only reads build files
(`pom.xml`, `build.gradle(.kts)`) and build artifacts (JaCoCo XML, JUnit
XML).

## What the range means for the harness

| | Boot 2.7 | Boot 3.0–3.3 | Boot 3.4–3.5 | Boot 4.0 |
|---|---|---|---|---|
| Java baseline | 8 (often 8 or 11) | 17 | 17 | 17 (25 recommended) |
| Text blocks in tests | only on 15+ | yes | yes | yes |
| JUnit | Jupiter 5.8.x (JUnit 4 still managed) | Jupiter 5.9–5.10 | Jupiter 5.11+ | JUnit 6 |
| Servlet API | `javax` | `jakarta` | `jakarta` | `jakarta` |
| Mock beans | `@MockBean` | `@MockBean` | `@MockitoBean` (`@MockBean` deprecated) | `@MockitoBean` only |
| HTTP test clients | MockMvc, WebTestClient, TestRestTemplate | same | + MockMvcTester | + RestTestClient |
| `@AutoConfigureMockMvc` package | `org.springframework.boot.test.autoconfigure.web.servlet` | same | same | `org.springframework.boot.webmvc.test.autoconfigure` |

The two package rows were checked against the published jars
(spring-boot-test-autoconfigure 2.7.18, spring-boot-webmvc-test 4.0.8).

## Changes

| Command | Change for 2.7–4.x |
|---|---|
| `qr spec scaffold` | `--java-release N` (default: read from the nearest `pom.xml`/`build.gradle` above `--out`, else 17). Below 15 it writes `@CsvSource(value = {...})` instead of a text block. |
| | `--spring-boot-test`, `--class-annotation`, `--field`, `--import` let a bind call an injected bean or `MockMvc`. Test methods declare `throws Exception`. |
| | Fixes that apply to every version: cells containing `\|` are quoted (they were split), and cells starting with `#` are quoted (JUnit read the row as a comment and dropped the example without an error). A literal `(null)` string switches the table's null marker to `(nil)`, because JUnit maps `nullValues` even when the value is quoted. |
| `qr gate test-oracles` | Judges Spring web and reactive tests per chain. A status, content-type or `exists()` check on its own is weak. Asserting a body, value, header value, view or redirect is strong. Covers MockMvc `andExpect`/`andExpectAll`, WebTestClient/RestTestClient `expect*`, MockMvcTester AssertJ chains, Reactor `StepVerifier` and BDDMockito `then(x).should()`. |
| | Before this change, a MockMvc `jsonPath(...).value(...)` test scored "no assertion" and failed the gate. A status-only WebTestClient test and a `verifyComplete()`-only StepVerifier test both passed as strong, because `expect*`/`verify*` matched the custom-helper rule. |
| `qr gate diff-coverage` / `test-oracles` | Gradle test suites (`src/integrationTest/`, `src/functionalTest/`, …) and `src/testFixtures/` count as test code. |
| | REST Assured / RestAssuredMockMvc is judged after `.then()`: `statusCode`/`contentType` alone is weak; `body(path, matcher)` with a value matcher, a Spring `ResultMatcher` value check passed to `expect(...)`/`assertThat(...)`, or `expect(openApi().isValid(spec))` (swagger-request-validator), is strong. JUnit 4 `thrown.expect(X.class)` is an exception oracle. `assertTrue`/`assertFalse` on one boolean call of the code under test (`assertTrue(router.isBookOrganized())`) is strong, like AssertJ `isEmpty()`/`contains()`. Comparisons (`size() > 0`), bare variables and `!= null` stay weak. |
| `qr contracts diff` / `check` | Reads generated-OpenAPI YAML (springdoc, swagger-core, SnakeYAML output) with a strict stdlib loader. Anchors, tags, block scalars, flow collections and multi-document files fail with a line number instead of diffing wrongly. |
| `qr spec scaffold` | `--indent N` matches the repo formatter. The next-step hint says to format before `qr spec lock`, because reformatting after the lock fails `qr gate acceptance`. |
| `qr init --ci` | New `github-gradle` template next to `github-maven`. The JDK comes from `--ci-java`, else the build file, else 17. The Maven feedback step also reads Failsafe reports. Feedback uses `--sources .` so multi-module builds resolve. The header says which JaCoCo release supports the chosen JDK. |

## Binding acceptance tests in a Spring repo

The scaffolded test is always JUnit Jupiter. That runs on 2.7 (Jupiter is in
`spring-boot-starter-test`) and on 4.x (JUnit 6). Pick the cheapest layer
that reaches the criterion's output:

1. **Plain object** (no Spring context). Use this for pure normalization or
   mapping rules. It is the fastest and has no version coupling.

   ```text
   qr spec scaffold --spec specs/item-v2.md --package edu.acme.normalize \
     --bind '*=new Normalizer().normalize(raw(manifest)).licenseId()' \
     --out src/test/java/edu/acme/normalize/ItemV2AcceptanceTest.java
   ```

2. **Bean** (`@SpringBootTest`). Use this when the rule depends on
   configuration or wiring.

   ```text
   qr spec scaffold ... --spring-boot-test \
     --field '@Autowired ContentNormalizer normalizer' \
     --import edu.acme.normalize.ContentNormalizer \
     --bind '*=normalizer.normalize(raw(manifest)).licenseId()'
   ```

3. **HTTP** (MockMvc). Use this for delivery-API criteria. The
   `@AutoConfigureMockMvc` import differs by Boot version (see the table
   above). `qr` does not guess it.

   ```text
   qr spec scaffold ... --spring-boot-test --class-annotation '@AutoConfigureMockMvc' \
     --import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc \
     --import org.springframework.test.web.servlet.MockMvc \
     --import 'static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get' \
     --field '@Autowired MockMvc mvc' \
     --bind 'AC-5=mvc.perform(get("/items/{id}", id)).andReturn().getResponse().getContentAsString()'
   ```

   On Boot 4, import `org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc`
   instead.

## Verification

Every check below used real compilers and runtimes. Jars came from Maven
Central and were checked against the published SHA-1.

| Check | Result |
|---|---|
| 15-row CSV probe (empty, padded, `'`, `"`, `\`, `\|`, `#`, literal `(null)`, `"""`, trailing `\`, `,`) with an identity bind | 15/15 pass on JUnit 5.8.2 (Boot 2.7) at `--release` 8, 11 and 17, and on JUnit 6.0.1 and 6.1.3 (Boot 4) at 17 |
| The same probe before the fix | 14 tests from 15 rows (the `#` row was dropped); the `\|` row failed |
| `--spring-boot-test` + `@Autowired` bean bind | compiles against spring-boot-test 2.7.18 (release 8 and 11) and 4.0.8 (release 17) |
| MockMvc HTTP bind | compiles on Boot 2.7.18 / `javax.servlet` 4.0.1 (release 11, detected from `pom.xml`) and on Boot 4.0.8 / `jakarta.servlet` 6.1.0 |
| Text block at release 11 without detection | `javac` rejects it, which is the failure the detection prevents |
| CI templates | both render to valid YAML |
| Four-repo demo | unchanged: the agent's PR fails 5 of 7 gates, the review fix passes 7 of 7 |
| Unit tests | 376 pass, 99% coverage, ruff clean |

Not verified here: a full Spring application context at runtime (the
checks above compile against the annotation and test jars only), and the
Gradle template running in GitHub Actions.

## Steer for 2.7 → 3.x → 4.x upgrades

Evidence markers follow phase 4: **[E]** is evidence-backed, **[J]** is
engineering judgment.

- **[E]** Compiling is a poor proxy for behaviour after a framework
  migration. On ScarfBench the best agents reach about 15% behavioural pass
  on enterprise Java migrations, even when compile and deploy rates rise
  (2605.06754, mixed, low risk of bias). So gate upgrades on locked
  acceptance tests and contract tests, not on a green build.
- **[E]** For repo-wide API moves (`javax` → `jakarta`, `@MockBean` →
  `@MockitoBean`, the Boot 4 test-module split), have the agent write or
  choose a deterministic transformation (OpenRewrite recipe, JavaParser
  codemod) once. Verify it in one seed repo, then apply it in the others
  (2606.24446). The evidence is thin: 3 papers, about 40% end-to-end
  success.
- **[J]** Treat OpenRewrite as a licensing decision before it is a
  tooling one. As of 2026-10 the docs list `JUnit4to5Migration` under the
  Moderne Source Available License, served from an authenticated
  repository (`research/harness-kb/docs-checks.md`). If that is not
  approved, have the agent write a JavaParser codemod instead and verify
  it the same way.
- **[J]** Lock the acceptance tests before the upgrade, then run the
  upgrade as the "implementation". `qr gate acceptance` then shows the
  upgrade did not rewrite the oracle. Regenerate with `--java-release 17`
  only in a separate spec-only change after the Java bump, and re-lock it.
- **[J]** Upgrade provider repos before consumer repos, as in phase 3.
  The content contract is the seam, not the Boot version.

## Field check: a production Boot 2.7 service

One team service was inspected statically. It was not built, and none of its
code or names are in this repository. Profile: Boot 2.7.18 with Spring Cloud
2021.0.x, a Gradle 8.10 toolchain on Java 17, a single module, Error Prone with
`-Werror` on main and test compiles, and JaCoCo XML. It has 420 main and 176
test files (1,639 test methods). 174 of the test files are JUnit 4 run through
the vintage engine, and none use Jupiter. Controller tests use
RestAssuredMockMvc with swagger-request-validator against a committed
springdoc YAML spec (325 paths, 116 schemas). Integration tests share
`src/test` and are split out by package `exclude`/`include` in a second
`Test` task.

| Gate | Before | After |
|---|---|---|
| `--java-release` detection | 17 from `JavaLanguageVersion.of(17)` | unchanged |
| `test-oracles` (1,639 tests) | 267 none, 147 weak, 25 mock-only. The gate could not see REST Assured, `ExpectedException` or OpenAPI validation, so 266 of the "none" verdicts (16% of the suite) were tests that do assert | 1 none, 143 weak, 18 mock-only |
| `contracts diff` on the spec | refused (YAML) | parses identically to PyYAML. Removing one schema property reports `property_removed` on every response that embeds it |
| scaffolded Jupiter test, `--indent 2` | not tried | compiles with `javac -Xlint:all -Werror --release 17` and passes on JUnit 5.8.2 (Error Prone itself was not run) |

What the 143 weak tests are: 108 assert only the HTTP status through REST
Assured. A typical one is an update endpoint that asserts 200 and never checks
what was stored. The rest are `assertNotNull`, `size() > 0` or `assertNull`
on their own. These are the tests worth strengthening first.

Judgment call **[J]**: 106 tests are strong only because of
`openApi().isValid(spec)`, which checks that the response matches the
published contract but not its values. That is counted as strong because the
check fails on a wrong shape, a missing required field or an undeclared
status. A team that wants value oracles on every endpoint can wrap the
validator in a helper and leave it out of `--assert-helper`.

Steer for repos like this one:

- **[J]** Scaffolded acceptance tests are Jupiter and run next to the JUnit 4
  suite unchanged, because `spring-boot-starter-test` 2.7 brings Jupiter and
  the build already calls `useJUnitPlatform()`. Do not migrate the JUnit 4
  suite as part of SDD adoption. Lock new acceptance tests, then migrate
  with a deterministic recipe as a separate change (see the upgrade steer
  below).
- **[J]** Pass `--indent 2` (or whatever the house formatter uses). Format
  the file before `qr spec lock`; an IDE reformat after the lock fails the
  acceptance gate by design.
- **[J]** Point `qr contracts check` at the committed springdoc YAML. It is
  the delivery seam other repos read. It is also generated from a running
  app (`generateOpenApiDocs`), so CI should regenerate it and fail if the
  committed file differs. Otherwise a contract change can merge without
  showing up in the diff.
- **[J]** The stamped `github-gradle` workflow assumes a public dependency
  graph. In a repo that resolves from a private registry, add the `qr`
  steps to the existing build workflow after the test step, rather than
  running a second build.

## Known limits

- The oracle rules are lexical. A custom `ResultMatcher` or a helper that
  wraps `andExpect` counts as weak unless it is passed to `--assert-helper`.
  So does a REST Assured `then().spec(sharedSpec)`, because the spec's
  `expectBody(...)` is defined elsewhere.
- `--java-release` detection reads literal values, `${property}`
  indirection in the same pom, and common Gradle forms. It does not follow
  parent poms outside the repository, version catalogs or convention
  plugins. In those cases it says so and defaults to 17; pass the flag.
- JUnit 4-only Boot 2.7 modules (vintage engine with no Jupiter on the test
  classpath) need `junit-jupiter` added before scaffolded tests run.
- `contracts diff` reports a changed shared schema once per operation that
  embeds it. That is accurate, since each endpoint's readers break, but it
  is noisy: one removed field produced about 100 findings on the field-check
  spec.
- The YAML loader covers generator output only. A hand-written spec with
  anchors or flow style must be exported to JSON first.

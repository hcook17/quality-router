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
| Unit tests | 294 pass, 99% coverage, ruff clean |

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
- **[J]** Lock the acceptance tests before the upgrade, then run the
  upgrade as the "implementation". `qr gate acceptance` then shows the
  upgrade did not rewrite the oracle. Regenerate with `--java-release 17`
  only in a separate spec-only change after the Java bump, and re-lock it.
- **[J]** Upgrade provider repos before consumer repos, as in phase 3.
  The content contract is the seam, not the Boot version.

## Known limits

- The oracle rules are lexical. A custom `ResultMatcher` or a helper that
  wraps `andExpect` counts as weak unless it is passed to `--assert-helper`.
- `--java-release` detection reads literal values, `${property}`
  indirection in the same pom, and common Gradle forms. It does not follow
  parent poms outside the repository, version catalogs or convention
  plugins. In those cases it says so and defaults to 17; pass the flag.
- JUnit 4-only Boot 2.7 modules (vintage engine with no Jupiter on the test
  classpath) need `junit-jupiter` added before scaffolded tests run.

# Vendor-docs checks (separate tier from the paper KB)

Papers tell us which patterns hold up. Vendor docs tell us what an API
does in the version a team runs. This file holds only the second kind. It
is not adversarially reviewed like `reviews/`. Vendor docs have their own
bias (they document the happy path and the vendor's preferred tool), so
any claim that changes a gate is also checked against a real jar or
runtime where possible.

Source order: Context7 (the agent host's MCP; `qr` never caches or proxies
it, per `docs/research/architecture-decisions.md`), then the vendor's own
docs. On 2026-10-06 Context7 returned "Monthly quota exceeded" because no
`CONTEXT7_API_KEY` was configured, so the checks below used the vendor
pages directly.

| Claim the harness relies on | Source (fetched 2026-10-06) | Result | Effect |
|---|---|---|---|
| RestAssuredMockMvc accepts Spring `ResultMatcher`s via `then().assertThat(...)` and its alias `expect(...)` | REST Assured wiki, "Spring" (6.0.1) | Confirmed | `test-oracles` now judges `expect`/`assertThat` arguments in a REST Assured chain with the MockMvc rules. Before, `expect(jsonPath(..).value(..))` scored weak |
| `then().body(path, matcher)` and `body(matcher)` are the value checks | same | Confirmed | Matches the rule added after the field check |
| A response can be checked through a shared `ResponseSpecBuilder` (`then().spec(..)`) | same | Confirmed | Not followed lexically. Scores weak; listed as a known limit |
| A `#` at the start of a text-block row makes it a comment. A quoted `#` is not a comment. `value = {...}` arrays have no comments | JUnit 6.1.3 User Guide, `@CsvSource` | Confirmed | Matches the scaffold's quoting of leading `#` cells |
| `nullValues` also applies to quoted cells | same | Not stated | Behaviour taken from running JUnit 5.8.2 / 6.0.1 / 6.1.3 jars (phase 5). The scaffold's `(nil)` fallback stays |
| The vintage engine is deprecated and meant only for migration | JUnit 6.1.3 User Guide, overview | Confirmed | Supports "scaffold Jupiter tests and leave JUnit 4 alone during SDD adoption; migrate separately" |
| OpenRewrite `JUnit4to5Migration` converts `ExpectedException` → `assertThrows`, `@RunWith(Parameterized)` → `@ParameterizedTest`, and removes the vintage engine | docs.openrewrite.org recipe page | Confirmed | After migration those tests still pass `test-oracles` (`assertThrows` is strong) |
| OpenRewrite recipes are freely usable | same | **Changed.** The page lists the recipe under the Moderne Source Available License. Artifacts are served from an authenticated Code Genome Project repository; non-commercial use may build from source | The phase-5 upgrade steer now treats recipe tooling as a licensing and procurement decision, with a JavaParser codemod as the fallback |

## Queries to rerun through Context7 once a key is set

Put the key in the host environment or `~/.config/quality-router/secrets`,
never in `mcp.json`. Then ask the host agent for each of these. The table
above is the baseline to diff against.

1. REST Assured: `then()` `body`, `expect`, `assertThat` and `spec` on RestAssuredMockMvc.
2. JUnit 5.8 and 6.x: `@CsvSource` `nullValues` on quoted values.
3. Spring Boot 2.7 / 3.5 / 4.0: what `spring-boot-starter-test` brings (Jupiter, vintage), the `@MockBean` → `@MockitoBean` move, the 4.x test-module split, and the `MockMvcTester` / `RestTestClient` APIs.
4. swagger-request-validator: `OpenApiValidationMatchers.openApi().isValid` and the REST Assured filter.
5. springdoc-openapi Gradle plugin: `generateOpenApiDocs` output format and build-time generation.
6. JaCoCo: minimum release per JDK (used in the CI template header).
7. OpenRewrite: license and distribution of `rewrite-testing-frameworks` and `rewrite-spring`.

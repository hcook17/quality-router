# Phase 6: Java API compatibility gate and evidence-aligned Gortex settings

Status: in progress. Branch `cursor/japicmp-gortex-tdd-5429`, on top of the
KB contribution gate.

Contract: `src/quality_router/harness/report.py` (the gate result shape both
parts reuse; new module API in section A).

Problem: shared internal Java libraries cross the team's several repositories, and no
`qr` gate catches a binary or source break before a consumer pulls it. A
static API diff finds 95% of what LLM-written client tests catch on
dependency bumps (2608.20167). Separately, `qr init --graph gortex` writes a
`.gortex.yaml` that Gortex rejects (indented `cross_workspace_deps`, `module`
instead of `modules`, no `mode`) and none of the settings
`research/harness-kb/implementations.md` recommends.

Out of scope: running japicmp, Maven, Gradle or Gortex. Changing the CI
templates. Feign, `@HttpExchange` and AsyncAPI boundaries.

## How this phase is built

Tests are written before the code, by a different agent from the one that
implements, and are locked before implementation starts. The KB supports
separating test authorship from implementation and freezing the tests:
self-consistent wrong tests when the coding agent writes both (P15,
2608.16742), agents editing their own checks (2609.00069), hidden validators
catching what visible tests miss (2608.19799). TDD as a prompting style is
contested in the KB (P15: 2 supporting, 3 mixed); the separation and the
lock are what this phase relies on.

1. This spec, with numbered criteria and example tables. No code.
2. A test agent that sees only this spec and the existing public interfaces
   writes visible tests (committed) and a held-out set (not shown to the
   implementer, hashed when written).
3. The visible tests fail (red). They are locked with `qr spec lock`.
4. Implementation. Locked tests are not edited.
5. Gate: `qr gate acceptance` passes, a separate agent runs the held-out set
   and its hashes still match, coverage stays at or above 98.7%, ruff is
   clean.

## A. `qr gate api-compat`

Reads japicmp XML reports (the Maven plugin writes them under
`target/japicmp/`; the japicmp CLI writes one with `--xml-file`). The
element names follow japicmp's JAXB model: root `japicmp` with `oldVersion`
and `newVersion`; `classes/class[@fullyQualifiedName]`; members under
`methods/method`, `constructors/constructor`, `fields/field`, `superclass`,
`interfaces/interface`; each element may hold
`compatibilityChanges/compatibilityChange[@type @binaryCompatible
@sourceCompatible]`.

Module API (`quality_router.harness.api_compat`):

- `ApiCompatError(ValueError)`.
- `ApiChange`: frozen dataclass with `class_name`, `target`, `kind`
  (`class`, `method`, `constructor`, `field`, `superclass`, `interface`),
  `type`, `binary_compatible`, `source_compatible`.
- `JapicmpReport`: dataclass with `path`, `old_version`, `new_version`
  (`str | None`), `classes` (int), `changes` (`list[ApiChange]`, document
  order).
- `parse_japicmp(path: Path) -> JapicmpReport`; raises `ApiCompatError`.
- `run_api_compat(reports, cwd, level="both", ignore=(),
  allow_major_bump=False, strict=False) -> GateResult` with gate name
  `api-compat`.

### AC-1 Reports are named on the command line

`qr gate api-compat --report PATH` reads one japicmp XML report. `--report`
repeats and accepts globs relative to `--cwd` (default `.`), sorted per
pattern. Exit 0 pass, 1 gate failed, 2 usage error. A pattern that matches
nothing, or a path that is not a file, exits 2 with `Error: japicmp report
not found` on stderr and a second line naming how to produce one.

| argv | exit | stderr contains |
| --- | --- | --- |
| `--report target/japicmp/japicmp.xml` (compatible report) | 0 | (nothing) |
| `--report 'mods/*/target/japicmp/*.xml'` (two compatible reports) | 0 | (nothing) |
| `--report missing.xml` | 2 | `japicmp report not found` |
| `--report 'none/*.xml'` | 2 | `japicmp report not found` |

### AC-2 A file that is not a japicmp report is a usage error

Malformed XML, or a root element other than `japicmp`, exits 2. Stderr
contains `not a japicmp XML report` and the path. `parse_japicmp` raises
`ApiCompatError` for the same inputs.

| file content | exit |
| --- | --- |
| `<japicmp` (truncated) | 2 |
| `<report name="r"/>` (a JaCoCo report) | 2 |
| `<japicmp><classes/></japicmp>` | 0 |

### AC-3 Each compatibility change is reported once, at its owner

Every `compatibilityChange` element is one `ApiChange`. Its owner is the
nearest ancestor that is a `class`, `method`, `constructor`, `field`,
`superclass` or `interface` element; elements in between (`parameter`,
`returnType`, `annotation`, `exception`, …) are not owners. `class_name` is
the `fullyQualifiedName` of the nearest `class` ancestor (or the owner
itself). Aggregate `binaryCompatible`/`sourceCompatible` attributes on
classes and members are not changes. `target` is built from the owner;
parameter types are the `type` attributes of the owner's direct
`parameters/parameter` children, in order, joined by `,` with no spaces.

| owner | target |
| --- | --- |
| `class fullyQualifiedName="com.acme.Item"` | `com.acme.Item` |
| `method name="title"` with parameters `java.lang.String`, `int` | `com.acme.Item#title(java.lang.String,int)` |
| `method name="size"` with no parameters | `com.acme.Item#size()` |
| `constructor name="Item"` with parameter `java.lang.String` | `com.acme.Item#<init>(java.lang.String)` |
| `field name="id"` | `com.acme.Item#id` |
| `superclass` | `com.acme.Item#superclass` |
| `interface fullyQualifiedName="com.acme.Named"` | `com.acme.Item#interface:com.acme.Named` |
| `annotation` inside `method name="size"` | `com.acme.Item#size()` |

### AC-4 Compatibility flags fail closed

`type` is the change's `type` attribute, else its stripped text (older
japicmp), else `UNKNOWN`. Each flag is read from the change's own attribute
(`false` in any case means incompatible). When the change has no such
attribute, the owner's attribute is used. When neither has it, the change
counts as incompatible on that level.

| change | owner | binary_compatible | source_compatible |
| --- | --- | --- | --- |
| `type="METHOD_REMOVED" binaryCompatible="false" sourceCompatible="false"` | any | false | false |
| `type="METHOD_ADDED_TO_INTERFACE" binaryCompatible="true" sourceCompatible="false"` | any | true | false |
| text `METHOD_REMOVED`, no attributes | `binaryCompatible="false" sourceCompatible="true"` | false | true |
| text `METHOD_REMOVED`, no attributes | no flags | false | false |
| `type="FIELD_NOW_FINAL" binaryCompatible="FALSE"` | `sourceCompatible="true"` | false | true |

### AC-5 `--level` selects which breaks fail

`--level binary|source|both`, default `both`. A change is breaking when a
selected flag is false.

| binary_compatible | source_compatible | `--level` | breaking |
| --- | --- | --- | --- |
| false | false | both | yes |
| true | false | both | yes |
| true | false | binary | no |
| false | true | source | no |
| false | true | binary | yes |
| true | true | both | no |

### AC-6 Breaking changes are errors with a fixed message

Each breaking change adds an `error` finding. The code is
`api_binary_incompatible` when the level includes binary and the change is
binary-incompatible, else `api_source_incompatible`. The message is
`<type> <target> [<flags>]`, where flags lists every false flag as
`binary`, `source` or `binary,source`. `path` is the report path relative
to `--cwd` in POSIX form (the absolute path when outside it); `line` is 0.
Findings follow report order, then document order.

| change | `--level` | finding |
| --- | --- | --- |
| `METHOD_REMOVED` on `com.acme.Item#size()`, both false | both | `error api_binary_incompatible ... METHOD_REMOVED com.acme.Item#size() [binary,source]` |
| `METHOD_ADDED_TO_INTERFACE` on `com.acme.Named#name()`, source false | both | `error api_source_incompatible ... METHOD_ADDED_TO_INTERFACE com.acme.Named#name() [source]` |
| `FIELD_REMOVED` on `com.acme.Item#id`, both false | source | `error api_source_incompatible ... FIELD_REMOVED com.acme.Item#id [binary,source]` |

### AC-7 A removed class is one finding

When a class element has a breaking `CLASS_REMOVED` change, the other
changes inside that same class element add no finding. They are counted as
`collapsed`.

| class content | findings | collapsed |
| --- | --- | --- |
| `CLASS_REMOVED` plus two `METHOD_REMOVED` | 1 | 2 |
| two `METHOD_REMOVED`, no `CLASS_REMOVED` | 2 | 0 |

### AC-8 Compatible and out-of-level changes are counted, not reported

A change with both flags true adds no finding and counts in
`compatible_changes`. A change that is incompatible only on a level that
`--level` did not select adds no finding and counts in `excluded_by_level`.

| changes | `--level` | findings | compatible_changes | excluded_by_level |
| --- | --- | --- | --- | --- |
| `METHOD_ADDED_TO_PUBLIC_CLASS` (both true) | both | 0 | 1 | 0 |
| `METHOD_ADDED_TO_INTERFACE` (source false) | binary | 0 | 0 | 1 |

### AC-9 `--ignore` downgrades named classes to info

`--ignore GLOB` repeats. A breaking change whose `class_name` matches a
glob (case-sensitive `fnmatch`) adds an `info` finding with code
`api_change_ignored` and the AC-6 message, and counts in `ignored`. Info
findings never fail the gate.

| `--ignore` | change on | exit |
| --- | --- | --- |
| `com.acme.internal.*` | `com.acme.internal.Cache` | 0 |
| `com.acme.internal.*` | `com.acme.Item` | 1 |
| `*$Builder` | `com.acme.Item$Builder` | 0 |

### AC-10 `--allow-major-bump` turns breaks into warnings on a major bump

With `--allow-major-bump`, each report's `oldVersion` and `newVersion` are
read with `^v?(\d+)`. When both parse and the new major is greater,
breaking changes in that report are `warning` findings with the AC-6 code
and message, and count in `allowed_by_major_bump`. When either is missing
or does not parse, the report adds one `warning` `api_versions_unknown`
and its breaking changes stay errors. Without the flag, versions are not
read. `--strict` makes warnings fail.

| oldVersion | newVersion | flags | exit |
| --- | --- | --- | --- |
| `1.4.2` | `2.0.0` | `--allow-major-bump` | 0 |
| `1.4.2` | `2.0.0` | `--allow-major-bump --strict` | 1 |
| `1.4.2` | `1.5.0` | `--allow-major-bump` | 1 |
| (absent) | `2.0.0` | `--allow-major-bump` | 1 |
| `v1.0` | `v2.0-SNAPSHOT` | `--allow-major-bump` | 0 |
| `1.4.2` | `2.0.0` | (none) | 1 |

### AC-11 An empty report warns

A report with no `class` elements adds a `warning` `api_report_empty`
(often a wrong package include). The gate passes unless `--strict`.

| report | flags | exit |
| --- | --- | --- |
| `<japicmp><classes/></japicmp>` | (none) | 0 |
| `<japicmp><classes/></japicmp>` | `--strict` | 1 |

### AC-12 The summary has fixed keys

The result's summary has exactly these keys: `reports`, `classes`,
`breaking`, `binary_incompatible`, `source_incompatible`,
`compatible_changes`, `excluded_by_level`, `collapsed`, `ignored`,
`allowed_by_major_bump`, `level`. `classes` counts class elements.
`binary_incompatible` and `source_incompatible` count changes with that
flag false, excluding collapsed changes, whatever the level or ignores.
`breaking` counts breaking changes that are not collapsed and not ignored
(it includes `allowed_by_major_bump`). `--json` prints the standard gate
JSON with `"gate": "api-compat"`.

| report | summary |
| --- | --- |
| one class, `METHOD_REMOVED` (both false) and `METHOD_ADDED_TO_PUBLIC_CLASS` (both true) | `breaking=1 binary_incompatible=1 source_incompatible=1 compatible_changes=1 classes=1 reports=1 level=both` |

### AC-13 The gate is read-only

`qr gate api-compat` writes no file, starts no process and opens no network
connection.

| action | effect |
| --- | --- |
| run the gate in a directory | directory listing unchanged |
| run with `subprocess` and `socket` patched to raise | same result as unpatched |

### AC-14 Help shows the command

`qr gate api-compat --help` exits 0 and shows an example with `--report`.
`qr gate --help` lists `api-compat` in its examples.

| argv | stdout contains |
| --- | --- |
| `gate api-compat --help` | `--report` |
| `gate --help` | `qr gate api-compat` |

## B. `qr init --graph gortex`

Gortex keys are from `zzet/gortex` `internal/config/config.go`
(`cross_workspace_deps[].modules`, `mode: read-only` required;
`embedding.enabled`; `mcp.tools.preset`/`mode`; `index.event_bus` with
`name`, `type`, `callee`, `decorator`, `topic_arg`). Hook mode and skills
are install-time flags, so `qr` prints them; it never runs `gortex`.

Interfaces: `_write_gortex_config(cwd, workspace, deps)` returns
`"written"`, `"exists"` or `"disconnected"`. `run_init(config)` returns
that status, or `None` without `--graph gortex`. Invalid init input raises
`quality_router.init.InitError(ValueError)` before anything is written.
`InitConfig` and the `qr init` flags otherwise stay as they are; `--module`
becomes repeatable.

### AC-15 The stamped file holds the evidence-aligned settings

With `gortex` on PATH and no `--workspace-dep`, `.gortex.yaml` is exactly
the text below (workspace from `--workspace`, else the directory name).
Every user value is double-quoted.

| argv | `.gortex.yaml` |
| --- | --- |
| `init --graph gortex --workspace my-service` | the block below |

```yaml
# Written by `qr init --graph gortex`. qr never overwrites this file.
# Settings follow research/harness-kb/implementations.md (quality-router):
#   embedding off: embedding indexes are poisonable and localize Java poorly
#   facade-v1 in hide mode: about 15 inlined tools still select well
#   Java Kafka boundaries declared: Gortex does not detect them for Java
workspace: "my-service"
embedding:
  enabled: false
mcp:
  tools:
    preset: facade-v1
    mode: hide
index:
  event_bus:
    - name: kafka
      type: producer
      callee: kafkaTemplate.send
      topic_arg: "0"
    - name: kafka
      type: consumer
      decorator: KafkaListener
      topic_arg: topics
```

### AC-16 Cross-workspace dependencies are read-only module lists

Each `--workspace-dep` pairs with a `--module` by position. With zero
`--module` flags each dependency gets module `.`. Pairs with the same
workspace merge into one entry, modules in first-seen order, duplicates
dropped. Entries are in first-seen order. The block goes right after the
`workspace:` line:

```yaml
cross_workspace_deps:
  - workspace: "content-model"
    modules:
      - "edu.acme:content-model"
      - "edu.acme:content-events"
    mode: read-only
```

| argv deps | entries |
| --- | --- |
| `--workspace-dep a --module x` | `a: [x]` |
| `--workspace-dep a --module x --workspace-dep b --module y` | `a: [x]`, `b: [y]` |
| `--workspace-dep a --module x --workspace-dep a --module y --workspace-dep a --module x` | `a: [x, y]` |
| `--workspace-dep a --workspace-dep b` | `a: [.]`, `b: [.]` |

### AC-17 The file loads as the documented mapping

`quality_router.harness.yamlsubset.loads` reads the stamped file (block
style only, no flow collections) into the AC-15/AC-16 structure, with
`cross_workspace_deps` absent when there are no dependencies. The same
input always produces the same bytes.

| argv | loaded `cross_workspace_deps` |
| --- | --- |
| `init --graph gortex --workspace s` | key absent |
| `init --graph gortex --workspace s --workspace-dep a --module x` | `[{"workspace": "a", "modules": ["x"], "mode": "read-only"}]` |

### AC-18 Without gortex on PATH nothing is written

When `gortex` is not on PATH, no `.gortex.yaml` is written and `qr init`
exits 0. Stdout has the line `gortex_config=disconnected`. Stderr says
`gortex not on PATH` and names a signed package
(`brew install zzet/tap/gortex`); it never suggests `curl`, `| sh` or
`irm`.

| gortex on PATH | `.gortex.yaml` | stdout line |
| --- | --- | --- |
| no | absent | `gortex_config=disconnected` |
| yes | written | `gortex_config=written` |

### AC-19 An existing file is never overwritten

An existing `.gortex.yaml` stays byte-identical and stdout has
`gortex_config=exists`. When it has the shape older `qr` releases wrote (a
line that is an indented `cross_workspace_deps:`, or a `module:` key),
stderr also warns that it was written by an older qr and Gortex rejects
it, and says to delete it and re-run.

| existing file | stdout line | stderr contains |
| --- | --- | --- |
| `workspace: x\n` | `gortex_config=exists` | (no `older qr`) |
| `workspace: x\n  cross_workspace_deps:\n    - workspace: y\n      module: z\n` | `gortex_config=exists` | `older qr` |

### AC-20 Next steps are printed, never run

When the status is `written` or `exists`, stderr lists next steps
containing `gortex install --hook-mode=enrich`, `gortex init --no-skills`
and `jdtls`. `qr init` never starts a process for this.

| status | stderr contains | processes started |
| --- | --- | --- |
| written | `gortex install --hook-mode=enrich`, `gortex init --no-skills`, `jdtls` | 0 |
| exists | `gortex install --hook-mode=enrich` | 0 |
| disconnected | (no `--hook-mode`) | 0 |

### AC-21 Mismatched `--module` counts are usage errors

When the number of `--module` flags is neither 0 nor the number of
`--workspace-dep` flags, `qr init` exits 2 with `Error:` on stderr, and
writes nothing (no `.quality-router/` either). `--module` without
`--workspace-dep` is the same error.

| argv | exit |
| --- | --- |
| `--graph gortex --workspace-dep a --workspace-dep b --module x` | 2 |
| `--graph gortex --module x` | 2 |
| `--graph gortex --workspace-dep a --module x` | 0 |

### AC-22 Slugs and modules are validated before writing

With `--graph gortex`, `--workspace` and each `--workspace-dep` must match
`^[A-Za-z0-9][A-Za-z0-9._-]*$`, and each `--module` must match
`^[A-Za-z0-9._/@:-]+$`. A dependency equal to the workspace is an error.
These are checked whether or not `gortex` is on PATH. When `--workspace` is
absent and `gortex` is on PATH, the directory name must match the slug
rule. A failure exits 2 with `Error:` on stderr and writes nothing.

| argv | exit |
| --- | --- |
| `--graph gortex --workspace 'a: b'` | 2 |
| `--graph gortex --workspace 'x"\nmcp:'` | 2 |
| `--graph gortex --workspace s --workspace-dep s` | 2 |
| `--graph gortex --workspace-dep a --module 'x y'` | 2 |
| `--graph gortex --workspace edu-content.ingest_v2 --workspace-dep a --module 'edu.acme:model/v2@1'` | 0 |
| (directory `my repo`, gortex on PATH) `--graph gortex` | 2 |

### AC-23 Without `--graph gortex` the gortex step is silent

`qr init` without `--graph gortex` writes no `.gortex.yaml` and prints no
`gortex_config=` line, as before.

| argv | stdout contains `gortex_config=` |
| --- | --- |
| `init` | no |
| `init --host cursor` | no |

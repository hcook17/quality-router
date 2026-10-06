"""qr gate diff-coverage and qr gate test-oracles."""

from __future__ import annotations

from pathlib import Path

from quality_router.harness.coverage_gate import (
    _match_report,
    is_test_path,
    parse_jacoco,
    run_diff_coverage,
)
from quality_router.harness.javasrc import TestMethod
from quality_router.harness.oracles import classify, run_test_oracles

SERVICE = """\
package com.acme.ingest;

class Loader {
  int load(String id) {
    try {
      return fetch(id);
    } catch (IllegalStateException e) {
      return -1;
    }
  }
}
"""


def jacoco_xml(lines: dict[int, tuple[int, int, int, int]], pkg: str = "com/acme/ingest",
               name: str = "Loader.java") -> str:
    rows = "".join(f'<line nr="{nr}" mi="{mi}" ci="{ci}" mb="{mb}" cb="{cb}"/>'
                   for nr, (mi, ci, mb, cb) in lines.items())
    package = f'<package name="{pkg}">' if pkg else "<package>"
    return (f'<?xml version="1.0"?><report name="r">{package}'
            f'<sourcefile name="{name}">{rows}</sourcefile></package></report>')


def setup_module_tree(tmp_path: Path, lines: dict[int, tuple[int, int, int, int]],
                      module: str = "ingest") -> Path:
    src = tmp_path / module / "src/main/java/com/acme/ingest/Loader.java"
    src.parent.mkdir(parents=True)
    src.write_text(SERVICE, encoding="utf-8")
    xml = tmp_path / module / "target/site/jacoco/jacoco.xml"
    xml.parent.mkdir(parents=True)
    xml.write_text(jacoco_xml(lines), encoding="utf-8")
    return xml


class TestDiffCoverage:
    def test_catch_lines_reported_and_gated(self, tmp_path: Path) -> None:
        xml = setup_module_tree(tmp_path, {
            6: (0, 4, 1, 1),   # covered, half the branches
            7: (2, 0, 0, 0),   # catch line, missed
            8: (2, 0, 0, 0),   # catch body, missed
            11: (0, 0, 0, 0),  # not executable
        })
        report = parse_jacoco(xml, tmp_path)
        assert report.module_root == "ingest"
        changed = {"ingest/src/main/java/com/acme/ingest/Loader.java": {6, 7, 8, 11, 99},
                   "ingest/src/test/java/com/acme/LoaderTest.java": {1},
                   "README.md": {1}}
        result = run_diff_coverage(changed, [report], tmp_path, minimum=0.5, catch_minimum=0.5)
        codes = [f.code for f in result.findings]
        assert codes.count("uncovered_catch_line") == 2
        assert "partial_branch" in codes
        assert "diff_coverage_below_min" in codes and "catch_coverage_below_min" in codes
        assert result.summary["changed_executable_lines"] == 3
        assert result.summary["catch_lines"] == 2
        assert not result.passed

    def test_passes_and_warns_on_missing_data(self, tmp_path: Path) -> None:
        xml = setup_module_tree(tmp_path, {6: (0, 3, 0, 0), 4: (1, 0, 0, 0)})
        report = parse_jacoco(xml, tmp_path)
        changed = {"ingest/src/main/java/com/acme/ingest/Loader.java": {4, 6},
                   "other/src/main/java/com/acme/Other.java": {1}}
        result = run_diff_coverage(changed, [report], tmp_path, minimum=0.5, catch_minimum=None)
        assert result.passed
        assert [f.code for f in result.findings] == ["uncovered_line", "no_coverage_data"]
        assert result.findings[0].level == "info"

    def test_no_changes_is_full_coverage(self, tmp_path: Path) -> None:
        result = run_diff_coverage({}, [], tmp_path, minimum=0.9, catch_minimum=0.9)
        assert result.passed and result.summary["diff_coverage"] == 1.0

    def test_include_tests_and_missing_source_file(self, tmp_path: Path) -> None:
        xml = tmp_path / "jacoco.xml"
        xml.write_text(jacoco_xml({1: (0, 1, 0, 0)}, pkg="", name="T.java"), encoding="utf-8")
        report = parse_jacoco(xml, tmp_path)
        assert report.module_root == "" and "T.java" in report.lines
        result = run_diff_coverage({"src/test/java/T.java": {1}}, [report], tmp_path, 1.0, None,
                                   include_tests=True)
        assert result.summary["changed_covered_lines"] == 1

    def test_report_outside_cwd_and_module_disambiguation(self, tmp_path: Path) -> None:
        a = setup_module_tree(tmp_path, {6: (0, 1, 0, 0)}, module="a")
        b = setup_module_tree(tmp_path, {6: (1, 0, 0, 0)}, module="b")
        reports = [parse_jacoco(a, tmp_path), parse_jacoco(b, tmp_path)]
        match = _match_report("b/src/main/java/com/acme/ingest/Loader.java", reports)
        assert match is not None and match[0].module_root == "b"
        assert parse_jacoco(a, tmp_path / "elsewhere").module_root == ""

    def test_is_test_path(self) -> None:
        assert is_test_path("src/test/java/A.java")
        assert is_test_path("svc/src/it/java/A.java")
        assert not is_test_path("src/main/java/test/A.java")
        assert is_test_path("svc/src/integrationTest/java/A.java")
        assert is_test_path("src/testFixtures/java/A.java")
        assert not is_test_path("src/main/java/integrationTest/A.java")


def method(body: str, args: str = "") -> TestMethod:
    return TestMethod("t", 1, 1, body, args)


class TestOracleClassify:
    def test_strong_weak_mock_none(self) -> None:
        assert classify(method("assertEquals(1, f());")).kind == "strong"
        assert classify(method("assertNotNull(f());")).kind == "weak"
        assert classify(method("verify(repo).save(x);")).kind == "mock_only"
        assert classify(method("verifyNoMoreInteractions(repo);")).kind == "mock_only"
        assert classify(method("f();")).kind == "none"

    def test_assertj_chain_after_args(self) -> None:
        assert classify(method("assertThat(list).containsExactly(1, 2);")).kind == "strong"
        assert classify(method("assertThat(list.contains(1)).isTrue();")).kind == "weak"
        assert classify(method("assertThat(x)")).kind == "weak"

    def test_hamcrest_needs_matcher_argument(self) -> None:
        assert classify(method("assertThat(x, equalTo(3));")).kind == "strong"
        assert classify(method("assertThat(equalTo(3));")).kind == "weak"

    def test_exception_oracles_and_helpers(self) -> None:
        assert classify(method("f();", "(expected = IOException.class)")).kind == "strong"
        body = "try { f(); fail(\"x\"); } catch (IOException e) { }"
        assert classify(method(body)).kind == "strong"
        verdict = classify(method("assertItemValid(item);"))
        assert verdict.kind == "strong" and verdict.custom == 1
        helped = classify(method("checkItem(item);"), helpers=("checkItem",))
        assert helped.strong == 1 and helped.custom == 0

    def test_bdd_mockito_then_should_is_mock(self) -> None:
        assert classify(method("svc.run(); then(repo).should().save(any());")).kind == "mock_only"


def kind(body: str) -> str:
    return classify(method(body)).kind


class TestSpringOracles:
    """Spring Boot 2.7-4.x web and reactive test idioms (bodies are pre-blanked by javasrc)."""

    def test_mockmvc_status_only_is_weak(self) -> None:
        assert kind("mvc.perform(get( )).andExpect(status().isOk());") == "weak"
        assert kind("mvc.perform(get( )).andExpect(MockMvcResultMatchers.status().is(404));") \
            == "weak"
        assert kind("mvc.perform(get( )).andExpect(jsonPath( ).exists());") == "weak"
        assert kind("mvc.perform(get( ))"
                    ".andExpectAll(status().isOk(), content().contentType(JSON));") == "weak"

    def test_mockmvc_body_matchers_are_strong(self) -> None:
        assert kind("mvc.perform(get( )).andExpect(status().isOk())"
                    ".andExpect(jsonPath( ).value( ));") == "strong"
        assert kind("mvc.perform(get( )).andExpect(content().json( ));") == "strong"
        assert kind("mvc.perform(get( )).andExpectAll(status().isOk(), "
                    "jsonPath( , is( )));") == "strong"
        assert kind("mvc.perform(post( )).andExpect(redirectedUrl( ));") == "strong"

    def test_web_and_rest_test_client(self) -> None:
        assert kind("client.get().uri( ).exchange().expectStatus().isOk();") == "weak"
        assert kind("client.get().uri( ).exchange().expectStatus().isOk()"
                    ".expectBody().jsonPath( ).isEqualTo( );") == "strong"
        assert kind("client.get().exchange().expectBody(String.class).isEqualTo( );") == "strong"
        verdict = classify(method("client.get().exchange().expectBody(Item.class)"
                                  ".consumeWith(r -> { assertThat(r.id()).isEqualTo( ); });"))
        assert verdict.kind == "strong" and verdict.custom == 0

    def test_mockmvc_tester(self) -> None:
        assert kind("assertThat(mvc.get().uri( )).hasStatusOk();") == "weak"
        assert kind("assertThat(mvc.get().uri( )).hasStatusOk().bodyJson()"
                    ".extractingPath( ).isEqualTo( );") == "strong"
        assert kind("assertThat(mvc.get().uri( )).bodyJson().isLenientlyEqualTo( );") == "strong"

    def test_step_verifier(self) -> None:
        assert kind("StepVerifier.create(flux).verifyComplete();") == "weak"
        verdict = classify(method("StepVerifier.create(flux).expectNext( ).verifyComplete();"))
        assert verdict.kind == "strong" and verdict.custom == 0
        assert kind("flux.as(StepVerifier::create).expectNextCount(2).verifyComplete();") \
            == "strong"

    def test_context_loads_has_no_oracle(self) -> None:
        assert kind("") == "none"
        assert kind("if (x) { f(); }") == "none"


TEST_FILE = """\
package com.acme;

class LoaderTest {
  @Test
  void strong() {
    assertEquals(1, load());
  }

  @Test
  void weak() {
    assertNotNull(load());
  }

  @Test
  void mocked() {
    verify(repo).save(any());
  }

  @Test
  void nothing() {
    load();
  }

  @Test
  void custom() {
    assertLoaded(load());
  }
}
"""


class TestOracleGate:
    def test_changed_lines_select_methods(self, tmp_path: Path) -> None:
        path = tmp_path / "src/test/java/com/acme/LoaderTest.java"
        path.parent.mkdir(parents=True)
        path.write_text(TEST_FILE, encoding="utf-8")
        rel = "src/test/java/com/acme/LoaderTest.java"
        result = run_test_oracles({rel: {11}, "README.md": {1}, "src/test/java/Gone.java": {1},
                                   "src/main/java/Main.java": {1}}, tmp_path)
        assert [f.code for f in result.findings] == ["weak_oracle"]
        assert result.summary["tests_checked"] == 1

        mains = tmp_path / "src/main/java/Main.java"
        mains.parent.mkdir(parents=True)
        mains.write_text(TEST_FILE, encoding="utf-8")
        assert run_test_oracles({"src/main/java/Main.java": {11}}, tmp_path).summary[
            "tests_checked"] == 0

    def test_whole_file_mode_and_allow_weak(self, tmp_path: Path) -> None:
        path = tmp_path / "LoaderTest.java"
        path.write_text(TEST_FILE, encoding="utf-8")
        result = run_test_oracles({"LoaderTest.java": None}, tmp_path, allow_weak=True)
        levels = {f.code: f.level for f in result.findings}
        assert levels == {"weak_oracle": "warning", "mock_only_oracle": "error",
                          "none_oracle": "error", "custom_assertion": "info"}
        assert result.summary["tests_strong"] == 2
        assert not result.passed

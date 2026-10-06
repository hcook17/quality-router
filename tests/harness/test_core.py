"""report, gitdiff and javasrc: shared plumbing for the harness gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.harness.gitdiff import git_diff, load_diff, parse_unified_diff
from quality_router.harness.javasrc import (
    blank_strings_and_comments,
    catch_block_lines,
    line_lookup,
    matching_brace,
)
from quality_router.harness.javasrc import (
    test_methods as find_test_methods,
)
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, Finding, GateResult


class TestReport:
    def test_finding_render_variants(self) -> None:
        assert Finding("error", "x", "msg").render() == "error x msg"
        assert Finding("info", "x", "msg", "a.java").render() == "info x a.java msg"
        assert Finding("warning", "x", "msg", "a.java", 3).render() == "warning x a.java:3 msg"

    def test_strict_turns_warnings_into_failure(self) -> None:
        result = GateResult(gate="g")
        result.add("warning", "w", "careful")
        assert result.passed and result.exit_code() == EXIT_PASS
        result.strict = True
        assert not result.passed and result.exit_code() == EXIT_FAIL

    def test_text_render_includes_summary_scalars(self) -> None:
        result = GateResult(gate="g", summary={"ratio": 0.5, "items": [1], "n": 3})
        result.add("error", "e", "bad")
        text = result.render(as_json=False)
        assert "error e bad" in text
        assert "ratio=0.5000" in text and "items=[1]" in text and "n=3" in text
        assert text.endswith("gate=g result=fail errors=1 warnings=0\n")

    def test_json_render(self) -> None:
        result = GateResult(gate="g")
        result.add("info", "i", "note", "p", 2)
        payload = json.loads(result.render(as_json=True))
        assert payload["passed"] is True
        assert payload["findings"][0] == {"level": "info", "code": "i", "message": "note",
                                          "path": "p", "line": 2}


DIFF = """\
diff --git a/src/A.java b/src/A.java
index 1..2 100644
--- a/src/A.java
+++ b/src/A.java
@@ -1,3 +1,4 @@
 keep
-gone
+new1
+new2
 keep
\\ No newline at end of file
@@ -10 +11,0 @@
-only removed
diff --git a/old.txt b/old.txt
--- a/old.txt
+++ /dev/null
@@ -1 +0,0 @@
-x
diff --git a/B.java b/B.java
--- /dev/null
+++ B.java\t2026-01-01
@@ -0,0 +1 @@
+hello
"""


class TestGitDiff:
    def test_parse_added_lines(self) -> None:
        assert parse_unified_diff(DIFF) == {"src/A.java": {2, 3}, "B.java": {1}}

    def test_lines_before_any_hunk_are_ignored(self) -> None:
        assert parse_unified_diff("+++ b/x\n+stray\n") == {}

    def test_load_diff_sources(self, tmp_path: Path) -> None:
        diff_file = tmp_path / "pr.diff"
        diff_file.write_text(DIFF, encoding="utf-8")
        assert load_diff(str(diff_file), None, tmp_path, None)["B.java"] == {1}
        assert load_diff("-", None, tmp_path, DIFF)["B.java"] == {1}
        assert load_diff("-", None, tmp_path, None) == {}
        with pytest.raises(ValueError):
            load_diff(None, None, tmp_path, None)

    def test_git_diff_against_base(self, repo: Path) -> None:
        (repo / "A.java").write_text("a\n", encoding="utf-8")
        (repo / "notes.md").write_text("n\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "base")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "A.java").write_text("a\nb\n", encoding="utf-8")
        (repo / "notes.md").write_text("n\nm\n", encoding="utf-8")
        git(repo, "commit", "-qam", "change")
        assert load_diff(None, base, repo, None, ["*.java"]) == {"A.java": {2}}
        assert "notes.md" in git_diff(base, repo)

    def test_git_diff_bad_base(self, repo: Path) -> None:
        with pytest.raises(RuntimeError):
            git_diff("does-not-exist", repo)


JAVA = """\
class X {
  // a comment with { brace
  String s = "a { \\" } brace";
  char c = '{';
  /* block
     { */
  void run() {
    try {
      go();
    } catch (IOException e) {
      log("x");
    }
  }
}
"""


class TestJavaSource:
    def test_blanking_preserves_offsets_and_newlines(self) -> None:
        blanked = blank_strings_and_comments(JAVA)
        assert len(blanked) == len(JAVA)
        assert blanked.count("\n") == JAVA.count("\n")
        assert "brace" not in blanked
        assert blanked.count("{") == blanked.count("}")

    def test_unterminated_comment_and_string(self) -> None:
        assert blank_strings_and_comments("a /* open").strip() == "a"
        assert blank_strings_and_comments('x "open').strip() == "x"
        assert blank_strings_and_comments("x // tail").strip() == "x"

    def test_line_lookup(self) -> None:
        line_of = line_lookup("a\nb\nc")
        assert [line_of(0), line_of(2), line_of(4)] == [1, 2, 3]

    def test_matching_brace_unbalanced(self) -> None:
        assert matching_brace("{ {", 0) == 2

    def test_catch_block_lines(self) -> None:
        assert catch_block_lines(JAVA) == {10, 11, 12}
        assert catch_block_lines("catch (E e)") == set()

    def test_test_methods_handles_annotation_arrays_and_fqcn(self) -> None:
        source = """\
class T {
  @ParameterizedTest
  @ValueSource(strings = {"a", "b"})
  void one(String s) {
    assertEquals(1, 1);
  }

  @org.junit.jupiter.api.Test(timeout = 5)
  public void two() throws Exception { x(); }

  @Test
  abstract void three();

  @Test
  int field = 3;
}
"""
        methods = find_test_methods(source)
        assert [m.name for m in methods] == ["one", "two"]
        assert (methods[0].start_line, methods[0].end_line) == (2, 6)
        assert "assertEquals" in methods[0].body
        assert methods[1].annotation_args == "(timeout = 5)"

    def test_unterminated_signature(self) -> None:
        assert find_test_methods("@Test void open(") == []

"""Phase 6 section A: `qr gate api-compat` over japicmp XML reports (AC-1 .. AC-14).

Spec: docs/design/phase-6-api-compat-and-gortex.md. The fixtures follow japicmp's
JAXB element names and carry aggregate binaryCompatible/sourceCompatible
attributes on classes and members, which are not changes (AC-3).
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import os
import socket
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

from quality_router.cli import run
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE, GateResult

REPORT = "target/japicmp/japicmp.xml"
SUMMARY_KEYS = {
    "reports", "classes", "breaking", "binary_incompatible", "source_incompatible",
    "compatible_changes", "excluded_by_level", "collapsed", "ignored",
    "allowed_by_major_bump", "level",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def api() -> ModuleType:
    return importlib.import_module("quality_router.harness.api_compat")


def qr(*argv: str) -> int:
    try:
        return run(list(argv))
    except SystemExit as exc:
        if exc.code is None:
            return EXIT_PASS
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE


def gate(cwd: Path, *argv: str) -> int:
    return qr("gate", "api-compat", "--cwd", str(cwd), *argv)


def gate_json(cwd: Path, capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict]:
    code = gate(cwd, *argv, "--json")
    out = capsys.readouterr().out
    return code, json.loads(out)


def _flag(value: bool | str) -> str:
    return value if isinstance(value, str) else str(value).lower()


def flags(binary: bool | str | None = None, source: bool | str | None = None) -> str:
    out = ""
    if binary is not None:
        out += f' binaryCompatible="{_flag(binary)}"'
    if source is not None:
        out += f' sourceCompatible="{_flag(source)}"'
    return out


def change(type_: str | None, binary: bool | str | None = None,
           source: bool | str | None = None, *, text: str | None = None) -> str:
    attrs = (f' type="{type_}"' if type_ else "") + flags(binary, source)
    if text is not None:
        return f"<compatibilityChange{attrs}>{text}</compatibilityChange>"
    return f"<compatibilityChange{attrs}/>"


def changes(*items: str) -> str:
    if not items:
        return "<compatibilityChanges/>"
    return "<compatibilityChanges>" + "".join(items) + "</compatibilityChanges>"


def parameters(*types: str) -> str:
    if not types:
        return "<parameters/>"
    return ("<parameters>" + "".join(
        f'<parameter type="{t}"><annotations/></parameter>' for t in types) + "</parameters>")


def method(name: str, *chg: str, params: tuple[str, ...] = (), binary: bool | None = True,
           source: bool | None = True, status: str = "UNCHANGED",
           annotations: str = "<annotations/>") -> str:
    return (f'<method name="{name}" changeStatus="{status}"{flags(binary, source)}'
            f' returnType="void">{annotations}{changes(*chg)}<exceptions/>'
            f"{parameters(*params)}"
            '<returnType changeStatus="UNCHANGED" oldValue="void" newValue="void">'
            "<compatibilityChanges/></returnType></method>")


def constructor(name: str, *chg: str, params: tuple[str, ...] = (), binary: bool = True,
                source: bool = True, status: str = "UNCHANGED") -> str:
    return (f'<constructor name="{name}" changeStatus="{status}"{flags(binary, source)}>'
            f"<annotations/>{changes(*chg)}<exceptions/>{parameters(*params)}</constructor>")


def field(name: str, *chg: str, binary: bool | None = True, source: bool | None = True,
          status: str = "UNCHANGED") -> str:
    return (f'<field name="{name}" changeStatus="{status}"{flags(binary, source)}'
            f' type="java.lang.String"><annotations/>{changes(*chg)}</field>')


def interface(fqn: str, *chg: str, binary: bool = True, source: bool = True,
              status: str = "UNCHANGED") -> str:
    return (f'<interface fullyQualifiedName="{fqn}" changeStatus="{status}"'
            f"{flags(binary, source)}>{changes(*chg)}</interface>")


def superclass(*chg: str, binary: bool = True, source: bool = True,
               status: str = "UNCHANGED") -> str:
    return (f'<superclass changeStatus="{status}" superclassOld="com.acme.Base"'
            f' superclassNew="com.acme.Base"{flags(binary, source)}>{changes(*chg)}'
            "</superclass>")


def _wrap(tag: str, items: tuple[str, ...] | list[str]) -> str:
    return f"<{tag}>{''.join(items)}</{tag}>" if items else f"<{tag}/>"


def klass(fqn: str, *, chg: tuple[str, ...] = (), methods: tuple[str, ...] = (),
          constructors: tuple[str, ...] = (), fields: tuple[str, ...] = (),
          interfaces: tuple[str, ...] = (), superclass_: str | None = None,
          binary: bool = True, source: bool = True, status: str = "MODIFIED") -> str:
    sup = superclass_ if superclass_ is not None else superclass()
    return (f'<class fullyQualifiedName="{fqn}" changeStatus="{status}" type="CLASS"'
            f'{flags(binary, source)}><annotations/><attributes/>'
            '<classType changeStatus="UNCHANGED" oldType="CLASS" newType="CLASS"/>'
            f"{changes(*chg)}{_wrap('constructors', constructors)}"
            f"{_wrap('fields', fields)}{_wrap('interfaces', interfaces)}"
            f"{_wrap('methods', methods)}<modifiers/>{sup}</class>")


def japicmp(*classes: str, old: str | None = "1.4.2", new: str | None = "1.5.0") -> str:
    versions = (f' oldVersion="{old}"' if old is not None else "") + (
        f' newVersion="{new}"' if new is not None else "")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<japicmp oldJar="lib-old.jar" newJar="lib-new.jar"{versions}'
            ' accessModifier="PROTECTED" onlyModifications="false"'
            ' onlyBinaryIncompatibleModifications="false">'
            f"{_wrap('classes', classes)}</japicmp>\n")


def put(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def compatible_report() -> str:
    return japicmp(klass(
        "com.acme.Item",
        methods=(
            method("title", params=("java.lang.String",)),
            method("slug", change("METHOD_ADDED_TO_PUBLIC_CLASS", True, True),
                   status="NEW"),
        ),
        fields=(field("id"),),
    ))


def item_with(*member_methods: str, binary: bool = False, source: bool = False) -> str:
    """One class com.acme.Item with the given methods plus unchanged members."""
    return japicmp(klass(
        "com.acme.Item",
        methods=(method("hashCode"), *member_methods),
        fields=(field("id"),),
        binary=binary, source=source,
    ))


def removed_size() -> str:
    return method("size", change("METHOD_REMOVED", False, False),
                  binary=False, source=False, status="REMOVED")


# --------------------------------------------------------------------------- #
# AC-1
# --------------------------------------------------------------------------- #

class TestAC1ReportsOnCommandLine:
    """AC-1: --report names japicmp XML reports; globs relative to --cwd; missing -> exit 2."""

    def test_single_compatible_report_passes(self, tmp_path: Path, capsys) -> None:
        """AC-1: `--report target/japicmp/japicmp.xml` (compatible) exits 0, empty stderr."""
        put(tmp_path, REPORT, compatible_report())
        assert gate(tmp_path, "--report", REPORT) == EXIT_PASS
        assert capsys.readouterr().err == ""

    def test_glob_two_compatible_reports(self, tmp_path: Path, capsys) -> None:
        """AC-1: a glob relative to --cwd reads every matching report."""
        put(tmp_path, "mods/a/target/japicmp/japicmp.xml", compatible_report())
        put(tmp_path, "mods/b/target/japicmp/japicmp.xml", compatible_report())
        code, payload = gate_json(tmp_path, capsys, "--report", "mods/*/target/japicmp/*.xml")
        assert code == EXIT_PASS
        assert payload["summary"]["reports"] == 2
        assert capsys.readouterr().err == ""

    def test_default_cwd_is_current_directory(self, tmp_path: Path, monkeypatch,
                                              capsys) -> None:
        """AC-1: --cwd defaults to `.`."""
        put(tmp_path, REPORT, compatible_report())
        monkeypatch.chdir(tmp_path)
        assert qr("gate", "api-compat", "--report", REPORT) == EXIT_PASS
        assert capsys.readouterr().err == ""

    def test_repeated_report_flag(self, tmp_path: Path, capsys) -> None:
        """AC-1: --report repeats."""
        put(tmp_path, "one.xml", compatible_report())
        put(tmp_path, "two.xml", compatible_report())
        code, payload = gate_json(tmp_path, capsys, "--report", "one.xml", "--report", "two.xml")
        assert code == EXIT_PASS
        assert payload["summary"]["reports"] == 2

    @pytest.mark.parametrize("pattern", ["missing.xml", "none/*.xml"])
    def test_missing_report_is_usage_error(self, pattern: str, tmp_path: Path, capsys) -> None:
        """AC-1: a missing path or an empty glob exits 2 with a how-to second line."""
        assert gate(tmp_path, "--report", pattern) == EXIT_USAGE
        err = capsys.readouterr().err
        assert "Error: japicmp report not found" in err
        lines = [line for line in err.splitlines() if line.strip()]
        assert len(lines) >= 2

    def test_directory_is_not_a_file(self, tmp_path: Path, capsys) -> None:
        """AC-1: a path that is not a file exits 2 with `japicmp report not found`."""
        (tmp_path / "target" / "japicmp").mkdir(parents=True)
        assert gate(tmp_path, "--report", "target/japicmp") == EXIT_USAGE
        assert "japicmp report not found" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# AC-2
# --------------------------------------------------------------------------- #

NOT_JAPICMP = [
    pytest.param("<japicmp", id="truncated"),
    pytest.param('<report name="r"/>', id="jacoco-root"),
]


class TestAC2NotAJapicmpReport:
    """AC-2: malformed XML or a non-`japicmp` root is a usage error (exit 2)."""

    @pytest.mark.parametrize("content", NOT_JAPICMP)
    def test_cli_exit_2(self, content: str, tmp_path: Path, capsys) -> None:
        """AC-2: stderr names `not a japicmp XML report` and the path."""
        put(tmp_path, "bad.xml", content)
        assert gate(tmp_path, "--report", "bad.xml") == EXIT_USAGE
        err = capsys.readouterr().err
        assert "not a japicmp XML report" in err
        assert "bad.xml" in err

    @pytest.mark.parametrize("content", NOT_JAPICMP)
    def test_parse_raises(self, content: str, tmp_path: Path) -> None:
        """AC-2: parse_japicmp raises ApiCompatError (a ValueError) for the same inputs."""
        mod = api()
        assert issubclass(mod.ApiCompatError, ValueError)
        path = put(tmp_path, "bad.xml", content)
        with pytest.raises(mod.ApiCompatError):
            mod.parse_japicmp(path)

    def test_empty_japicmp_is_accepted(self, tmp_path: Path) -> None:
        """AC-2: `<japicmp><classes/></japicmp>` exits 0."""
        put(tmp_path, "ok.xml", "<japicmp><classes/></japicmp>")
        assert gate(tmp_path, "--report", "ok.xml") == EXIT_PASS
        report = api().parse_japicmp(tmp_path / "ok.xml")
        assert report.classes == 0
        assert report.changes == []


# --------------------------------------------------------------------------- #
# AC-3
# --------------------------------------------------------------------------- #

def owners_report() -> str:
    deprecated = ('<annotations><annotation fullyQualifiedName="java.lang.Deprecated"'
                  ' changeStatus="NEW" binaryCompatible="true" sourceCompatible="true">'
                  + changes(change("ANNOTATION_DEPRECATED_ADDED", True, True))
                  + "<elements/></annotation></annotations>")
    item = klass(
        "com.acme.Item",
        chg=(change("CLASS_NOW_ABSTRACT", False, False),),
        methods=(
            method("title", change("METHOD_NOW_FINAL", False, False),
                   params=("java.lang.String", "int"), binary=False, source=False,
                   status="MODIFIED"),
            method("size", change("METHOD_REMOVED", False, False), binary=False,
                   source=False, status="REMOVED", annotations=deprecated),
            method("hashCode"),
        ),
        constructors=(
            constructor("Item", change("CONSTRUCTOR_REMOVED", False, False),
                        params=("java.lang.String",), binary=False, source=False,
                        status="REMOVED"),
            constructor("Item"),
        ),
        fields=(field("id", change("FIELD_REMOVED", False, False), binary=False,
                      source=False, status="REMOVED"), field("name")),
        superclass_=superclass(change("SUPERCLASS_REMOVED", False, False), binary=False,
                               source=False, status="MODIFIED"),
        interfaces=(interface("com.acme.Named", change("INTERFACE_REMOVED", False, False),
                              binary=False, source=False, status="REMOVED"),
                    interface("java.io.Serializable")),
        binary=False, source=False,
    )
    other = klass("com.acme.Other", status="UNCHANGED",
                  methods=(method("run"),), fields=(field("x"),))
    return japicmp(item, other)


OWNER_ROWS = [
    ("class", "com.acme.Item", "CLASS_NOW_ABSTRACT"),
    ("method", "com.acme.Item#title(java.lang.String,int)", "METHOD_NOW_FINAL"),
    ("method", "com.acme.Item#size()", "METHOD_REMOVED"),
    ("constructor", "com.acme.Item#<init>(java.lang.String)", "CONSTRUCTOR_REMOVED"),
    ("field", "com.acme.Item#id", "FIELD_REMOVED"),
    ("superclass", "com.acme.Item#superclass", "SUPERCLASS_REMOVED"),
    ("interface", "com.acme.Item#interface:com.acme.Named", "INTERFACE_REMOVED"),
    ("method", "com.acme.Item#size()", "ANNOTATION_DEPRECATED_ADDED"),
]


class TestAC3ChangeReportedOnceAtOwner:
    """AC-3: each compatibilityChange is one ApiChange at its nearest owner element."""

    @pytest.mark.parametrize(("kind", "target", "type_"), OWNER_ROWS)
    def test_owner_target(self, kind: str, target: str, type_: str, tmp_path: Path) -> None:
        """AC-3: target is built from the owner (table rows)."""
        report = api().parse_japicmp(put(tmp_path, REPORT, owners_report()))
        matches = [c for c in report.changes if c.type == type_]
        assert len(matches) == 1
        assert matches[0].kind == kind
        assert matches[0].target == target
        assert matches[0].class_name == "com.acme.Item"

    def test_full_change_list_in_document_order(self, tmp_path: Path) -> None:
        """AC-3: aggregate attributes are not changes; changes keep document order."""
        mod = api()
        path = put(tmp_path, REPORT, owners_report())
        report = mod.parse_japicmp(path)

        def c(target: str, kind: str, type_: str, binary: bool, source: bool):
            return mod.ApiChange(class_name="com.acme.Item", target=target, kind=kind,
                                 type=type_, binary_compatible=binary,
                                 source_compatible=source)

        assert report.changes == [
            c("com.acme.Item", "class", "CLASS_NOW_ABSTRACT", False, False),
            c("com.acme.Item#<init>(java.lang.String)", "constructor", "CONSTRUCTOR_REMOVED",
              False, False),
            c("com.acme.Item#id", "field", "FIELD_REMOVED", False, False),
            c("com.acme.Item#interface:com.acme.Named", "interface", "INTERFACE_REMOVED",
              False, False),
            c("com.acme.Item#title(java.lang.String,int)", "method", "METHOD_NOW_FINAL",
              False, False),
            c("com.acme.Item#size()", "method", "ANNOTATION_DEPRECATED_ADDED", True, True),
            c("com.acme.Item#size()", "method", "METHOD_REMOVED", False, False),
            c("com.acme.Item#superclass", "superclass", "SUPERCLASS_REMOVED", False, False),
        ]
        assert report.classes == 2
        assert report.old_version == "1.4.2"
        assert report.new_version == "1.5.0"
        assert Path(report.path) == path

    def test_api_change_is_frozen(self, tmp_path: Path) -> None:
        """AC-3: ApiChange is a frozen dataclass."""
        report = api().parse_japicmp(put(tmp_path, REPORT, owners_report()))
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.changes[0].target = "x"  # type: ignore[misc]

    def test_method_without_parameters(self, tmp_path: Path) -> None:
        """AC-3: `method name="size"` with no parameters -> `com.acme.Item#size()`."""
        report = api().parse_japicmp(put(tmp_path, REPORT, item_with(removed_size())))
        assert [c.target for c in report.changes] == ["com.acme.Item#size()"]


# --------------------------------------------------------------------------- #
# AC-4
# --------------------------------------------------------------------------- #

FLAG_ROWS = [
    pytest.param(change("METHOD_REMOVED", "false", "false"), (True, True),
                 "METHOD_REMOVED", False, False, id="own-flags-both-false"),
    pytest.param(change("METHOD_ADDED_TO_INTERFACE", "true", "false"), (False, False),
                 "METHOD_ADDED_TO_INTERFACE", True, False, id="own-flags-win-over-owner"),
    pytest.param(change(None, text="METHOD_REMOVED"), (False, True),
                 "METHOD_REMOVED", False, True, id="text-form-owner-flags"),
    pytest.param(change(None, text="METHOD_REMOVED"), (None, None),
                 "METHOD_REMOVED", False, False, id="text-form-no-flags-fail-closed"),
    pytest.param(change("FIELD_NOW_FINAL", "FALSE"), (None, True),
                 "FIELD_NOW_FINAL", False, True, id="uppercase-false-plus-owner-source"),
]


class TestAC4FlagsFailClosed:
    """AC-4: type from attribute/text/UNKNOWN; flags from change, then owner, else false."""

    @pytest.mark.parametrize(("chg", "owner", "type_", "binary", "source"), FLAG_ROWS)
    def test_flag_rows(self, chg: str, owner: tuple[bool | None, bool | None], type_: str,
                       binary: bool, source: bool, tmp_path: Path) -> None:
        """AC-4: example table rows."""
        if type_ == "FIELD_NOW_FINAL":
            owner_xml = field("id", chg, binary=owner[0], source=owner[1], status="MODIFIED")
            xml = japicmp(klass("com.acme.Item", fields=(owner_xml,)))
        else:
            owner_xml = method("size", chg, binary=owner[0], source=owner[1],
                               status="MODIFIED")
            xml = japicmp(klass("com.acme.Item", methods=(owner_xml, method("hashCode"))))
        report = api().parse_japicmp(put(tmp_path, REPORT, xml))
        assert len(report.changes) == 1
        got = report.changes[0]
        assert (got.type, got.binary_compatible, got.source_compatible) == (
            type_, binary, source)

    def test_type_unknown_when_no_attribute_or_text(self, tmp_path: Path) -> None:
        """AC-4: no type attribute and no text -> `UNKNOWN`."""
        xml = item_with(method("size", change(None, False, False), status="MODIFIED"))
        report = api().parse_japicmp(put(tmp_path, REPORT, xml))
        assert [c.type for c in report.changes] == ["UNKNOWN"]

    def test_text_type_is_stripped(self, tmp_path: Path) -> None:
        """AC-4: older japicmp text form is stripped."""
        xml = item_with(method("size", change(None, False, False, text="\n  METHOD_REMOVED \n"),
                               status="REMOVED"))
        report = api().parse_japicmp(put(tmp_path, REPORT, xml))
        assert [c.type for c in report.changes] == ["METHOD_REMOVED"]


# --------------------------------------------------------------------------- #
# AC-5
# --------------------------------------------------------------------------- #

LEVEL_ROWS = [
    (False, False, "both", True),
    (True, False, "both", True),
    (True, False, "binary", False),
    (False, True, "source", False),
    (False, True, "binary", True),
    (True, True, "both", False),
]


class TestAC5LevelSelectsBreaks:
    """AC-5: --level binary|source|both (default both); breaking when a selected flag is false."""

    @pytest.mark.parametrize(("binary", "source", "level", "breaking"), LEVEL_ROWS)
    def test_level_rows(self, binary: bool, source: bool, level: str, breaking: bool,
                        tmp_path: Path, capsys) -> None:
        """AC-5: example table rows."""
        xml = item_with(method("size", change("METHOD_CHANGED", binary, source),
                               binary=binary, source=source, status="MODIFIED"))
        put(tmp_path, REPORT, xml)
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--level", level)
        assert code == (EXIT_FAIL if breaking else EXIT_PASS)
        assert payload["summary"]["breaking"] == (1 if breaking else 0)
        assert payload["summary"]["level"] == level

    def test_default_level_is_both(self, tmp_path: Path, capsys) -> None:
        """AC-5: default --level is both (a source-only break fails)."""
        xml = item_with(method("name", change("METHOD_ADDED_TO_INTERFACE", True, False),
                               status="NEW"))
        put(tmp_path, REPORT, xml)
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert code == EXIT_FAIL
        assert payload["summary"]["level"] == "both"

    def test_bad_level_is_usage_error(self, tmp_path: Path, capsys) -> None:
        """AC-5: only binary, source and both are levels."""
        put(tmp_path, REPORT, compatible_report())
        assert gate(tmp_path, "--report", REPORT, "--level", "api") == EXIT_USAGE
        assert "--level" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# AC-6
# --------------------------------------------------------------------------- #

def named_interface_report() -> str:
    return japicmp(klass(
        "com.acme.Named",
        methods=(method("name", change("METHOD_ADDED_TO_INTERFACE", True, False),
                        status="NEW", source=False),
                 method("id")),
        source=False,
    ))


def item_field_removed_report() -> str:
    return japicmp(klass(
        "com.acme.Item",
        methods=(method("size"),),
        fields=(field("id", change("FIELD_REMOVED", False, False), binary=False,
                      source=False, status="REMOVED"), field("name")),
        binary=False, source=False,
    ))


FINDING_ROWS = [
    pytest.param(lambda: item_with(removed_size()), "both", "api_binary_incompatible",
                 "METHOD_REMOVED com.acme.Item#size() [binary,source]", id="binary-code"),
    pytest.param(named_interface_report, "both", "api_source_incompatible",
                 "METHOD_ADDED_TO_INTERFACE com.acme.Named#name() [source]", id="source-code"),
    pytest.param(item_field_removed_report, "source", "api_source_incompatible",
                 "FIELD_REMOVED com.acme.Item#id [binary,source]", id="level-source"),
]


class TestAC6FindingMessage:
    """AC-6: breaking change -> error with code by level and `<type> <target> [<flags>]`."""

    @pytest.mark.parametrize(("make", "level", "code", "message"), FINDING_ROWS)
    def test_finding_json(self, make, level: str, code: str, message: str, tmp_path: Path,
                          capsys) -> None:
        """AC-6: example table rows (path relative to --cwd, line 0)."""
        put(tmp_path, REPORT, make())
        exit_code, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--level", level)
        assert exit_code == EXIT_FAIL
        assert payload["findings"] == [
            {"level": "error", "code": code, "message": message, "path": REPORT, "line": 0},
        ]

    @pytest.mark.parametrize(("make", "level", "code", "message"), FINDING_ROWS)
    def test_finding_text(self, make, level: str, code: str, message: str, tmp_path: Path,
                          capsys) -> None:
        """AC-6: the rendered text line."""
        put(tmp_path, REPORT, make())
        assert gate(tmp_path, "--report", REPORT, "--level", level) == EXIT_FAIL
        out = capsys.readouterr().out.splitlines()
        assert f"error {code} {REPORT} {message}" in out

    def test_findings_follow_document_order(self, tmp_path: Path, capsys) -> None:
        """AC-6: findings follow document order within a report."""
        xml = japicmp(
            klass("com.acme.Item",
                  methods=(method("title", change("METHOD_REMOVED", False, False),
                                  params=("java.lang.String",), status="REMOVED"),
                           method("hashCode")),
                  fields=(field("id", change("FIELD_REMOVED", False, False),
                                status="REMOVED"),),
                  binary=False, source=False),
            klass("com.acme.Alpha",
                  methods=(method("run", change("METHOD_REMOVED", False, False),
                                  status="REMOVED"),),
                  binary=False, source=False),
        )
        put(tmp_path, REPORT, xml)
        _, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert [f["message"] for f in payload["findings"]] == [
            "FIELD_REMOVED com.acme.Item#id [binary,source]",
            "METHOD_REMOVED com.acme.Item#title(java.lang.String) [binary,source]",
            "METHOD_REMOVED com.acme.Alpha#run() [binary,source]",
        ]


# --------------------------------------------------------------------------- #
# AC-7
# --------------------------------------------------------------------------- #

def removed_class(with_class_removed: bool) -> str:
    chg = (change("CLASS_REMOVED", False, False),) if with_class_removed else ()
    return japicmp(klass(
        "com.acme.Item",
        chg=chg,
        methods=(method("size", change("METHOD_REMOVED", False, False), binary=False,
                        source=False, status="REMOVED"),
                 method("title", change("METHOD_REMOVED", False, False), binary=False,
                        source=False, status="REMOVED")),
        binary=False, source=False, status="REMOVED" if with_class_removed else "MODIFIED",
    ))


class TestAC7RemovedClassCollapses:
    """AC-7: a breaking CLASS_REMOVED collapses the other changes in that class element."""

    @pytest.mark.parametrize(("with_class_removed", "findings", "collapsed"),
                             [(True, 1, 2), (False, 2, 0)])
    def test_collapse_rows(self, with_class_removed: bool, findings: int, collapsed: int,
                           tmp_path: Path, capsys) -> None:
        """AC-7: example table rows."""
        put(tmp_path, REPORT, removed_class(with_class_removed))
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert code == EXIT_FAIL
        assert len(payload["findings"]) == findings
        assert payload["summary"]["collapsed"] == collapsed

    def test_the_one_finding_is_class_removed(self, tmp_path: Path, capsys) -> None:
        """AC-7: the remaining finding is the CLASS_REMOVED change."""
        put(tmp_path, REPORT, removed_class(True))
        _, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert [f["message"] for f in payload["findings"]] == [
            "CLASS_REMOVED com.acme.Item [binary,source]"]


# --------------------------------------------------------------------------- #
# AC-8
# --------------------------------------------------------------------------- #

class TestAC8CountedNotReported:
    """AC-8: compatible changes and out-of-level changes add no finding but are counted."""

    @pytest.mark.parametrize(
        ("chg", "level", "compatible", "excluded"),
        [
            (change("METHOD_ADDED_TO_PUBLIC_CLASS", True, True), "both", 1, 0),
            (change("METHOD_ADDED_TO_INTERFACE", True, False), "binary", 0, 1),
        ],
    )
    def test_count_rows(self, chg: str, level: str, compatible: int, excluded: int,
                        tmp_path: Path, capsys) -> None:
        """AC-8: example table rows."""
        put(tmp_path, REPORT, item_with(method("slug", chg, status="NEW"),
                                        binary=True, source=level != "binary"))
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--level", level)
        assert code == EXIT_PASS
        assert payload["findings"] == []
        assert payload["summary"]["compatible_changes"] == compatible
        assert payload["summary"]["excluded_by_level"] == excluded


# --------------------------------------------------------------------------- #
# AC-9
# --------------------------------------------------------------------------- #

def single_break(class_name: str) -> str:
    return japicmp(klass(
        class_name,
        methods=(method("size", change("METHOD_REMOVED", False, False), binary=False,
                        source=False, status="REMOVED"), method("hashCode")),
        binary=False, source=False,
    ))


IGNORE_ROWS = [
    ("com.acme.internal.*", "com.acme.internal.Cache", EXIT_PASS),
    ("com.acme.internal.*", "com.acme.Item", EXIT_FAIL),
    ("*$Builder", "com.acme.Item$Builder", EXIT_PASS),
]


class TestAC9IgnoreDowngradesToInfo:
    """AC-9: --ignore GLOB (fnmatch on class_name) turns a break into info api_change_ignored."""

    @pytest.mark.parametrize(("glob", "class_name", "exit_code"), IGNORE_ROWS)
    def test_ignore_rows(self, glob: str, class_name: str, exit_code: int, tmp_path: Path,
                         capsys) -> None:
        """AC-9: example table rows."""
        put(tmp_path, REPORT, single_break(class_name))
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--ignore", glob)
        assert code == exit_code
        message = f"METHOD_REMOVED {class_name}#size() [binary,source]"
        if exit_code == EXIT_PASS:
            assert payload["findings"] == [{"level": "info", "code": "api_change_ignored",
                                            "message": message, "path": REPORT, "line": 0}]
            assert payload["summary"]["ignored"] == 1
            assert payload["passed"] is True
        else:
            assert payload["summary"]["ignored"] == 0
            assert [f["level"] for f in payload["findings"]] == ["error"]

    def test_ignore_repeats(self, tmp_path: Path, capsys) -> None:
        """AC-9: --ignore repeats."""
        put(tmp_path, "a.xml", single_break("com.acme.internal.Cache"))
        put(tmp_path, "b.xml", single_break("com.acme.Item$Builder"))
        code, payload = gate_json(tmp_path, capsys, "--report", "a.xml", "--report", "b.xml",
                                  "--ignore", "com.acme.internal.*", "--ignore", "*$Builder")
        assert code == EXIT_PASS
        assert payload["summary"]["ignored"] == 2

    def test_info_does_not_fail_strict(self, tmp_path: Path, capsys) -> None:
        """AC-9: info findings never fail the gate, even with --strict."""
        put(tmp_path, REPORT, single_break("com.acme.internal.Cache"))
        code, _ = gate_json(tmp_path, capsys, "--report", REPORT, "--ignore",
                            "com.acme.internal.*", "--strict")
        assert code == EXIT_PASS


# --------------------------------------------------------------------------- #
# AC-10
# --------------------------------------------------------------------------- #

def versioned_break(old: str | None, new: str | None) -> str:
    return japicmp(klass(
        "com.acme.Item",
        methods=(method("size", change("METHOD_REMOVED", False, False), binary=False,
                        source=False, status="REMOVED"), method("hashCode")),
        binary=False, source=False,
    ), old=old, new=new)


MAJOR_ROWS = [
    ("1.4.2", "2.0.0", ["--allow-major-bump"], EXIT_PASS),
    ("1.4.2", "2.0.0", ["--allow-major-bump", "--strict"], EXIT_FAIL),
    ("1.4.2", "1.5.0", ["--allow-major-bump"], EXIT_FAIL),
    (None, "2.0.0", ["--allow-major-bump"], EXIT_FAIL),
    ("v1.0", "v2.0-SNAPSHOT", ["--allow-major-bump"], EXIT_PASS),
    ("1.4.2", "2.0.0", [], EXIT_FAIL),
]


class TestAC10AllowMajorBump:
    """AC-10: --allow-major-bump turns breaks into warnings when the major version grows."""

    @pytest.mark.parametrize(("old", "new", "extra", "exit_code"), MAJOR_ROWS)
    def test_major_rows(self, old: str | None, new: str, extra: list[str], exit_code: int,
                        tmp_path: Path, capsys) -> None:
        """AC-10: example table rows."""
        put(tmp_path, REPORT, versioned_break(old, new))
        code, _ = gate_json(tmp_path, capsys, "--report", REPORT, *extra)
        assert code == exit_code

    def test_allowed_breaks_are_warnings(self, tmp_path: Path, capsys) -> None:
        """AC-10: allowed breaks keep the AC-6 code and message at level warning."""
        put(tmp_path, REPORT, versioned_break("1.4.2", "2.0.0"))
        _, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--allow-major-bump")
        assert payload["findings"] == [{
            "level": "warning", "code": "api_binary_incompatible",
            "message": "METHOD_REMOVED com.acme.Item#size() [binary,source]",
            "path": REPORT, "line": 0}]
        assert payload["summary"]["allowed_by_major_bump"] == 1
        assert payload["summary"]["breaking"] == 1

    def test_unknown_versions_warn_and_keep_errors(self, tmp_path: Path, capsys) -> None:
        """AC-10: a missing version adds one warning api_versions_unknown; breaks stay errors."""
        put(tmp_path, REPORT, versioned_break(None, "2.0.0"))
        _, payload = gate_json(tmp_path, capsys, "--report", REPORT, "--allow-major-bump")
        by_level = sorted((f["level"], f["code"]) for f in payload["findings"])
        assert by_level == [("error", "api_binary_incompatible"),
                            ("warning", "api_versions_unknown")]
        assert payload["summary"]["allowed_by_major_bump"] == 0

    def test_without_flag_versions_are_not_read(self, tmp_path: Path, capsys) -> None:
        """AC-10: without the flag no api_versions_unknown warning is added."""
        put(tmp_path, REPORT, versioned_break(None, None))
        _, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert [f["code"] for f in payload["findings"]] == ["api_binary_incompatible"]

    def test_parse_reads_versions(self, tmp_path: Path) -> None:
        """AC-10: JapicmpReport.old_version is None when the attribute is absent."""
        report = api().parse_japicmp(put(tmp_path, REPORT, versioned_break(None, "2.0.0")))
        assert report.old_version is None
        assert report.new_version == "2.0.0"


# --------------------------------------------------------------------------- #
# AC-11
# --------------------------------------------------------------------------- #

class TestAC11EmptyReportWarns:
    """AC-11: a report with no class elements adds warning api_report_empty."""

    @pytest.mark.parametrize(("extra", "exit_code"), [([], EXIT_PASS), (["--strict"], EXIT_FAIL)])
    def test_empty_rows(self, extra: list[str], exit_code: int, tmp_path: Path, capsys) -> None:
        """AC-11: example table rows."""
        put(tmp_path, REPORT, "<japicmp><classes/></japicmp>")
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT, *extra)
        assert code == exit_code
        assert [(f["level"], f["code"]) for f in payload["findings"]] == [
            ("warning", "api_report_empty")]


# --------------------------------------------------------------------------- #
# AC-12
# --------------------------------------------------------------------------- #

def summary_report() -> str:
    return japicmp(klass(
        "com.acme.Item",
        methods=(
            method("size", change("METHOD_REMOVED", False, False), binary=False,
                   source=False, status="REMOVED"),
            method("slug", change("METHOD_ADDED_TO_PUBLIC_CLASS", True, True), status="NEW"),
            method("hashCode"),
        ),
        fields=(field("id"),),
        binary=False, source=False,
    ))


EXPECTED_SUMMARY = {
    "reports": 1, "classes": 1, "breaking": 1, "binary_incompatible": 1,
    "source_incompatible": 1, "compatible_changes": 1, "excluded_by_level": 0,
    "collapsed": 0, "ignored": 0, "allowed_by_major_bump": 0, "level": "both",
}


class TestAC12SummaryKeys:
    """AC-12: the summary has exactly the fixed keys; --json is the standard gate JSON."""

    def test_json_summary(self, tmp_path: Path, capsys) -> None:
        """AC-12: example table row via --json."""
        put(tmp_path, REPORT, summary_report())
        code, payload = gate_json(tmp_path, capsys, "--report", REPORT)
        assert code == EXIT_FAIL
        assert payload["gate"] == "api-compat"
        assert payload["passed"] is False
        assert payload["errors"] == 1
        assert set(payload["summary"]) == SUMMARY_KEYS
        assert payload["summary"] == EXPECTED_SUMMARY

    def test_module_result(self, tmp_path: Path) -> None:
        """AC-12: run_api_compat returns a GateResult named api-compat with the fixed keys."""
        mod = api()
        report = mod.parse_japicmp(put(tmp_path, REPORT, summary_report()))
        result = mod.run_api_compat([report], tmp_path)
        assert isinstance(result, GateResult)
        assert result.gate == "api-compat"
        assert result.summary == EXPECTED_SUMMARY
        assert result.exit_code() == EXIT_FAIL

    def test_text_output_lists_summary(self, tmp_path: Path, capsys) -> None:
        """AC-12: text output renders the summary keys."""
        put(tmp_path, REPORT, summary_report())
        gate(tmp_path, "--report", REPORT)
        out = capsys.readouterr().out.splitlines()
        assert "breaking=1" in out
        assert "level=both" in out
        assert out[-1].startswith("gate=api-compat result=fail")


# --------------------------------------------------------------------------- #
# AC-13
# --------------------------------------------------------------------------- #

def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else b"<dir>")
            for p in sorted(root.rglob("*"))}


class TestAC13ReadOnly:
    """AC-13: the gate writes no file, starts no process, opens no network connection."""

    def test_directory_unchanged(self, tmp_path: Path, monkeypatch, capsys) -> None:
        """AC-13: directory listing unchanged after a run."""
        put(tmp_path, REPORT, summary_report())
        before = _snapshot(tmp_path)
        monkeypatch.chdir(tmp_path)
        assert qr("gate", "api-compat", "--report", REPORT) == EXIT_FAIL
        assert _snapshot(tmp_path) == before

    def test_same_result_with_processes_and_sockets_blocked(self, tmp_path: Path, monkeypatch,
                                                            capsys) -> None:
        """AC-13: patched subprocess/socket give the same result as unpatched."""
        put(tmp_path, REPORT, summary_report())
        first = gate(tmp_path, "--report", REPORT, "--json")
        unpatched = capsys.readouterr()

        def boom(*_a, **_k):
            raise AssertionError("api-compat must not start processes or open sockets")

        monkeypatch.setattr(subprocess, "run", boom)
        monkeypatch.setattr(subprocess, "Popen", boom)
        monkeypatch.setattr(os, "system", boom)
        monkeypatch.setattr(socket, "socket", boom)
        monkeypatch.setattr(socket, "create_connection", boom)
        second = gate(tmp_path, "--report", REPORT, "--json")
        patched = capsys.readouterr()
        assert first == second == EXIT_FAIL
        assert patched.out == unpatched.out
        assert patched.err == unpatched.err


# --------------------------------------------------------------------------- #
# AC-14
# --------------------------------------------------------------------------- #

class TestAC14Help:
    """AC-14: help shows the command and an example with --report."""

    @pytest.mark.parametrize(("argv", "needle"), [
        (["gate", "api-compat", "--help"], "--report"),
        (["gate", "--help"], "qr gate api-compat"),
    ])
    def test_help_rows(self, argv: list[str], needle: str, capsys) -> None:
        """AC-14: example table rows."""
        assert qr(*argv) == EXIT_PASS
        assert needle in capsys.readouterr().out

    def test_api_compat_help_has_example(self, capsys) -> None:
        """AC-14: the api-compat help shows a `qr gate api-compat ... --report` example."""
        assert qr("gate", "api-compat", "--help") == EXIT_PASS
        out = capsys.readouterr().out
        assert any("qr gate api-compat" in line and "--report" in line
                   for line in out.splitlines())

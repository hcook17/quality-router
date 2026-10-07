"""Held-out tests for phase 6 section A, `qr gate api-compat` (AC-1 .. AC-14).

Self-contained: imports only pytest, the stdlib and quality_router.*.
"""

from __future__ import annotations

import importlib
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from quality_router.cli import run

PASS, FAIL, USAGE = 0, 1, 2
SUMMARY_KEYS = {
    "reports", "classes", "breaking", "binary_incompatible", "source_incompatible",
    "compatible_changes", "excluded_by_level", "collapsed", "ignored",
    "allowed_by_major_bump", "level",
}


def mod():
    return importlib.import_module("quality_router.harness.api_compat")


def qr(*argv: str) -> int:
    try:
        return run(list(argv))
    except SystemExit as exc:
        if exc.code is None:
            return PASS
        return exc.code if isinstance(exc.code, int) else USAGE


def gate(cwd: Path, *argv: str) -> int:
    return qr("gate", "api-compat", "--cwd", str(cwd), *argv)


def gate_json(cwd: Path, capsys, *argv: str) -> tuple[int, dict]:
    code = gate(cwd, *argv, "--json")
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ----------------------------------------------------------------------------- #
# japicmp XML builders (JAXB element names; aggregate flags on owners)
# ----------------------------------------------------------------------------- #

def fl(b=None, s=None) -> str:
    def v(x):
        return x if isinstance(x, str) else ("true" if x else "false")
    return ((f' binaryCompatible="{v(b)}"' if b is not None else "")
            + (f' sourceCompatible="{v(s)}"' if s is not None else ""))


def cc(type_=None, b=None, s=None, text=None) -> str:
    attrs = (f' type="{type_}"' if type_ is not None else "") + fl(b, s)
    if text is None:
        return f"<compatibilityChange{attrs}/>"
    return f"<compatibilityChange{attrs}>{text}</compatibilityChange>"


def ccs(*items: str) -> str:
    return ("<compatibilityChanges>" + "".join(items) + "</compatibilityChanges>"
            if items else "<compatibilityChanges/>")


def wrap(tag: str, items) -> str:
    items = list(items)
    return f"<{tag}>{''.join(items)}</{tag}>" if items else f"<{tag}/>"


def params(types, inner: dict[int, str] | None = None) -> str:
    inner = inner or {}
    return wrap("parameters", [
        f'<parameter type="{t}"><annotations/>{inner.get(i, "")}</parameter>'
        for i, t in enumerate(types)])


def meth(name, *chg, types=(), b=True, s=True, st="UNCHANGED", annotations="",
         param_inner=None, return_inner="", exceptions="") -> str:
    return (f'<method name="{name}" changeStatus="{st}"{fl(b, s)} returnType="java.lang.Object">'
            f"{annotations or '<annotations/>'}{ccs(*chg)}"
            f"{exceptions or '<exceptions/>'}{params(types, param_inner)}"
            '<returnType changeStatus="UNCHANGED" oldValue="java.lang.Object"'
            f' newValue="java.lang.Object">{return_inner or "<compatibilityChanges/>"}'
            "</returnType></method>")


def ctor(name, *chg, types=(), b=True, s=True, st="UNCHANGED") -> str:
    return (f'<constructor name="{name}" changeStatus="{st}"{fl(b, s)}><annotations/>'
            f"{ccs(*chg)}<exceptions/>{params(types)}</constructor>")


def fld(name, *chg, b=True, s=True, st="UNCHANGED", annotations="") -> str:
    return (f'<field name="{name}" changeStatus="{st}"{fl(b, s)} type="long">'
            f"{annotations or '<annotations/>'}{ccs(*chg)}</field>")


def iface(fqn, *chg, b=True, s=True, st="UNCHANGED") -> str:
    return (f'<interface fullyQualifiedName="{fqn}" changeStatus="{st}"{fl(b, s)}>'
            f"{ccs(*chg)}</interface>")


def sup(*chg, b=True, s=True, st="UNCHANGED") -> str:
    return (f'<superclass changeStatus="{st}" superclassOld="org.lms.Base"'
            f' superclassNew="n.a."{fl(b, s)}>{ccs(*chg)}</superclass>')


def ann(fqn, *chg, b=True, s=True) -> str:
    return (f'<annotations><annotation fullyQualifiedName="{fqn}" changeStatus="MODIFIED"'
            f"{fl(b, s)}>{ccs(*chg)}<elements/></annotation></annotations>")


def cls(fqn, *, chg=(), ctors=(), fields=(), ifaces=(), methods=(), superclass=None,
        b=True, s=True, st="MODIFIED", annotations="") -> str:
    return (f'<class fullyQualifiedName="{fqn}" changeStatus="{st}" type="CLASS"{fl(b, s)}>'
            f"{annotations or '<annotations/>'}<attributes/>"
            '<classType changeStatus="UNCHANGED" oldType="CLASS" newType="CLASS"/>'
            f"{ccs(*chg)}{wrap('constructors', ctors)}{wrap('fields', fields)}"
            f"{wrap('interfaces', ifaces)}{wrap('methods', methods)}<modifiers/>"
            f"{superclass or sup()}<serialVersionUid/></class>")


def doc(*classes, old="3.2.0", new="3.3.0") -> str:
    v = (f' oldVersion="{old}"' if old is not None else "") + (
        f' newVersion="{new}"' if new is not None else "")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<japicmp oldJar="/m2/catalog-old.jar" newJar="/m2/catalog-new.jar"{v}'
            ' accessModifier="PROTECTED" onlyModifications="true"'
            ' onlyBinaryIncompatibleModifications="false" packagesInclude="org.lms.*">'
            f"{wrap('classes', classes)}</japicmp>\n")


def gone(name: str, type_: str = "METHOD_REMOVED", *types: str) -> str:
    return meth(name, cc(type_, False, False), types=types, b=False, s=False, st="REMOVED")


def one_break(fqn: str, member: str = "publish", old="3.2.0", new="3.3.0") -> str:
    return doc(cls(fqn, methods=(meth("toString"), gone(member)), fields=(fld("version"),),
                   b=False, s=False), old=old, new=new)


def quiet(fqn: str = "org.lms.catalog.Course") -> str:
    return doc(cls(fqn, methods=(meth("toString"),
                                 meth("tags", cc("METHOD_ADDED_TO_PUBLIC_CLASS", True, True),
                                      st="NEW")),
                   fields=(fld("version"),)))


# ----------------------------------------------------------------------------- #
# AC-1
# ----------------------------------------------------------------------------- #

def test_ac1_second_pattern_matching_nothing_is_usage_error(tmp_path, capsys):
    """AC-1: one good report plus a pattern that matches nothing exits 2."""
    write(tmp_path, "catalog/target/japicmp/japicmp.xml", quiet())
    code = gate(tmp_path, "--report", "catalog/target/japicmp/japicmp.xml",
                "--report", "gone/*/target/japicmp/*.xml")
    assert code == USAGE
    err = capsys.readouterr().err
    assert "japicmp report not found" in err
    assert len([ln for ln in err.splitlines() if ln.strip()]) >= 2


def test_ac1_glob_matching_only_directories_is_usage_error(tmp_path, capsys):
    """AC-1: matches that are not files exit 2 with `japicmp report not found`."""
    (tmp_path / "modules" / "grading").mkdir(parents=True)
    (tmp_path / "modules" / "roster").mkdir(parents=True)
    assert gate(tmp_path, "--report", "modules/*") == USAGE
    assert "japicmp report not found" in capsys.readouterr().err


def test_ac1_nested_glob_sorted_within_pattern(tmp_path, capsys):
    """AC-1: a nested glob reads every module report, sorted per pattern."""
    for name in ("gamma", "alpha", "beta"):
        write(tmp_path, f"services/{name}/lib/target/japicmp/api.xml",
              one_break(f"org.lms.{name}.Api"))
    code, payload = gate_json(tmp_path, capsys, "--report",
                              "services/*/lib/target/japicmp/*.xml")
    assert code == FAIL
    assert payload["summary"]["reports"] == 3
    assert [f["path"] for f in payload["findings"]] == [
        "services/alpha/lib/target/japicmp/api.xml",
        "services/beta/lib/target/japicmp/api.xml",
        "services/gamma/lib/target/japicmp/api.xml",
    ]


def test_ac1_patterns_keep_command_line_order(tmp_path, capsys):
    """AC-1: sorting is per pattern; patterns keep their command-line order."""
    write(tmp_path, "zeta/r.xml", one_break("org.lms.zeta.Z"))
    write(tmp_path, "alpha/r.xml", one_break("org.lms.alpha.A"))
    _, payload = gate_json(tmp_path, capsys, "--report", "zeta/*.xml", "--report", "alpha/*.xml")
    assert [f["path"] for f in payload["findings"]] == ["zeta/r.xml", "alpha/r.xml"]


def test_ac1_compatible_glob_reports_have_empty_stderr(tmp_path, capsys):
    """AC-1: compatible reports matched by a glob exit 0 with nothing on stderr."""
    write(tmp_path, "a/target/japicmp/x.xml", quiet("org.lms.a.A"))
    write(tmp_path, "b/target/japicmp/y.xml", quiet("org.lms.b.B"))
    assert gate(tmp_path, "--report", "*/target/japicmp/*.xml") == PASS
    assert capsys.readouterr().err == ""


# ----------------------------------------------------------------------------- #
# AC-2
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize("content", [
    "plain text, not xml",
    "",
    '<?xml version="1.0"?><testsuite name="CourseTest" tests="1"/>',
    '<japicmpReport><classes/></japicmpReport>',
    "<japicmp><classes></japicmp>",
])
def test_ac2_not_japicmp_cli_and_module(content, tmp_path, capsys):
    """AC-2: other roots or malformed XML exit 2 and raise ApiCompatError."""
    path = write(tmp_path, "reports/broken-api.xml", content)
    assert gate(tmp_path, "--report", "reports/*.xml") == USAGE
    err = capsys.readouterr().err
    assert "not a japicmp XML report" in err
    assert "broken-api.xml" in err
    m = mod()
    with pytest.raises(m.ApiCompatError):
        m.parse_japicmp(path)
    with pytest.raises(ValueError):
        m.parse_japicmp(path)


def test_ac2_bare_japicmp_root_is_valid(tmp_path):
    """AC-2: a well-formed `japicmp` root without a classes element is not a usage error."""
    write(tmp_path, "r.xml", '<japicmp oldVersion="1.0" newVersion="1.1"/>')
    assert gate(tmp_path, "--report", "r.xml") == PASS
    report = mod().parse_japicmp(tmp_path / "r.xml")
    assert report.classes == 0
    assert report.changes == []


def test_ac2_bad_second_report_still_usage_error(tmp_path, capsys):
    """AC-2: a bad file among good ones exits 2 and names the bad path."""
    write(tmp_path, "good.xml", quiet())
    write(tmp_path, "jacoco.xml", '<report name="catalog"><sessioninfo id="x"/></report>')
    assert gate(tmp_path, "--report", "good.xml", "--report", "jacoco.xml") == USAGE
    err = capsys.readouterr().err
    assert "not a japicmp XML report" in err
    assert "jacoco.xml" in err


# ----------------------------------------------------------------------------- #
# AC-3
# ----------------------------------------------------------------------------- #

def test_ac3_nested_class_and_array_parameters(tmp_path):
    """AC-3: `$` class names and parameter types keep their exact text."""
    xml = doc(cls("org.lms.catalog.Course$Section",
                  methods=(meth("toString"),
                           meth("rename", cc("METHOD_RETURN_TYPE_CHANGED", False, False),
                                types=("java.util.List", "long[]"), b=False, s=False,
                                st="MODIFIED")),
                  b=False, s=False))
    report = mod().parse_japicmp(write(tmp_path, "r.xml", xml))
    [c] = report.changes
    assert c.class_name == "org.lms.catalog.Course$Section"
    assert c.target == "org.lms.catalog.Course$Section#rename(java.util.List,long[])"
    assert c.kind == "method"
    assert c.type == "METHOD_RETURN_TYPE_CHANGED"


def test_ac3_intermediate_elements_are_not_owners(tmp_path):
    """AC-3: changes under parameter, returnType, exception and annotation belong to the member."""
    param_change = ccs(cc("METHOD_PARAMETER_ANNOTATION_REMOVED", True, True))
    xml = doc(cls(
        "org.lms.grading.Rubric",
        annotations=ann("javax.annotation.Generated", cc("ANNOTATION_REMOVED", True, False)),
        fields=(fld("weight", cc("FIELD_TYPE_CHANGED", False, False), b=False, s=False,
                    st="MODIFIED",
                    annotations=ann("org.lms.Audited", cc("ANNOTATION_ADDED", True, True))),),
        methods=(
            meth("score", types=("org.lms.grading.Answer", "int"), st="MODIFIED",
                 param_inner={1: param_change},
                 return_inner=ccs(cc("METHOD_RETURN_TYPE_GENERICS_CHANGED", True, False)),
                 exceptions=('<exceptions><exception name="java.io.IOException"'
                             ' changeStatus="NEW">'
                             + ccs(cc("METHOD_NOW_THROWS_CHECKED_EXCEPTION", True, False))
                             + "</exception></exceptions>")),
        ),
        b=False, s=False))
    report = mod().parse_japicmp(write(tmp_path, "r.xml", xml))
    got = [(c.kind, c.target, c.type) for c in report.changes]
    score = "org.lms.grading.Rubric#score(org.lms.grading.Answer,int)"
    assert got == [
        ("class", "org.lms.grading.Rubric", "ANNOTATION_REMOVED"),
        ("field", "org.lms.grading.Rubric#weight", "ANNOTATION_ADDED"),
        ("field", "org.lms.grading.Rubric#weight", "FIELD_TYPE_CHANGED"),
        ("method", score, "METHOD_NOW_THROWS_CHECKED_EXCEPTION"),
        ("method", score, "METHOD_PARAMETER_ANNOTATION_REMOVED"),
        ("method", score, "METHOD_RETURN_TYPE_GENERICS_CHANGED"),
    ]
    assert {c.class_name for c in report.changes} == {"org.lms.grading.Rubric"}


def test_ac3_constructors_interfaces_superclass_across_classes(tmp_path):
    """AC-3: every owner kind, class_name per class, unchanged classes counted."""
    xml = doc(
        cls("org.lms.roster.Enrollment",
            ctors=(ctor("Enrollment", cc("CONSTRUCTOR_REMOVED", False, False), b=False,
                        s=False, st="REMOVED"),
                   ctor("Enrollment", cc("CONSTRUCTOR_LESS_ACCESSIBLE", False, False),
                        types=("java.lang.String", "java.time.Instant"), b=False, s=False,
                        st="MODIFIED")),
            ifaces=(iface("java.lang.Comparable"),
                    iface("org.lms.roster.Auditable", cc("INTERFACE_REMOVED", False, False),
                          b=False, s=False, st="REMOVED")),
            b=False, s=False),
        cls("org.lms.roster.Seat", st="UNCHANGED", methods=(meth("number"),)),
        cls("org.lms.roster.Waitlist",
            superclass=sup(cc("SUPERCLASS_REMOVED", False, False), b=False, s=False,
                           st="MODIFIED"),
            methods=(meth("size"),), b=False, s=False),
    )
    report = mod().parse_japicmp(write(tmp_path, "r.xml", xml))
    assert [(c.class_name, c.kind, c.target) for c in report.changes] == [
        ("org.lms.roster.Enrollment", "constructor", "org.lms.roster.Enrollment#<init>()"),
        ("org.lms.roster.Enrollment", "constructor",
         "org.lms.roster.Enrollment#<init>(java.lang.String,java.time.Instant)"),
        ("org.lms.roster.Enrollment", "interface",
         "org.lms.roster.Enrollment#interface:org.lms.roster.Auditable"),
        ("org.lms.roster.Waitlist", "superclass", "org.lms.roster.Waitlist#superclass"),
    ]
    assert report.classes == 3
    assert report.old_version == "3.2.0"
    assert report.new_version == "3.3.0"


def test_ac3_aggregate_flags_alone_are_not_changes(tmp_path):
    """AC-3: incompatible aggregate attributes without compatibilityChange are not changes."""
    xml = doc(cls("org.lms.Legacy", methods=(meth("run", b=False, s=False, st="MODIFIED"),),
                  fields=(fld("id", b=False, s=False),), b=False, s=False))
    report = mod().parse_japicmp(write(tmp_path, "r.xml", xml))
    assert report.changes == []
    assert report.classes == 1


# ----------------------------------------------------------------------------- #
# AC-4
# ----------------------------------------------------------------------------- #

def _single(tmp_path, member_xml: str, b=True, s=True):
    xml = doc(cls("org.lms.catalog.Course", methods=(meth("toString"), member_xml), b=b, s=s))
    [c] = mod().parse_japicmp(write(tmp_path, "r.xml", xml)).changes
    return c


@pytest.mark.parametrize(("change", "owner", "expected"), [
    (cc("METHOD_NOW_STATIC", "False", "True"), (True, False), (False, True)),
    (cc("METHOD_NOW_STATIC", "TRUE", "fAlSe"), (False, True), (True, False)),
    (cc("METHOD_ABSTRACT_ADDED_TO_CLASS", "true"), (True, "False"), (True, False)),
    (cc(None, text="  METHOD_LESS_ACCESSIBLE\n"), ("FALSE", "true"), (False, True)),
    (cc("METHOD_NOW_FINAL", s="false"), (None, True), (False, False)),
])
def test_ac4_flags_change_then_owner_then_fail_closed(change, owner, expected, tmp_path):
    """AC-4: own attribute (any case) first, then the owner's, else incompatible."""
    c = _single(tmp_path, meth("enroll", change, b=owner[0], s=owner[1], st="MODIFIED"))
    assert (c.binary_compatible, c.source_compatible) == expected


def test_ac4_owner_is_member_not_class_for_fallback(tmp_path):
    """AC-4: a member without flags does not inherit the class's flags; fail closed."""
    c = _single(tmp_path, meth("enroll", cc(None, text="METHOD_REMOVED"), b=None, s=None,
                               st="REMOVED"), b=True, s=True)
    assert (c.type, c.binary_compatible, c.source_compatible) == ("METHOD_REMOVED", False, False)


def test_ac4_annotation_flags_are_not_the_owner(tmp_path):
    """AC-4: for a change under an annotation, the fallback owner is the method."""
    member = meth("enroll", b=False, s=True, st="MODIFIED",
                  annotations=ann("org.lms.Beta", cc("ANNOTATION_REMOVED"), b=True, s=True))
    c = _single(tmp_path, member)
    assert (c.binary_compatible, c.source_compatible) == (False, True)


def test_ac4_type_attribute_wins_over_text(tmp_path):
    """AC-4: the type attribute is used before the text."""
    c = _single(tmp_path, meth("enroll", cc("METHOD_NOW_ABSTRACT", False, False,
                                           text="METHOD_REMOVED"), st="MODIFIED"))
    assert c.type == "METHOD_NOW_ABSTRACT"


def test_ac4_blank_text_is_unknown(tmp_path):
    """AC-4: whitespace-only text and no type attribute -> UNKNOWN."""
    c = _single(tmp_path, meth("enroll", cc(None, False, True, text="  \n "), st="MODIFIED"))
    assert (c.type, c.binary_compatible, c.source_compatible) == ("UNKNOWN", False, True)


def test_ac4_unknown_change_without_flags_fails_the_gate(tmp_path, capsys):
    """AC-4: a change with no type and no flags anywhere counts as incompatible."""
    xml = doc(cls("org.lms.catalog.Course",
                  methods=(meth("enroll", cc(), b=None, s=None, st="MODIFIED"),)))
    write(tmp_path, "r.xml", xml)
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml")
    assert code == FAIL
    assert [f["message"] for f in payload["findings"]] == [
        "UNKNOWN org.lms.catalog.Course#enroll() [binary,source]"]


# ----------------------------------------------------------------------------- #
# AC-5
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("b", "s", "level", "exit_code"), [
    (False, False, "source", FAIL),
    (False, False, "binary", FAIL),
    (True, False, "source", FAIL),
    (False, True, "both", FAIL),
    (True, True, "binary", PASS),
    (True, True, "source", PASS),
])
def test_ac5_more_level_rows(b, s, level, exit_code, tmp_path, capsys):
    """AC-5: breaking when a selected flag is false."""
    write(tmp_path, "r.xml", doc(cls("org.lms.grading.Grade", fields=(
        fld("points", cc("FIELD_STATIC_AND_OVERRIDES_STATIC", b, s), b=b, s=s,
            st="MODIFIED"),))))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--level", level)
    assert code == exit_code
    assert payload["summary"]["level"] == level


# ----------------------------------------------------------------------------- #
# AC-6
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("b", "s", "level", "code", "flags"), [
    (False, False, "binary", "api_binary_incompatible", "[binary,source]"),
    (False, False, "source", "api_source_incompatible", "[binary,source]"),
    (False, True, "both", "api_binary_incompatible", "[binary]"),
    (True, False, "source", "api_source_incompatible", "[source]"),
])
def test_ac6_code_and_flags(b, s, level, code, flags, tmp_path, capsys):
    """AC-6: code by level and binary flag; flags list every false flag."""
    write(tmp_path, "build/japicmp/catalog.xml", doc(cls(
        "org.lms.catalog.Course$Builder",
        ctors=(ctor("Builder", cc("CONSTRUCTOR_LESS_ACCESSIBLE", b, s),
                    types=("org.lms.catalog.Course",), b=b, s=s, st="MODIFIED"),))))
    exit_code, payload = gate_json(tmp_path, capsys, "--report", "build/japicmp/catalog.xml",
                                   "--level", level)
    assert exit_code == FAIL
    assert payload["findings"] == [{
        "level": "error", "code": code, "line": 0, "path": "build/japicmp/catalog.xml",
        "message": ("CONSTRUCTOR_LESS_ACCESSIBLE "
                    f"org.lms.catalog.Course$Builder#<init>(org.lms.catalog.Course) {flags}"),
    }]


def test_ac6_report_outside_cwd_uses_absolute_path(tmp_path, capsys):
    """AC-6: a report outside --cwd keeps its absolute POSIX path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = write(tmp_path, "shared/japicmp/roster.xml", one_break("org.lms.roster.Seat"))
    _, payload = gate_json(repo, capsys, "--report", str(outside))
    assert [f["path"] for f in payload["findings"]] == [outside.as_posix()]


def test_ac6_absolute_path_inside_cwd_is_relative(tmp_path, capsys):
    """AC-6: an absolute report path inside --cwd is shown relative to it."""
    inside = write(tmp_path, "grading/target/japicmp/japicmp.xml",
                   one_break("org.lms.grading.Grade"))
    _, payload = gate_json(tmp_path, capsys, "--report", str(inside))
    assert [f["path"] for f in payload["findings"]] == ["grading/target/japicmp/japicmp.xml"]


def test_ac6_relative_cwd(tmp_path, monkeypatch, capsys):
    """AC-6: with a relative --cwd the path is still relative to --cwd."""
    write(tmp_path, "svc/target/japicmp/japicmp.xml", one_break("org.lms.Svc"))
    monkeypatch.chdir(tmp_path)
    code = qr("gate", "api-compat", "--cwd", "svc", "--report",
              "target/japicmp/japicmp.xml", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert code == FAIL
    assert [f["path"] for f in payload["findings"]] == ["target/japicmp/japicmp.xml"]


def test_ac6_report_order_then_document_order(tmp_path, capsys):
    """AC-6: findings follow report order (command line), then document order."""
    write(tmp_path, "b-second.xml", doc(cls("org.lms.b.Zed", methods=(
        gone("zap"), gone("act")), b=False, s=False)))
    write(tmp_path, "a-first.xml", doc(cls("org.lms.a.Alpha", methods=(gone("one"),),
                                           b=False, s=False)))
    _, payload = gate_json(tmp_path, capsys, "--report", "b-second.xml",
                           "--report", "a-first.xml")
    assert [(f["path"], f["message"]) for f in payload["findings"]] == [
        ("b-second.xml", "METHOD_REMOVED org.lms.b.Zed#zap() [binary,source]"),
        ("b-second.xml", "METHOD_REMOVED org.lms.b.Zed#act() [binary,source]"),
        ("a-first.xml", "METHOD_REMOVED org.lms.a.Alpha#one() [binary,source]"),
    ]


# ----------------------------------------------------------------------------- #
# AC-7
# ----------------------------------------------------------------------------- #

def test_ac7_class_removed_collapses_every_member_kind(tmp_path, capsys):
    """AC-7: constructor, field, method and superclass changes in a removed class collapse."""
    write(tmp_path, "r.xml", doc(cls(
        "org.lms.legacy.Gradebook",
        chg=(cc("CLASS_REMOVED", False, False),),
        ctors=(ctor("Gradebook", cc("CONSTRUCTOR_REMOVED", False, False), b=False, s=False,
                    st="REMOVED"),),
        fields=(fld("rows", cc("FIELD_REMOVED", False, False), b=False, s=False,
                    st="REMOVED"),),
        methods=(gone("export"),),
        superclass=sup(cc("SUPERCLASS_REMOVED", False, False), b=False, s=False,
                       st="REMOVED"),
        b=False, s=False, st="REMOVED")))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml")
    assert code == FAIL
    assert [f["message"] for f in payload["findings"]] == [
        "CLASS_REMOVED org.lms.legacy.Gradebook [binary,source]"]
    s = payload["summary"]
    assert (s["collapsed"], s["breaking"], s["binary_incompatible"],
            s["source_incompatible"]) == (4, 1, 1, 1)


def test_ac7_collapse_is_per_class_element(tmp_path, capsys):
    """AC-7: a nested class element and a sibling class are not collapsed."""
    write(tmp_path, "r.xml", doc(
        cls("org.lms.legacy.Gradebook", chg=(cc("CLASS_REMOVED", False, False),),
            methods=(gone("export"),), b=False, s=False, st="REMOVED"),
        cls("org.lms.legacy.Gradebook$Row", methods=(gone("cells"),), b=False, s=False),
        cls("org.lms.legacy.Report", methods=(gone("render"),), b=False, s=False),
    ))
    _, payload = gate_json(tmp_path, capsys, "--report", "r.xml")
    assert [f["message"] for f in payload["findings"]] == [
        "CLASS_REMOVED org.lms.legacy.Gradebook [binary,source]",
        "METHOD_REMOVED org.lms.legacy.Gradebook$Row#cells() [binary,source]",
        "METHOD_REMOVED org.lms.legacy.Report#render() [binary,source]",
    ]
    assert payload["summary"]["collapsed"] == 1


def test_ac7_non_breaking_class_removed_does_not_collapse(tmp_path, capsys):
    """AC-7: only a breaking CLASS_REMOVED (at the selected level) collapses."""
    write(tmp_path, "r.xml", doc(cls(
        "org.lms.legacy.Gradebook",
        chg=(cc("CLASS_REMOVED", True, False),),
        methods=(meth("export", cc("METHOD_REMOVED", False, True), b=False, s=True,
                      st="REMOVED"),),
        b=False, s=False)))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--level", "binary")
    assert code == FAIL
    assert [f["message"] for f in payload["findings"]] == [
        "METHOD_REMOVED org.lms.legacy.Gradebook#export() [binary]"]
    assert payload["summary"]["collapsed"] == 0
    assert payload["summary"]["excluded_by_level"] == 1


# ----------------------------------------------------------------------------- #
# AC-8
# ----------------------------------------------------------------------------- #

def test_ac8_counts_across_classes(tmp_path, capsys):
    """AC-8: compatible and out-of-level changes add no findings but are counted."""
    write(tmp_path, "r.xml", doc(
        cls("org.lms.catalog.Course", methods=(
            meth("tags", cc("METHOD_ADDED_TO_PUBLIC_CLASS", True, True), st="NEW"),
            meth("slug", cc("METHOD_ADDED_TO_PUBLIC_CLASS", True, True), st="NEW"))),
        cls("org.lms.catalog.Named", methods=(
            meth("label", cc("METHOD_ADDED_TO_INTERFACE", True, False), s=False, st="NEW"),
            meth("hint", cc("METHOD_DEFAULT_ADDED_IN_IMPLEMENTED_INTERFACE", "True", "TRUE"),
                 st="NEW"))),
        cls("org.lms.catalog.Lesson", fields=(
            fld("order", cc("FIELD_LESS_ACCESSIBLE", False, True), b=False, st="MODIFIED"),)),
    ))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--level", "source")
    assert code == FAIL
    assert [f["message"] for f in payload["findings"]] == [
        "METHOD_ADDED_TO_INTERFACE org.lms.catalog.Named#label() [source]"]
    s = payload["summary"]
    assert (s["compatible_changes"], s["excluded_by_level"], s["breaking"]) == (3, 1, 1)
    assert (s["binary_incompatible"], s["source_incompatible"]) == (1, 1)


# ----------------------------------------------------------------------------- #
# AC-9
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("glob", "fqn", "exit_code"), [
    ("org.lms.INTERNAL.*", "org.lms.internal.Cache", FAIL),
    ("org.lms.catalog.Cours?", "org.lms.catalog.Course", PASS),
    ("*publish*", "org.lms.catalog.Course", FAIL),
    ("org.lms.catalog.Course$*", "org.lms.catalog.Course$Section", PASS),
    ("org.lms.catalog.Course", "org.lms.catalog.Course$Section", FAIL),
    ("*", "org.lms.anything.At.All", PASS),
])
def test_ac9_glob_matches_class_name_case_sensitively(glob, fqn, exit_code, tmp_path, capsys):
    """AC-9: fnmatch (case-sensitive) on class_name, not on the target."""
    write(tmp_path, "r.xml", one_break(fqn))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--ignore", glob)
    assert code == exit_code
    assert payload["summary"]["ignored"] == (1 if exit_code == PASS else 0)


def test_ac9_ignored_counts(tmp_path, capsys):
    """AC-9: ignored breaks are info; they count in ignored and in the flag counts only."""
    write(tmp_path, "r.xml", doc(
        cls("org.lms.internal.Cache", methods=(gone("evict"), gone("warm")), b=False, s=False),
        cls("org.lms.catalog.Course", methods=(gone("publish"),), b=False, s=False),
    ))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml",
                              "--ignore", "org.lms.internal.*")
    assert code == FAIL
    assert [(f["level"], f["code"]) for f in payload["findings"]] == [
        ("info", "api_change_ignored"), ("info", "api_change_ignored"),
        ("error", "api_binary_incompatible")]
    assert payload["findings"][0]["message"] == (
        "METHOD_REMOVED org.lms.internal.Cache#evict() [binary,source]")
    s = payload["summary"]
    assert (s["ignored"], s["breaking"], s["binary_incompatible"],
            s["source_incompatible"]) == (2, 1, 3, 3)
    assert payload["errors"] == 1
    assert payload["warnings"] == 0


def test_ac9_out_of_level_change_is_excluded_not_ignored(tmp_path, capsys):
    """AC-9: only breaking changes are ignored; an out-of-level change stays excluded."""
    write(tmp_path, "r.xml", doc(cls("org.lms.internal.Cache", methods=(
        meth("evict", cc("METHOD_ADDED_TO_INTERFACE", True, False), s=False, st="NEW"),))))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--level", "binary",
                              "--ignore", "org.lms.internal.*")
    assert code == PASS
    assert payload["findings"] == []
    assert (payload["summary"]["ignored"], payload["summary"]["excluded_by_level"]) == (0, 1)


# ----------------------------------------------------------------------------- #
# AC-10
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("old", "new", "exit_code"), [
    ("9.7.1", "10.0.0", PASS),
    ("2.0.0", "1.9.0", FAIL),
    ("4.1", "4.9", FAIL),
    ("release-1", "2.0.0", FAIL),
    ("1.0.0", "", FAIL),
    ("v3", "4.0.0-RC1", PASS),
])
def test_ac10_major_compare(old, new, exit_code, tmp_path, capsys):
    """AC-10: majors compare as integers read with ^v?(\\d+)."""
    write(tmp_path, "r.xml", one_break("org.lms.catalog.Course", old=old, new=new))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--allow-major-bump")
    assert code == exit_code
    assert payload["summary"]["allowed_by_major_bump"] == (1 if exit_code == PASS else 0)


def test_ac10_one_unknown_warning_per_report(tmp_path, capsys):
    """AC-10: a report with unparseable versions adds exactly one api_versions_unknown."""
    write(tmp_path, "r.xml", doc(cls("org.lms.catalog.Course", methods=(
        gone("a"), gone("b"), gone("c")), b=False, s=False), old=None, new="snapshot"))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--allow-major-bump")
    assert code == FAIL
    codes = [(f["level"], f["code"]) for f in payload["findings"]]
    assert codes.count(("warning", "api_versions_unknown")) == 1
    assert codes.count(("error", "api_binary_incompatible")) == 3


def test_ac10_unknown_versions_warn_even_without_breaks(tmp_path, capsys):
    """AC-10: the unknown-versions warning does not depend on breaking changes; --strict fails."""
    write(tmp_path, "r.xml", doc(cls("org.lms.catalog.Course", methods=(meth("x"),)),
                                 old=None, new=None))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--allow-major-bump")
    assert code == PASS
    assert [(f["level"], f["code"]) for f in payload["findings"]] == [
        ("warning", "api_versions_unknown")]
    assert gate(tmp_path, "--report", "r.xml", "--allow-major-bump", "--strict") == FAIL


def test_ac10_decided_per_report(tmp_path, capsys):
    """AC-10: one report bumps its major, the other does not."""
    write(tmp_path, "bumped.xml", one_break("org.lms.a.A", old="1.9.0", new="2.0.0"))
    write(tmp_path, "minor.xml", one_break("org.lms.b.B", old="3.1.0", new="3.2.0"))
    code, payload = gate_json(tmp_path, capsys, "--report", "bumped.xml",
                              "--report", "minor.xml", "--allow-major-bump")
    assert code == FAIL
    assert [(f["path"], f["level"], f["code"]) for f in payload["findings"]] == [
        ("bumped.xml", "warning", "api_binary_incompatible"),
        ("minor.xml", "error", "api_binary_incompatible"),
    ]
    assert payload["summary"]["allowed_by_major_bump"] == 1
    assert payload["summary"]["breaking"] == 2


# ----------------------------------------------------------------------------- #
# AC-11
# ----------------------------------------------------------------------------- #

def test_ac11_only_the_empty_report_warns(tmp_path, capsys):
    """AC-11: one empty report among others adds one api_report_empty."""
    write(tmp_path, "empty.xml", '<japicmp oldVersion="1" newVersion="1"/>')
    write(tmp_path, "full.xml", quiet())
    code, payload = gate_json(tmp_path, capsys, "--report", "empty.xml", "--report", "full.xml")
    assert code == PASS
    assert [(f["level"], f["code"]) for f in payload["findings"]] == [
        ("warning", "api_report_empty")]
    assert payload["summary"]["reports"] == 2


def test_ac11_classes_without_changes_is_not_empty(tmp_path, capsys):
    """AC-11: a report with class elements but no changes does not warn."""
    write(tmp_path, "r.xml", doc(cls("org.lms.catalog.Course", st="UNCHANGED",
                                     methods=(meth("x"),))))
    code, payload = gate_json(tmp_path, capsys, "--report", "r.xml", "--strict")
    assert code == PASS
    assert payload["findings"] == []
    assert payload["summary"]["classes"] == 1


# ----------------------------------------------------------------------------- #
# AC-12
# ----------------------------------------------------------------------------- #

def _two_reports(tmp_path: Path) -> tuple[Path, Path]:
    a = write(tmp_path, "a.xml", doc(
        cls("org.lms.catalog.Course",
            fields=(fld("credits", cc("FIELD_TYPE_CHANGED", False, False), b=False, s=False,
                        st="MODIFIED"),),
            methods=(gone("publish"),), b=False, s=False),
        cls("org.lms.catalog.Lesson", chg=(cc("CLASS_REMOVED", False, False),),
            methods=(gone("start"), gone("stop")), b=False, s=False, st="REMOVED"),
        old="1.0.0", new="2.0.0"))
    b = write(tmp_path, "b.xml", doc(
        cls("org.lms.internal.Cache", methods=(gone("evict"),), b=False, s=False),
        cls("org.lms.quiz.Quiz",
            fields=(fld("limit", cc("FIELD_REMOVED", False, False), b=False, s=False,
                        st="REMOVED"),),
            methods=(meth("label", cc("METHOD_ADDED_TO_INTERFACE", True, False), s=False,
                          st="NEW"),
                     meth("tags", cc("METHOD_ADDED_TO_PUBLIC_CLASS", True, True), st="NEW")),
            b=False, s=False),
        cls("org.lms.quiz.Answer", st="UNCHANGED", methods=(meth("text"),)),
        old="3.0.0", new="3.1.0"))
    return a, b


EXPECTED = {
    "reports": 2, "classes": 5, "breaking": 4, "binary_incompatible": 5,
    "source_incompatible": 6, "compatible_changes": 1, "excluded_by_level": 1,
    "collapsed": 2, "ignored": 1, "allowed_by_major_bump": 3, "level": "binary",
}


def test_ac12_summary_over_two_reports_json(tmp_path, capsys):
    """AC-12: every counter over two reports with level, ignore and major bump."""
    _two_reports(tmp_path)
    code, payload = gate_json(tmp_path, capsys, "--report", "a.xml", "--report", "b.xml",
                              "--level", "binary", "--ignore", "org.lms.internal.*",
                              "--allow-major-bump")
    assert code == FAIL
    assert payload["gate"] == "api-compat"
    assert set(payload["summary"]) == SUMMARY_KEYS
    assert payload["summary"] == EXPECTED
    assert (payload["errors"], payload["warnings"], payload["passed"]) == (1, 3, False)
    assert [(f["level"], f["message"]) for f in payload["findings"]] == [
        ("warning", "FIELD_TYPE_CHANGED org.lms.catalog.Course#credits [binary,source]"),
        ("warning", "METHOD_REMOVED org.lms.catalog.Course#publish() [binary,source]"),
        ("warning", "CLASS_REMOVED org.lms.catalog.Lesson [binary,source]"),
        ("info", "METHOD_REMOVED org.lms.internal.Cache#evict() [binary,source]"),
        ("error", "FIELD_REMOVED org.lms.quiz.Quiz#limit [binary,source]"),
    ]


def test_ac12_module_api_matches_cli(tmp_path):
    """AC-12: run_api_compat over parsed reports gives the same summary; strict is honoured."""
    m = mod()
    a, b = _two_reports(tmp_path)
    reports = [m.parse_japicmp(a), m.parse_japicmp(b)]
    result = m.run_api_compat(reports, tmp_path, level="binary", ignore=("org.lms.internal.*",),
                              allow_major_bump=True)
    assert result.gate == "api-compat"
    assert result.summary == EXPECTED
    only_bumped = m.run_api_compat([reports[0]], tmp_path, level="binary",
                                   allow_major_bump=True)
    assert only_bumped.exit_code() == PASS
    strict = m.run_api_compat([reports[0]], tmp_path, level="binary", allow_major_bump=True,
                              strict=True)
    assert strict.exit_code() == FAIL


def test_ac12_defaults_of_run_api_compat(tmp_path):
    """AC-12: defaults are level both, no ignores, no major bump, not strict."""
    m = mod()
    a, _ = _two_reports(tmp_path)
    result = m.run_api_compat([m.parse_japicmp(a)], tmp_path)
    s = result.summary
    assert s["level"] == "both"
    assert (s["allowed_by_major_bump"], s["ignored"], s["breaking"], s["collapsed"]) == (
        0, 0, 3, 2)
    assert result.exit_code() == FAIL


# ----------------------------------------------------------------------------- #
# AC-13
# ----------------------------------------------------------------------------- #

def _tree(root: Path) -> dict[str, tuple[bytes, int]]:
    return {p.relative_to(root).as_posix(): ((p.read_bytes() if p.is_file() else b"/"),
                                             p.stat().st_mtime_ns)
            for p in sorted(root.rglob("*"))}


def test_ac13_no_writes_no_processes_no_sockets(tmp_path, monkeypatch, capsys):
    """AC-13: glob + JSON run leaves the tree unchanged with processes and sockets blocked."""
    _two_reports(tmp_path)
    write(tmp_path, "mods/x/target/japicmp/japicmp.xml", quiet())
    before = _tree(tmp_path)
    argv = ("--report", "*.xml", "--report", "mods/*/target/japicmp/*.xml",
            "--allow-major-bump", "--json")
    first = gate(tmp_path, *argv)
    plain = capsys.readouterr()

    def boom(*_a, **_k):
        raise AssertionError("no process or socket")

    for target, name in [(subprocess, "run"), (subprocess, "Popen"),
                         (subprocess, "check_output"), (os, "system"), (os, "popen"),
                         (socket, "socket"), (socket, "create_connection"),
                         (socket, "getaddrinfo")]:
        monkeypatch.setattr(target, name, boom)
    second = gate(tmp_path, *argv)
    blocked = capsys.readouterr()
    assert first == second == FAIL
    assert (blocked.out, blocked.err) == (plain.out, plain.err)
    assert _tree(tmp_path) == before


def test_ac13_usage_error_writes_nothing(tmp_path, monkeypatch, capsys):
    """AC-13: the usage-error path is read-only too."""
    write(tmp_path, "bad.xml", "<nope/>")
    before = _tree(tmp_path)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("no process")))
    assert gate(tmp_path, "--report", "bad.xml") == USAGE
    assert "not a japicmp XML report" in capsys.readouterr().err
    assert gate(tmp_path, "--report", "missing/*.xml") == USAGE
    assert "japicmp report not found" in capsys.readouterr().err
    assert _tree(tmp_path) == before


# ----------------------------------------------------------------------------- #
# AC-14
# ----------------------------------------------------------------------------- #

def test_ac14_short_help_flag(capsys):
    """AC-14: `-h` shows the same help with a --report example."""
    assert qr("gate", "api-compat", "-h") == PASS
    out = capsys.readouterr().out
    assert any("qr gate api-compat" in line and "--report" in line for line in out.splitlines())


def test_ac14_gate_help_example_line(capsys):
    """AC-14: `qr gate --help` has an example line starting with `qr gate api-compat`."""
    assert qr("gate", "--help") == PASS
    out = capsys.readouterr().out
    assert any(line.strip().startswith("qr gate api-compat") for line in out.splitlines())

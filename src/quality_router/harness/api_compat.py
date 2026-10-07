"""Java API compatibility gate over japicmp XML reports (read-only).

Evidence: 2608.20167 (95% of what LLM-written client tests caught on
dependency bumps was crash-type breakage: missing classes and methods, the
class of break japicmp reports; japicmp itself was not measured). japicmp
computes the diff in the build;
this gate reads its JAXB XML and decides. Each `compatibilityChange` counts
once, at its nearest class/member owner; the aggregate compatibility
attributes on classes and members are derived from those changes and are not
counted again.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

from quality_router.harness.report import GateResult, Level

LEVELS = ("binary", "source", "both")
OWNER_TAGS = ("class", "method", "constructor", "field", "superclass", "interface")
_MAJOR = re.compile(r"^v?(\d+)")


class ApiCompatError(ValueError):
    pass


@dataclass(frozen=True)
class ApiChange:
    class_name: str
    target: str
    kind: str
    type: str
    binary_compatible: bool
    source_compatible: bool


@dataclass
class JapicmpReport:
    path: Path
    old_version: str | None
    new_version: str | None
    classes: int = 0
    changes: list[ApiChange] = field(default_factory=list)


def parse_japicmp(path: Path) -> JapicmpReport:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ApiCompatError(f"not a japicmp XML report: {path} ({exc})") from exc
    if root.tag != "japicmp":
        raise ApiCompatError(f"not a japicmp XML report: {path} (root <{root.tag}>)")
    report = JapicmpReport(path=Path(path), old_version=root.get("oldVersion"),
                           new_version=root.get("newVersion"))
    _walk(root, [], report)
    return report


def _walk(element: ET.Element, owners: list[ET.Element], report: JapicmpReport) -> None:
    for child in element:
        if child.tag == "compatibilityChange":
            if owners:
                report.changes.append(_change(child, owners))
            continue
        if child.tag == "class":
            report.classes += 1
        _walk(child, [*owners, child] if child.tag in OWNER_TAGS else owners, report)


def _change(element: ET.Element, owners: list[ET.Element]) -> ApiChange:
    owner = owners[-1]
    klass = next((o for o in reversed(owners) if o.tag == "class"), owner)
    class_name = klass.get("fullyQualifiedName", "")
    type_ = element.get("type") or (element.text or "").strip() or "UNKNOWN"
    return ApiChange(class_name=class_name, target=_target(owner, class_name), kind=owner.tag,
                     type=type_, binary_compatible=_flag(element, owner, "binaryCompatible"),
                     source_compatible=_flag(element, owner, "sourceCompatible"))


def _flag(element: ET.Element, owner: ET.Element, name: str) -> bool:
    value = element.get(name)
    if value is None:
        value = owner.get(name)
    return value is not None and value.lower() != "false"


def _target(owner: ET.Element, class_name: str) -> str:
    match owner.tag:
        case "class":
            return class_name
        case "method":
            return f"{class_name}#{owner.get('name', '')}({_params(owner)})"
        case "constructor":
            return f"{class_name}#<init>({_params(owner)})"
        case "field":
            return f"{class_name}#{owner.get('name', '')}"
        case "superclass":
            return f"{class_name}#superclass"
        case _:
            return f"{class_name}#interface:{owner.get('fullyQualifiedName', '')}"


def _params(owner: ET.Element) -> str:
    return ",".join(p.get("type", "") for p in owner.findall("parameters/parameter"))


def _rel(path: Path, cwd: Path) -> str:
    resolved, base = Path(path).resolve(), cwd.resolve()
    if resolved.is_relative_to(base):
        return Path(os.path.relpath(resolved, base)).as_posix()
    return resolved.as_posix()


def _major_bump(report: JapicmpReport) -> bool | None:
    old = _MAJOR.match(report.old_version or "")
    new = _MAJOR.match(report.new_version or "")
    if not (old and new):
        return None
    return int(new.group(1)) > int(old.group(1))


def _breaking(change: ApiChange, level: str) -> bool:
    binary = level in ("binary", "both") and not change.binary_compatible
    source = level in ("source", "both") and not change.source_compatible
    return binary or source


def _collapsed(report: JapicmpReport, level: str) -> set[int]:
    """Indexes of changes hidden behind a breaking CLASS_REMOVED of the same class element."""
    removed = {c.class_name for c in report.changes
               if c.kind == "class" and c.type == "CLASS_REMOVED" and _breaking(c, level)}
    return {i for i, c in enumerate(report.changes) if c.class_name in removed
            and not (c.kind == "class" and c.type == "CLASS_REMOVED")}


def run_api_compat(reports: list[JapicmpReport], cwd: Path, level: str = "both",
                   ignore: tuple[str, ...] = (), allow_major_bump: bool = False,
                   strict: bool = False) -> GateResult:
    if level not in LEVELS:
        raise ApiCompatError(f"--level must be one of {', '.join(LEVELS)}")
    result = GateResult(gate="api-compat", strict=strict)
    counts = dict.fromkeys(("breaking", "binary_incompatible", "source_incompatible",
                            "compatible_changes", "excluded_by_level", "collapsed", "ignored",
                            "allowed_by_major_bump"), 0)
    for report in reports:
        where = _rel(report.path, cwd)
        if not report.classes:
            result.add("warning", "api_report_empty",
                       "no classes compared; check the japicmp includes/excludes", where)
        bump = _major_bump(report) if allow_major_bump else False
        if bump is None:
            result.add("warning", "api_versions_unknown",
                       f"oldVersion={report.old_version!r} newVersion={report.new_version!r}; "
                       "cannot tell a major bump, breaks stay errors", where)
        collapsed = _collapsed(report, level)
        for index, change in enumerate(report.changes):
            if index in collapsed:
                counts["collapsed"] += 1
                continue
            counts["binary_incompatible"] += not change.binary_compatible
            counts["source_incompatible"] += not change.source_compatible
            if change.binary_compatible and change.source_compatible:
                counts["compatible_changes"] += 1
                continue
            if not _breaking(change, level):
                counts["excluded_by_level"] += 1
                continue
            _report_break(result, counts, change, level, where, ignore, bool(bump))
    result.summary.update(counts)
    result.summary.update({"reports": len(reports), "level": level,
                           "classes": sum(r.classes for r in reports)})
    return result


def _report_break(result: GateResult, counts: dict[str, int], change: ApiChange, level: str,
                  where: str, ignore: tuple[str, ...], allowed: bool) -> None:
    false_flags = [name for name, ok in (("binary", change.binary_compatible),
                                         ("source", change.source_compatible)) if not ok]
    message = f"{change.type} {change.target} [{','.join(false_flags)}]"
    if any(fnmatchcase(change.class_name, pattern) for pattern in ignore):
        counts["ignored"] += 1
        result.add("info", "api_change_ignored", message, where)
        return
    counts["breaking"] += 1
    binary = level in ("binary", "both") and not change.binary_compatible
    code = "api_binary_incompatible" if binary else "api_source_incompatible"
    finding_level: Level = "error"
    if allowed:
        counts["allowed_by_major_bump"] += 1
        finding_level = "warning"
    result.add(finding_level, code, message, where)

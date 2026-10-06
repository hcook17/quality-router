"""Shared finding/result shape and text/JSON rendering for harness gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

Level = Literal["error", "warning", "info"]

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class Finding:
    level: Level
    code: str
    message: str
    path: str = ""
    line: int = 0

    def render(self) -> str:
        where = self.path
        if where and self.line:
            where = f"{where}:{self.line}"
        prefix = f"{self.level} {self.code}"
        return f"{prefix} {where} {self.message}" if where else f"{prefix} {self.message}"


@dataclass
class GateResult:
    gate: str
    findings: list[Finding] = field(default_factory=list)
    summary: dict[str, object] = field(default_factory=dict)
    strict: bool = False

    def add(self, level: Level, code: str, message: str, path: str = "", line: int = 0) -> None:
        self.findings.append(Finding(level, code, message, path, line))

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.level == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.level == "warning")

    @property
    def passed(self) -> bool:
        return self.errors == 0 and not (self.strict and self.warnings)

    def exit_code(self) -> int:
        return EXIT_PASS if self.passed else EXIT_FAIL

    def render(self, as_json: bool) -> str:
        if as_json:
            payload = {
                "gate": self.gate,
                "passed": self.passed,
                "errors": self.errors,
                "warnings": self.warnings,
                "summary": self.summary,
                "findings": [asdict(f) for f in self.findings],
            }
            return json.dumps(payload, indent=2, sort_keys=True) + "\n"
        lines = [f.render() for f in self.findings]
        for key in sorted(self.summary):
            lines.append(f"{key}={_scalar(self.summary[key])}")
        verdict = "pass" if self.passed else "fail"
        lines.append(f"gate={self.gate} result={verdict} errors={self.errors} "
                     f"warnings={self.warnings}")
        return "\n".join(lines) + "\n"


def _scalar(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list | dict):
        return json.dumps(value, sort_keys=True)
    return str(value)

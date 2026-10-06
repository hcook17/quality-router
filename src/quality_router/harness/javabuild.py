"""Read the Java release a Maven or Gradle module compiles for, without running the build.

Spring Boot 2.7 modules commonly target Java 8 or 11 (no text blocks);
Boot 3.x and 4.x require 17+. Declarations are read from the nearest
pom.xml / build.gradle(.kts) walking up from a path, stopping at the
repository root.
"""

from __future__ import annotations

import re
from pathlib import Path

_MAVEN = (
    re.compile(r"<maven\.compiler\.release>\s*([^<\s]+)\s*<"),
    re.compile(r"<release>\s*([^<\s]+)\s*</release>"),
    re.compile(r"<java\.version>\s*([^<\s]+)\s*<"),
    re.compile(r"<maven\.compiler\.target>\s*([^<\s]+)\s*<"),
    re.compile(r"<maven\.compiler\.source>\s*([^<\s]+)\s*<"),
)
_MAVEN_PROPERTY = re.compile(r"\$\{([\w.-]+)\}")
_GRADLE = (
    re.compile(r"JavaLanguageVersion\.of\(\s*['\"]?(\d+)"),
    re.compile(r"jvmToolchain\(\s*(\d+)"),
    re.compile(r"\brelease(?:\.set\(|\s*=)\s*['\"]?(\d+)"),
    re.compile(r"\b(?:targetCompatibility|sourceCompatibility)(?:\.set\(|\s*=)\s*"
               r"(?:JavaVersion\.VERSION_([\d_]+)|['\"]?([\d.]+))"),
)
BUILD_FILES = ("pom.xml", "build.gradle.kts", "build.gradle")


def parse_release(value: str) -> int | None:
    """'1.8' -> 8, '11' -> 11, 'VERSION_1_8' style '1_8' -> 8."""
    text = value.strip().replace("_", ".")
    match = re.fullmatch(r"1\.(\d+)|(\d+)(?:\.\d+)*", text)
    if match is None:
        return None
    return int(match.group(1) or match.group(2))


def _maven_release(text: str) -> int | None:
    for pattern in _MAVEN:
        for match in pattern.finditer(text):
            value = match.group(1)
            prop = _MAVEN_PROPERTY.fullmatch(value)
            if prop:
                found = re.search(rf"<{re.escape(prop.group(1))}>\s*([^<\s]+)\s*<", text)
                value = found.group(1) if found else ""
            release = parse_release(value)
            if release is not None:
                return release
    return None


def _gradle_release(text: str) -> int | None:
    for pattern in _GRADLE:
        match = pattern.search(text)
        if match:
            release = parse_release(next(g for g in match.groups() if g))
            if release is not None:
                return release
    return None


def detect_java_release(start: Path) -> tuple[int, Path] | None:
    """(release, build file) from the nearest build file that declares one, else None."""
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    for directory in (current, *current.parents):
        for name in BUILD_FILES:
            build = directory / name
            if not build.is_file():
                continue
            text = build.read_text(encoding="utf-8", errors="replace")
            release = _maven_release(text) if name == "pom.xml" else _gradle_release(text)
            if release is not None:
                return release, build
        if (directory / ".git").exists():
            break
    return None

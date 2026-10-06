"""Java release detection from Maven and Gradle build files (Spring Boot 2.7-4.x layouts)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quality_router.harness.javabuild import detect_java_release, parse_release


@pytest.mark.parametrize("value, release", [
    ("1.8", 8), ("8", 8), ("11", 11), ("17.0.2", 17), ("1_8", 8), ("21", 21),
    ("${x}", None), ("latest", None),
])
def test_parse_release(value: str, release: int | None) -> None:
    assert parse_release(value) == release


@pytest.mark.parametrize("pom, release", [
    ("<properties><java.version>1.8</java.version></properties>", 8),
    ("<properties><maven.compiler.release>21</maven.compiler.release></properties>", 21),
    ("<plugin><configuration><release>17</release></configuration></plugin>", 17),
    ("<properties><maven.compiler.source>11</maven.compiler.source></properties>", 11),
    ("<properties><jdk>11</jdk><maven.compiler.release>${jdk}</maven.compiler.release>"
     "</properties>", 11),
    ("<properties><maven.compiler.release>${missing}</maven.compiler.release>"
     "<java.version>17</java.version></properties>", 17),
])
def test_maven(tmp_path: Path, pom: str, release: int) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "pom.xml").write_text(f"<project>{pom}</project>")
    assert detect_java_release(tmp_path / "src/test/java/A.java") == (release,
                                                                       tmp_path / "pom.xml")


@pytest.mark.parametrize("name, script, release", [
    ("build.gradle", "java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }", 21),
    ("build.gradle.kts", "kotlin { jvmToolchain(17) }", 17),
    ("build.gradle", "sourceCompatibility = JavaVersion.VERSION_1_8", 8),
    ("build.gradle", "sourceCompatibility = '11'", 11),
    ("build.gradle.kts", "java { sourceCompatibility = JavaVersion.VERSION_17 }", 17),
    ("build.gradle.kts", "tasks.withType<JavaCompile> { options.release.set(11) }", 11),
    ("build.gradle", "compileJava { options.release = 8 }", 8),
])
def test_gradle(tmp_path: Path, name: str, script: str, release: int) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / name).write_text(script)
    found = detect_java_release(tmp_path)
    assert found == (release, tmp_path / name)


def test_nearest_declaring_module_wins_and_stops_at_repo_root(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project><java.version>21</java.version></project>")
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "pom.xml").write_text("<project><java.version>11</java.version></project>")
    module = repo / "content-normalize"
    (module / "src/test/java").mkdir(parents=True)
    (module / "pom.xml").write_text("<project><parent/></project>")
    assert detect_java_release(module / "src/test/java/X.java") == (11, repo / "pom.xml")
    (repo / "pom.xml").write_text("<project/>")
    assert detect_java_release(module / "src/test/java") is None

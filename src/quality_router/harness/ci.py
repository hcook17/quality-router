"""CI templates stamped by `qr init --ci`. CI runs the build; qr only reads its reports.

The JDK defaults to the release the repository's build file declares (Spring
Boot 2.7 modules are often Java 8/11; Boot 3.x/4.x need 17+), else 17.
"""

from __future__ import annotations

from pathlib import Path

from quality_router.harness.javabuild import detect_java_release

GITHUB_WORKFLOW_PATH = ".github/workflows/qr-harness.yml"
GITHUB_MAVEN_PATH = GITHUB_WORKFLOW_PATH
DEFAULT_CI_JAVA = 17

_HEAD = """\
# Stamped by `qr init --ci @KIND@`. Edit freely; qr will not overwrite it.
# @TOOL@ builds and writes reports; qr gates read them (qr never runs @TOOL@).
# JDK @JAVA@: @JAVA_FROM@. Pin a JaCoCo that officially supports it:
# Java 21 from 0.8.11, 23-24 from 0.8.13, 25 from 0.8.14, 26 from 0.8.15.
name: qr-harness

on:
  pull_request:

permissions:
  contents: read

jobs:
  harness:
    runs-on: ubuntu-latest
    env:
      QR_PACKAGE: ${{ vars.QR_PACKAGE || 'git+https://github.com/hcook17/quality-router@main' }}
      BASE_REF: origin/${{ github.base_ref }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "@JAVA@"
          cache: @CACHE@
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install qr
        run: python -m pip install "$QR_PACKAGE"
      - name: Acceptance lock
        if: hashFiles('.quality-router/acceptance.lock.json') != ''
        run: qr gate acceptance --base "$BASE_REF"
"""

_MAVEN_BUILD = """\
      - name: Build with JaCoCo
        id: build
        run: mvn -B verify
      - name: Test failure feedback
        if: failure() && steps.build.outcome == 'failure'
        run: >-
          qr feedback junit --sources .
          --reports '**/target/surefire-reports/TEST-*.xml' '**/target/failsafe-reports/TEST-*.xml'
      - name: Diff coverage
        run: qr gate diff-coverage --base "$BASE_REF" --jacoco '**/target/site/jacoco/jacoco.xml'
"""

_GRADLE_BUILD = """\
      # The jacoco plugin writes XML only with: jacocoTestReport { reports { xml.required = true } }
      - name: Build with JaCoCo
        id: build
        run: ./gradlew --no-daemon check jacocoTestReport
      - name: Test failure feedback
        if: failure() && steps.build.outcome == 'failure'
        run: qr feedback junit --sources . --reports '**/build/test-results/**/TEST-*.xml'
      - name: Diff coverage
        run: qr gate diff-coverage --base "$BASE_REF" --jacoco '**/build/reports/jacoco/**/*.xml'
"""

_TAIL = """\
      - name: Test oracles
        run: qr gate test-oracles --base "$BASE_REF"
      - name: Instruction files
        run: qr lint instructions
      - name: Spec trace
        if: hashFiles('specs/**/*.md') != ''
        run: qr spec trace --spec 'specs/**/*.md' --tests .
      - name: Contract diff
        if: hashFiles('contracts/**/*.json') != ''
        shell: bash
        run: |
          status=0
          for f in contracts/*.json; do
            if git cat-file -e "$BASE_REF:$f" 2>/dev/null; then
              qr contracts diff --old "git:$BASE_REF:$f" --new "$f" || status=1
            fi
          done
          exit $status
"""

TEMPLATES = {
    "github-maven": (GITHUB_WORKFLOW_PATH, "Maven", "maven", _MAVEN_BUILD),
    "github-gradle": (GITHUB_WORKFLOW_PATH, "Gradle", "gradle", _GRADLE_BUILD),
}


def ci_java(root: Path, java: int | None = None) -> tuple[int, str]:
    """(JDK, why): the flag, else the build file's release, else DEFAULT_CI_JAVA."""
    if java is not None:
        return java, "from --ci-java"
    found = detect_java_release(root)
    if found is None:
        return DEFAULT_CI_JAVA, "default; no release declared in pom.xml/build.gradle"
    release, build = found
    try:
        where = build.relative_to(root).as_posix()
    except ValueError:
        where = str(build)
    return release, f"from {where}"


def render_ci(kind: str, java: int, java_from: str) -> str:
    _, tool, cache, build = TEMPLATES[kind]
    text = _HEAD + build + _TAIL
    for key, value in (("@KIND@", kind), ("@TOOL@", tool), ("@CACHE@", cache),
                       ("@JAVA_FROM@", java_from), ("@JAVA@", str(java))):
        text = text.replace(key, value)
    return text


def stamp_ci(root: Path, kind: str, java: int | None = None) -> bool:
    """Write the CI template unless the file exists. Returns True when written."""
    rel = TEMPLATES[kind][0]
    target = root / rel
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_ci(kind, *ci_java(root, java)), encoding="utf-8")
    return True

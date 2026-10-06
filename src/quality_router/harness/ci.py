"""CI templates stamped by `qr init --ci`. CI runs the build; qr only reads its reports."""

from __future__ import annotations

from pathlib import Path

GITHUB_MAVEN_PATH = ".github/workflows/qr-harness.yml"

GITHUB_MAVEN = """\
# Stamped by `qr init --ci github-maven`. Edit freely; qr will not overwrite it.
# Maven builds and writes reports; qr gates read them (qr never runs Maven).
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
          java-version: "21"
          cache: maven
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install qr
        run: python -m pip install "$QR_PACKAGE"
      - name: Build with JaCoCo
        run: mvn -B verify
      - name: Diff coverage
        run: qr gate diff-coverage --base "$BASE_REF" --jacoco '**/target/site/jacoco/jacoco.xml'
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

TEMPLATES = {"github-maven": (GITHUB_MAVEN_PATH, GITHUB_MAVEN)}


def stamp_ci(root: Path, kind: str) -> bool:
    """Write the CI template unless the file exists. Returns True when written."""
    rel, body = TEMPLATES[kind]
    target = root / rel
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return True

"""Deterministic harness gates (phase 3).

Each gate is a Python predicate over files the repo or CI already has:
JaCoCo XML, unified diffs, JUnit sources, specs, contracts, policy. No
gate runs Maven/Gradle, calls an LLM, or writes outside its target.
Evidence per gate: docs/design/phase-3-harness.md.
"""

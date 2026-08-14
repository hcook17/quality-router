"""Removable quality constituents. Disconnected means no-op."""

from __future__ import annotations

REMOVABLE_CONSTITUENTS = ("sonar", "gortex", "semgrep", "spectral", "arxiv")


def disconnected_noop(reason: str) -> str:
    return f"disconnected (no-op): {reason}"

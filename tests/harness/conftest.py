from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from harness.helpers import git


@pytest.fixture
def write(tmp_path: Path) -> Callable[[str, str], Path]:
    def _write(rel: str, text: str) -> Path:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    return root

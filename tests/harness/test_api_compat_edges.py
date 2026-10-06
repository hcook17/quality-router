"""Implementation edges of `qr gate api-compat` / `qr init --graph gortex` not in the locked set."""

from __future__ import annotations

from pathlib import Path

import pytest

from quality_router.harness.api_compat import ApiCompatError, parse_japicmp, run_api_compat
from quality_router.init import InitConfig, InitError, run_init

REMOVED = ('<japicmp><classes><class fullyQualifiedName="com.acme.Item">'
           '<methods><method name="size"><compatibilityChanges>'
           '<compatibilityChange type="METHOD_REMOVED" binaryCompatible="false"'
           ' sourceCompatible="false"/></compatibilityChanges></method></methods>'
           "</class></classes></japicmp>")


def test_change_without_owner_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "r.xml"
    path.write_text('<japicmp><compatibilityChanges><compatibilityChange type="X"'
                    ' binaryCompatible="false"/></compatibilityChanges></japicmp>',
                    encoding="utf-8")
    assert parse_japicmp(path).changes == []


def test_report_outside_cwd_uses_absolute_path(tmp_path: Path) -> None:
    path = tmp_path / "lib" / "r.xml"
    path.parent.mkdir()
    path.write_text(REMOVED, encoding="utf-8")
    (tmp_path / "svc").mkdir()
    result = run_api_compat([parse_japicmp(path)], tmp_path / "svc")
    assert [f.path for f in result.findings] == [path.resolve().as_posix()]


def test_module_api_rejects_unknown_level(tmp_path: Path) -> None:
    path = tmp_path / "r.xml"
    path.write_text(REMOVED, encoding="utf-8")
    with pytest.raises(ApiCompatError, match="--level"):
        run_api_compat([parse_japicmp(path)], tmp_path, level="api")


def test_invalid_dep_slug_raises_before_writing(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="--workspace-dep"):
        run_init(InitConfig(cwd=tmp_path, graph="gortex", workspace="s",
                            workspace_deps=[("a b", ".")]))
    assert list(tmp_path.iterdir()) == []

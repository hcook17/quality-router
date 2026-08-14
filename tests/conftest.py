from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_host_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_QUALITY_ROOT", raising=False)
    monkeypatch.delenv("SONAR_PORT", raising=False)
    monkeypatch.delenv("SONARQUBE_URL", raising=False)
    monkeypatch.delenv("GITNEXUS_HOOKS", raising=False)
    monkeypatch.delenv("QUALITY_ROUTER_SECRETS", raising=False)


@pytest.fixture
def local_quality_root(tmp_path: Path) -> Path:
    root = tmp_path / "local-quality"
    root.mkdir()
    (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (root / "install.ps1").write_text("# local installer\n", encoding="utf-8")
    (root / "install.sh").write_text("# local installer\n", encoding="utf-8")
    return root

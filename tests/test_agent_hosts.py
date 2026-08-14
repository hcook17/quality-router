from pathlib import Path

from quality_router.agent_hosts import product_secrets_dir


def test_product_secrets_dir_uses_env_flag(tmp_path: Path) -> None:
    flagged = tmp_path / "qr-secrets"
    assert product_secrets_dir({"QUALITY_ROUTER_SECRETS": str(flagged)}) == flagged


def test_product_secrets_dir_default_is_xdg() -> None:
    path = product_secrets_dir({})
    assert path == Path.home() / ".config" / "quality-router" / "secrets"


def test_product_secrets_dir_none_environ_uses_xdg() -> None:
    assert product_secrets_dir() == Path.home() / ".config" / "quality-router" / "secrets"

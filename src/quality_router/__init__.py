"""quality-router: CLI mediator for independent quality constituents."""

__version__ = "0.1.0"


def main() -> None:
    from quality_router.cli import entrypoint

    entrypoint()

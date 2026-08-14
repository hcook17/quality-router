"""qr / quality-router entry. Phase 1: help, status, install wrap."""

from __future__ import annotations

import json
import os
import sys
import textwrap
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from collections.abc import Sequence
from pathlib import Path

from quality_router import __version__
from quality_router.host_bind import bind_host
from quality_router.init import ADAPTERS, InitConfig, run_init
from quality_router.install_wrap import (
    build_installer_argv,
    invoke_installer,
    prepare_sonar_install,
)
from quality_router.status_report import report_status

ROOT_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr --help
      qr status
      qr install --sonar --dry-run
      qr install --sonar --hooks --no-gitnexus

    Constituents stay removable. A disconnected constituent no-ops.
    Local Sonar only. Do not irm|iex. Tokens stay in the environment.
    Not locked to one agent host. Not an MCP aggregator. Not a local-LLM host.
    """
)

STATUS_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr status
      qr status --root ~/dev/local-quality
    """
)

INSTALL_EPILOG = textwrap.dedent(
    """\
    Examples:
      qr install --sonar
      qr install --sonar --dry-run
      qr install --sonar --root ~/dev/local-quality
      qr install --sonar --hooks --no-gitnexus
      qr install --sonar --skip-bootstrap

    Wraps local-quality install.ps1 / install.sh (flags > env > defaults).
    Does not download-execute. Does not set GITNEXUS_HOOKS=0.
    """
)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="qr",
        description=(
            "CLI mediator for independent quality constituents "
            "(local Sonar, Gortex, hooks, Spectral, Semgrep, arXiv). "
            "Not locked to one agent host. Not an MCP aggregator. Not a local-LLM host."
        ),
        epilog=ROOT_EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"quality-router {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_status_parser(subparsers)
    _add_install_parser(subparsers)
    _add_init_parser(subparsers)
    return parser


def _add_bind_flags(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=None,
        help="local-quality directory (flag > LOCAL_QUALITY_ROOT > ~/dev/local-quality).",
    )
    parser.add_argument(
        "--sonar-port",
        type=int,
        default=None,
        help="Published Sonar port (flag > SONAR_PORT > 9000).",
    )
    parser.add_argument(
        "--sonar-mcp-url",
        default=None,
        help="Local Sonar MCP URL (flag > SONARQUBE_URL if local > host.docker.internal).",
    )


def _add_status_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "status",
        help="Show constituent presence from local files and PATH (no org Sonar probe).",
        epilog=STATUS_EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    _add_bind_flags(parser)
    parser.set_defaults(handler=cmd_status)


def _add_install_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "install",
        help="Wrap local-quality install.ps1 / install.sh for selected constituents.",
        epilog=INSTALL_EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sonar",
        action="store_true",
        help="Run the local-quality Sonar CE installer (loopback / host.docker.internal only).",
    )
    parser.add_argument(
        "--hooks",
        action="store_true",
        help="Accepted in Phase 1; hooks runner is stamped by qr init.",
    )
    parser.add_argument(
        "--no-gitnexus",
        action="store_true",
        help="Keep GitNexus disconnected. Does not set GITNEXUS_HOOKS=0.",
    )
    _add_bind_flags(parser)
    parser.add_argument(
        "--reset-volume",
        action="store_true",
        help="Pass through to the installer (compose down -v and local Sonar secrets).",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Bind paths without running bootstrap.ps1 / bootstrap.sh.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print installer argv as JSON; do not execute.",
    )
    parser.set_defaults(handler=cmd_install)


INIT_EPILOG = textwrap.dedent(
    """\\
    Examples:
      qr init
      qr init --host cursor
      qr init --host cursor --no-gitnexus
      qr init --graph gortex
      qr init --graph gortex --workspace my-service
      qr init --graph gortex --workspace-dep other-svc --module services/shared

    Stamps a portable quality rule, hooks runner, and gitnexus off-marker.
    Optional --host adapters stamp that host's rule/hooks files only.
    Optional --graph gortex writes .gortex.yaml (no-op if gortex not on PATH).
    Does not write mcp.json. Does not set GITNEXUS_HOOKS=0. Idempotent.
    """
)


def _add_init_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Stamp portable quality rule, hooks runner, and "
        "gitnexus off-marker into any checkout.",
        epilog=INIT_EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        choices=list(ADAPTERS.keys()),
        default=None,
        help="Optional host adapter (cursor, vscode, claude-code). Default: portable only.",
    )
    parser.add_argument(
        "--graph",
        choices=["gortex"],
        default=None,
        help="Optional constituent graph (gortex). No-op if gortex not on PATH.",
    )
    parser.add_argument(
        "--workspace",
        default=None,
        help="Gortex workspace slug for --graph gortex. Default: directory basename.",
    )
    parser.add_argument(
        "--workspace-dep",
        default=None,
        action="append",
        help="Opt-in cross_workspace_deps for "
        "--graph gortex. Repeatable: --workspace-dep "
        "<slug> --module <path>.",
    )
    parser.add_argument(
        "--module",
        default=None,
        help="Module path paired with the preceding --workspace-dep.",
    )
    parser.add_argument(
        "--no-gitnexus",
        action="store_true",
        help="Write the gitnexus off-marker. Does not set GITNEXUS_HOOKS=0.",
    )
    parser.set_defaults(handler=cmd_init)


def _host_from_args(args: Namespace):
    root = str(args.root) if args.root is not None else None
    return bind_host(
        root_flag=root,
        sonar_port_flag=args.sonar_port,
        sonar_mcp_url_flag=args.sonar_mcp_url,
    )


def cmd_status(args: Namespace) -> int:
    bind = _host_from_args(args)
    sys.stdout.write(
        report_status(
            bind,
            cwd=Path.cwd(),
            windows=sys.platform == "win32",
            environ=os.environ,
        )
    )
    return 0


def cmd_install(args: Namespace) -> int:
    if not (args.sonar or args.hooks or args.no_gitnexus):
        print(
            "Error: select at least one constituent (--sonar, --hooks, --no-gitnexus).",
            file=sys.stderr,
        )
        print("  qr install --sonar", file=sys.stderr)
        return 2
    if args.hooks:
        print("hooks=deferred_to_qr_init")
    if args.no_gitnexus:
        print("gitnexus_off_marker=deferred_to_qr_init")
    if not args.sonar:
        return 0
    return _run_sonar_install(args)


def cmd_init(args: Namespace) -> int:
    """Stamp portable + optional host/graph stamps into cwd."""
    # Collect workspace deps (repeatable --workspace-dep with --module)
    deps: list[tuple[str, str]] = []
    if args.workspace_dep:
        for dep_slug in args.workspace_dep:
            deps.append((dep_slug, args.module or "."))

    config = InitConfig(
        cwd=Path.cwd(),
        host=args.host,
        graph=args.graph,
        workspace=args.workspace,
        workspace_deps=deps,
        no_gitnexus=args.no_gitnexus,
    )
    run_init(config)
    return 0


def _run_sonar_install(args: Namespace) -> int:
    bind = _host_from_args(args)
    try:
        prepare_sonar_install(bind)
        argv = build_installer_argv(
            bind,
            reset_volume=args.reset_volume,
            skip_bootstrap=args.skip_bootstrap,
            windows=sys.platform == "win32",
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("  qr install --sonar --root <path-to-local-quality>", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"dry_run={json.dumps(argv)}")
        return 0
    return invoke_installer(argv)


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    return args.handler(args)


def entrypoint() -> None:
    raise SystemExit(run())

# Phase 1 CLI (spec gate)

Ollama/Hermes spike is out of scope. `qr init` is Phase 2 (implemented).

**Status:** implemented under `src/` + `tests/`. Host-agnostic status
probes included (`agent_host_lock=none`). `uv.lock` pins pytest/ruff.
Next: `--json` on report commands, then `enable` / `disable`.

## Commands

| Command | Behavior |
| --- | --- |
| `qr --help` / `quality-router --help` | List `status` and `install`. |
| `qr status` | Report host bind + removable constituents. Disconnected constituents no-op. |
| `qr install --sonar` | Wrap `$LOCAL_QUALITY_ROOT/install.ps1` (Windows) or `install.sh` (POSIX). |

## Host bind (flags > env > defaults)

| Value | Flag | Env | Default |
| --- | --- | --- | --- |
| Root | `--root` | `LOCAL_QUALITY_ROOT` | `~/dev/local-quality` |
| Port | `--sonar-port` | `SONAR_PORT` | `9000` |
| MCP URL | `--sonar-mcp-url` | `SONARQUBE_URL` | `http://host.docker.internal:<port>` |

## Install wrap

- Invoke the on-disk installer with `-File` / argv. Never `irm \| iex`, never `shell=True`.
- `--reset-volume` / `--skip-bootstrap` map to the installer switches.
- `--sonar-mcp-url` must be local (`127.0.0.1`, `localhost`, `host.docker.internal`). Do not probe org Sonar.
- `--hooks` and `--no-gitnexus` are accepted and reported; stamping is `qr init`. Never set `GITNEXUS_HOOKS=0`.
- Tokens stay in the environment (or `QUALITY_ROUTER_SECRETS`). This tree does not write `mcp.json` for any host.

## Status

- Local listen probe is `127.0.0.1:<port>` only.
- Constituents: sonar, gortex, semgrep, spectral, arXiv. Missing → `disconnected (no-op)`.
- `agent_host_lock=none`. MCP token scan covers portable and host catalogs
  (`.quality-router/mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, `.mcp.json`).
- No visualization MCP. No Hermes/Ollama router.

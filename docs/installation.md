# Installation

This fork is installable in Codex, Claude Code, OpenCode V1, and OpenCode V2 (TUI, desktop, and web).

The generated packages live under `plugins/`. They are built from `skills/` and `docs/skills/`; do not edit the packaged copies by hand.

## Prerequisites

- `git`
- Python 3.12+
- Node.js and a package manager for the site only
- one supported AI tool

Optional:

- `pnpm` for the production site build
- `agent-browser` for exact damage, KO, and survival calculations

## Codex

```bash
git clone https://github.com/felipesuarez-dev/vgc-coach.git
cd vgc-coach
python3 tools/build_plugins.py build
python3 tools/install_codex_plugin.py
```

Restart Codex after install. The installer copies the generated package to `~/plugins/vgc-coach-codex` and writes the local marketplace entry.

Verify:

```bash
ls ~/.agents/plugins/marketplace.json ~/plugins/vgc-coach-codex/.codex-plugin/plugin.json
```

## Claude Code

```bash
claude plugin marketplace add felipesuarez-dev/vgc-coach \
  --sparse .claude-plugin plugins
claude plugin install vgc-coach-claude@vgc-coach
```

Verify:

```bash
claude plugin details vgc-coach-claude@vgc-coach
```

Update:

```bash
claude plugin marketplace update vgc-coach
claude plugin update vgc-coach-claude@vgc-coach
```

If Claude reports a new version, run `/reload-plugins`.

## OpenCode V1

OpenCode 1.x uses the generated plugin entry in `opencode.json`:

```json
{
  "plugin": ["vgc-coach-opencode@git+https://github.com/felipesuarez-dev/vgc-coach.git"]
}
```

Restart OpenCode 1.x after editing the config.

## OpenCode V2, Desktop, and Web

OpenCode V2 uses the `skills` field, not the V1 plugin shim. Clone the fork and point `skills` at the generated package:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/vgc-coach/plugins/vgc-coach-opencode/skills"]
}
```

Use the same config for the TUI, the desktop app, and the web UI. V2 reloads configuration without a restart; use `/reload` if the skill list does not refresh.

### OpenCode Web

The web UI is served by the same OpenCode V2 server as the TUI:

```bash
opencode pair
```

Open the printed link, or use the address from:

```bash
opencode service status
```

If you run a standalone server:

```bash
opencode serve --hostname 0.0.0.0 --port 4096
```

For an HTTP client, V2 uses Basic auth with the username `opencode` and the server password. Do not put the password in this repository.

After changing the skills directory, reload the server location:

```bash
curl -u opencode:<password> -X POST http://127.0.0.1:4096/api/location/reload
curl -u opencode:<password> http://127.0.0.1:4096/api/skill
```

The skill list should include the ten `vgc-*` skills.

## Update

For any runtime:

```bash
cd vgc-coach
git pull
python3 tools/build_plugins.py build
```

Then reload the runtime:

- Codex: reinstall with `python3 tools/install_codex_plugin.py` and restart.
- Claude Code: `claude plugin update vgc-coach-claude@vgc-coach`.
- OpenCode V1: restart.
- OpenCode V2, desktop, or web: `/reload` or `POST /api/location/reload`.

## Uninstall

- Codex: remove `~/plugins/vgc-coach-codex` and its entry from `~/.agents/plugins/marketplace.json`.
- Claude Code: `claude plugin uninstall vgc-coach-claude@vgc-coach`.
- OpenCode V1: remove the `plugin` entry.
- OpenCode V2, desktop, or web: remove the `skills` path.

## Repository Validation

See [Validation](./validation.md) for the full command list.

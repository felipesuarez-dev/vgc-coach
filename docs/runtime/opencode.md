# OpenCode Runtime

OpenCode support in this repo covers OpenCode V1 and OpenCode V2 (TUI, desktop, and web). Both use the same shared skill packages; only the loading mechanism differs.

## Loading Model

- Repo-wide product and workflow rules still live in `AGENTS.md`.
- `opencode.json` loads `docs/runtime/opencode.md` through the `instructions` field.
- OpenCode scans `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` for project skills.
- The repo keeps unique wrapper names under `.opencode/skills/opencode-vgc-*/` so the project wrappers do not collide with the packaged `vgc-*` names.
- `opencode.json` denies the shared `vgc-*` names and allows only `opencode-vgc-*` for repo-local source work.
- The installable package lives under `plugins/vgc-coach-opencode/`.

## V1 Install

OpenCode 1.x loads the generated plugin from `opencode.json`:

```json
{
  "plugin": ["vgc-coach-opencode@git+https://github.com/felipesuarez-dev/vgc-coach.git"]
}
```

Restart OpenCode 1.x after editing the config.

## V2, Desktop, and Web Install

OpenCode V2 uses the `skills` field:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/vgc-coach/plugins/vgc-coach-opencode/skills"]
}
```

The TUI, desktop app, and web UI all read the same global config. V2 reloads configuration without a restart; use `/reload` if the skill list does not refresh.

The web UI is served by the same V2 server:

```bash
opencode pair
```

Open the printed link, or use the address from `opencode service status`. A standalone server can be started with:

```bash
opencode serve --hostname 0.0.0.0 --port 4096
```

For HTTP checks against a standalone server, V2 uses Basic auth with the username `opencode` and the server password:

```bash
curl -u opencode:<password> http://127.0.0.1:4096/api/skill
curl -u opencode:<password> -X POST http://127.0.0.1:4096/api/location/reload
```

Do not add the password to the repository.

## Adapter Rules

- Reuse `AGENTS.md`, `skills/`, `data/fixtures/`, and `data/rubrics/`.
- Keep OpenCode-specific behavior in this file, `.opencode/commands/`, and thin `.opencode/skills/opencode-vgc-*/` wrappers only.
- Keep `.opencode/skills/` as a discovery layer, not a second skill implementation tree.
- Avoid OpenCode-only forks of the coaching logic unless a real runtime limitation forces it.
- The V1 plugin shim is not used by V2. Do not present it as a V2 install path.

## Current-Info And Sourcing Rules

- Current format, legality, and meta claims are time-sensitive; verify them live before presenting them as current.
- Prefer official rules sources over community sources.
- Use community sources for usage, trends, and archetype interpretation only after format truth is locked.
- Use absolute dates when clarifying "current" claims.
- Distinguish sourced facts from inference explicitly.
- Use `docs/skills/shared/references/current-regulation.md`; do not link a dated regulation note from a skill.

## Tooling Boundary

- `vgc-calcs-assistant` exact-browser support depends on local `agent-browser` plus `python3 tools/browser_damage_calc.py`.
- In `battle-ready` mode, `vgc-team-builder` uses live cores and recent top teams as benchmark inputs, then hands narrow benchmark questions to `vgc-calcs-assistant`.
- Exact damage, KO, and survival support is only acceptable when the local tool chain is available and working.
- If OpenCode cannot use the local browser/tool path, say the exact path is blocked or unverified and fall back to assumption-framed guidance.
- Speed checks remain assumption-framed unless a verified exact backend is added later.
- `export-ready` output must downgrade when named items or moves are not verified.

## Validation Expectations

- When changing shared skill logic, validate against the fixed eval cases and rubrics.
- For OpenCode-specific support changes, verify project command discovery, wrapper-skill discovery, shared file reads, and one representative command invocation.
- For V2 and web, verify the `vgc-*` skills appear in the skill list.
- Use [OpenCode Team Builder Live Checklist](../evals/opencode-team-builder-live-checklist.md) when pressure-testing `vgc-team-builder`.

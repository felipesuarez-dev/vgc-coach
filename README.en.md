# VGC Coach

[Español](./README.md)

VGC Coach is an open-source coaching assistant for Pokemon VGC (Video Game Championships). It packages coaching logic into *skills* that run inside Codex, Claude Code, and OpenCode. Ask in plain language for a team, a meta snapshot, a lead plan, a team audit, or a replay review.

It is not a standalone app or a ladder client. The shared coaching logic lives in this repository and is distributed as generated packages for each runtime.

## Project Status

- License: [Apache-2.0](./LICENSE)
- Fork of [NoahJenkins/vgc-coach](https://github.com/NoahJenkins/vgc-coach)
- Contributions: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Security: [SECURITY.md](./SECURITY.md)
- Documentation: [docs/README.md](./docs/README.md)

This fork keeps the upstream attribution and adds a verified source stack, a regulation-transition workflow, and a stricter team-building skill.

## Installation

Installable packages are generated from `skills/` and `docs/skills/`. Do not edit the copies under `plugins/` by hand.

### Codex

```bash
git clone https://github.com/felipesuarez-dev/vgc-coach.git
cd vgc-coach
python3 tools/build_plugins.py build
python3 tools/install_codex_plugin.py
```

Restart Codex after install.

### Claude Code

```bash
claude plugin marketplace add felipesuarez-dev/vgc-coach \
  --sparse .claude-plugin plugins
claude plugin install vgc-coach-claude@vgc-coach
```

Verify:

```bash
claude plugin details vgc-coach-claude@vgc-coach
```

### OpenCode V1

Add the generated plugin to `opencode.json`:

```json
{
  "plugin": ["vgc-coach-opencode@git+https://github.com/felipesuarez-dev/vgc-coach.git"]
}
```

Restart OpenCode 1.x after editing the config.

### OpenCode V2, Desktop, and Web

OpenCode V2 uses the `skills` field, not the V1 plugin shim. Clone the repository and point `skills` at the generated package:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/vgc-coach/plugins/vgc-coach-opencode/skills"]
}
```

The TUI, desktop app, and web UI read the same global config. V2 reloads configuration without a restart; use `/reload` if the skill list does not refresh.

Open the web UI with:

```bash
opencode pair
```

Open the printed link. For a standalone server:

```bash
opencode serve --hostname 0.0.0.0 --port 4096
```

Full instructions, including HTTP verification and server reload, are in [docs/installation.md](./docs/installation.md).

## Sources

The source contract lives in
[docs/skills/shared/references/live-source-registry.yaml](./docs/skills/shared/references/live-source-registry.yaml)
and renders to
[live-source-map.md](./docs/skills/shared/references/live-source-map.md).

Summary:

- **Official**: Pokemon HOME regulation, official roster, Championship Series calendar and results.
- **Tournament meta**: infovgc, LabMaus, and Limitless.
- **Broader meta**: PokeStats and Smogon.
- **Supporting sets**: Pikalytics, PokeBase, and Pokepaste.
- **Events and standings**: PokeData.
- **Editorial**: Victory Road.

ChampionsMeta is retired (HTTP 402, `DEPLOYMENT_DISABLED`). ChampionsLab is outside the automated stack because its data lives in the Next.js RSC payload.

LabMaus omits its intermediate certificate and requires `Origin`/`Referer`. The repository includes a fetcher that completes the TLS chain, verifies the hostname, and pins the certificate fingerprint. Do not use a generic `curl -k` as the workaround.

Full table, TTLs, fallbacks, and probe results: [docs/sources.md](./docs/sources.md).

## How Team Building Works

```text
official regulation + roster
  -> meta snapshot with fallbacks
  -> real 2/3/4 and 4/5/6 cores
  -> one six-mon identity
  -> legality ledger
  -> capped benchmarks
  -> battle-ready spreads
  -> playbook from the chosen cores
  -> synergy and matchup audit
  -> export gate
```

Key rules:

- A `current-field` recommendation needs regulation, roster, one tournament source, and one broader source.
- The official roster verifies species, not items, moves, abilities, or mechanics.
- 2/3/4 cores come from Limitless; LabMaus publishes 4/5/6 and does not get invented 2/3 cores.
- Benchmarks and spreads are blocked while legality is unverified.
- `export-ready` is used only when legality and benchmarks are complete. Do not invent a Champions import string.

Full guide: [docs/team-building.md](./docs/team-building.md).

## Current Regulation and M-D

- **M-C** is current: `2026-09-09 02:00 UTC` through `2026-12-02 01:59 UTC`.
- **M-D** is `upcoming`: `2026-12-02 02:00 UTC` through `2027-03-03 01:59 UTC`.
- The M-D roster is not published yet. It is not added until the official page links it.
- Skills use `current-regulation.md`, not a dated note. Activation changes one wrapper.
- `python3 tools/resolve_regulation.py --check-registry` detects the real state and compares it with the registry.
- Runbook: [docs/maintenance/regulation-transition.md](./docs/maintenance/regulation-transition.md).

## Validation

```bash
python3 tools/validate.py
```

The full scope runs tests, the registry render check, offline probe coverage, format freshness, plugin drift, site trust data, and the production site build.

Individual commands and live probes: [docs/validation.md](./docs/validation.md).

## Maintenance

- [Regulation transition runbook](./docs/maintenance/regulation-transition.md)
- [Dependabot rebase runbook](./docs/maintenance/dependabot-rebase.md)

## Coaching Tools

Core skills:

1. `vgc-meta-research`
2. `vgc-team-builder`
3. `vgc-team-audit`
4. `vgc-lead-planner`
5. `vgc-battle-review`

Support skills:

- `vgc-format-verifier`
- `vgc-source-verifier`
- `vgc-calcs-assistant`
- `vgc-opponent-scout`
- `vgc-practice-journal`

## Repository Layout

```text
vgc-coach/
├── AGENTS.md
├── LICENSE
├── NOTICE
├── README.md
├── README.en.md
├── docs/
│   ├── README.md
│   ├── installation.md
│   ├── sources.md
│   ├── team-building.md
│   ├── validation.md
│   ├── runtime/
│   └── skills/
├── skills/
├── plugins/          # generated
├── data/
│   ├── fixtures/evals/
│   ├── rubrics/
│   └── snapshots/
├── tools/
└── site/
```

## License and Attribution

Apache-2.0. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE).

- Upstream: [NoahJenkins/vgc-coach](https://github.com/NoahJenkins/vgc-coach)
- Endpoint and TTL research: [VGC-Reporter](https://github.com/felipesuarez-dev/VGC-Reporter) (MIT)

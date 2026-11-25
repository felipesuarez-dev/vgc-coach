# VGC Coach Documentation

This directory holds the product and contributor documentation.

## Start Here

- [Installation](./installation.md) — Codex, Claude Code, OpenCode V1, OpenCode V2, desktop, and web.
- [Team Building](./team-building.md) — the team-building pipeline, legality ledger, benchmarks, playbook, and export gate.
- [Live Sources](./sources.md) — source roles, TTLs, fallbacks, probe results, and excluded sources.
- [Validation](./validation.md) — full and focused checks, live probes, the regulation resolver, and evals.

## Runtime Notes

- [Codex](./runtime/codex.md)
- [Claude Code](./runtime/claude-code.md)
- [OpenCode](./runtime/opencode.md)

## Skills and Evals

- `skills/` is the canonical editable source for coaching behavior.
- `docs/skills/` holds supporting references and examples used by the skills.
- `data/fixtures/evals/` holds fixed eval cases.
- `data/rubrics/` holds scoring rubrics.
- `docs/evals/` holds live checklists and the local eval workflow.

## Maintenance

- [Regulation Transition](./maintenance/regulation-transition.md)
- [Dependabot Rebase](./maintenance/dependabot-rebase.md)

## Data and Site

- `data/snapshots/` holds dated regulation snapshots.
- `site/` holds the Vite site.
- `plugins/` holds generated runtime packages. Do not edit them by hand.

## License and Attribution

VGC Coach is Apache-2.0. This fork keeps the upstream attribution to
[NoahJenkins/vgc-coach](https://github.com/NoahJenkins/vgc-coach).
Endpoint and TTL research was informed by
[VGC-Reporter](https://github.com/felipesuarez-dev/VGC-Reporter) (MIT).

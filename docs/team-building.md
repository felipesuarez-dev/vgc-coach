# Team Building

`vgc-team-builder` builds one practical Pokemon Champions team around a real user goal. It is deliberately narrow: one primary six, one coherent plan, and honest confidence labels.

## Pipeline

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

## 1. Lock Format and Roster

Read the current regulation from
[`current-regulation.md`](./skills/shared/references/current-regulation.md) and the
shared [live source map](./skills/shared/references/live-source-map.md).

A `current-field recommendation` needs:

- current official regulation
- current official roster
- one tournament-focused source
- one broader usage source

If the roster is missing, species legality is unverified. If any required source is missing, the build is an `inference-heavy early read`.

M-D was announced on November 25, 2026 and starts on December 2, 2026. It is `upcoming`; do not use it for present-tense coaching before the start. The official roster is not published yet.

## 2. Meta Snapshot and Fallbacks

Keep the snapshot short:

```text
Official: M-C, 2026-09-09 to 2026-12-02 UTC; roster 262 entries
Tournament: Limitless, fetched 2026-11-25, 76 standings with decklists
Broader: Smogon 2026-10 chaos
Fallbacks: infovgc down -> Limitless
Label: current-field recommendation
```

Name the failed source and the replacement. Do not claim a source was checked when it returned 403 or failed.

## 3. Core Grounding

Use real shells:

- **Limitless**: count 2-mon, 3-mon, and 4-mon cores from top standings decklists. State the event, date, and sample.
- **LabMaus**: use the 4-mon, 5-mon, and 6-mon compositions from `/api/top_teams`. Do not invent 2-mon or 3-mon LabMaus cores.
- **infovgc**: tournament usage, adjusted win rate, Top 8 index, recent teams, and trends.

Keep `Targeted Meta Cores and Teams` to 3 to 5 entries. Name the source and date for every entry. Use the cores in slot selection, benchmarks, and matchup framing.

## 4. Legality Ledger

Build the ledger before locking items, moves, spreads, or exports:

| Slot | Species | Species source | Item | Ability | Moves | Mechanics | Export |
|---|---|---|---|---|---|---|---|

Rules:

- Species: current official roster.
- Items, abilities, moves, mechanics: separate evidence.
- Use `verified`, `partial`, or `unverified`.
- If a row is unverified, label it inline and downgrade `Export Status`.
- Never invent an item, move, ability, or mechanic.

The roster verifies species only. It does not prove that Life Orb, an old move, or a Mega mechanic is legal.

## 5. Benchmarks

Only after the legality ledger is verified for the pieces the benchmark depends on:

- up to 2 speed benchmarks
- up to 2 survival benchmarks
- up to 2 KO or damage benchmarks

Utility slots may keep heuristic spreads. Hand only narrow benchmark questions to `vgc-calcs-assistant`.

## 6. Playbook

Default to 3 packages, allow a fourth only when it is materially distinct, and allow 2 when the team honestly supports only two.

Each package needs:

- `Use Into`: a concrete core or team shape from `Targeted Meta Cores and Teams`
- `Lead Pair`
- `Preferred Backline`
- `Opening Goal`
- `Turn-One Pattern`
- `Why This Package Works`
- `Watch-Outs`

At least 2 distinct lead pairs across the packages. Do not write fake deterministic full-game scripts.

## 7. Synergy and Matchup Audit

Audit:

- speed control
- Trick Room
- weather
- Fake Out
- endgame
- role overlap
- item and ability overlap
- support and closer balance

State `pass`, `partial`, or `fail` for each and give one concrete fix for every partial or fail. Do not turn the audit into a second team.

## 8. Export Gate

`export-ready` requires:

- every named species in the current official roster
- every named item, ability, move, and mechanic verified
- complete benchmark notes
- usable spreads for the active format

A Showdown paste is allowed only under that gate. A Champions build sheet is allowed when spreads are usable but some item or move is provisional. Do not invent a Champions import string.

`Export Status` must be one of:

- `export-ready`
- `battle-ready but not export-ready`
- `provisional build blocked by legality or calc gaps`

## 9. Source Failure Handling

- infovgc down -> Limitless or LabMaus, and say so.
- LabMaus TLS/Origin issue -> `python3 tools/fetch_labmaus.py`; if unavailable, use infovgc or Limitless.
- PokeStats 403 -> Smogon for the automated check; say PokeStats was browser-only.
- Roster missing -> no species legality claims and no `export-ready`.
- Official results missing -> PokeData standings, marked unofficial.

## 10. Output Skeleton

Default mode:

```text
Build Goal
Evidence and Confidence
Supporting Species Legality
Recommended Team
Role Map
Set Direction
Synergy and Matchup Audit
Why Each Slot Exists
Matchup Notes
Weaknesses and Next Refinements
```

Battle-ready mode adds:

```text
Meta Snapshot and Fallbacks
Targeted Meta Cores and Teams
Legality Ledger
Benchmark Plan
Battle-Ready Spreads
Playbook
Export Status
```

See [Live Sources](./sources.md) for roles, TTLs, probe results, and fallbacks.

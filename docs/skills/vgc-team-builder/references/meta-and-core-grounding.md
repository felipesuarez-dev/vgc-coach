# Meta and Core Grounding

Use this reference before choosing slots for a current-format Champions build.

## Minimum Meta Stack

A `current-field recommendation` needs:

- 1 current official regulation source
- 1 current official roster source for team building
- 1 tournament-focused community source
- 1 broader usage or community source

If a required role is missing, label the build `inference-heavy early read`. If the roster is missing, do not claim species legality and do not call the build `export-ready`.

## Meta Snapshot Shape

Keep the snapshot short and auditable:

```text
Official: Regulation M-C, 2026-09-09 to 2026-12-02 UTC; roster 262 entries
Tournament: infovgc or Limitless, fetched 2026-11-25, sample scope
Broader: Smogon 2026-10 chaos or PokeStats monthly snapshot
Fallbacks: source that failed and the replacement used
Label: current-field recommendation or inference-heavy early read
```

Record fetched dates, publication months, event dates, and sample sizes when the source provides them. Do not present a monthly snapshot as today's data.

## Core Grounding

### Limitless

- Use completed Champions tournaments and their top standings decklists.
- Count 2-mon, 3-mon, and 4-mon co-occurrences from the published decklists. State the event, date, and number of teams sampled.
- A core is only grounded when at least two published teams share it, unless the user explicitly asked about a one-off team.

### LabMaus

- `/api/top_teams` publishes 4-mon, 5-mon, and 6-mon compositions. Use those as shells.
- `/api/discover_teams` returns tournament teams with pokepaste URLs. Use it for exact set context.
- Do not claim LabMaus publishes 2-mon or 3-mon cores. If you need 2-mon or 3-mon cores, count them from Limitless decklists or from LabMaus team lists only when the underlying teams are visible.

### infovgc

- Use for tournament usage, adjusted win rate, Top 8 index, recent teams, and trend context.
- Treat it as a tournament-weighted snapshot, not as a legality source.

## Core Selection Priority

1. user-named anti-meta target
2. core or team that directly pressures the requested strategy
3. most common current-field core or top team
4. individual threat not covered by those shells

Keep `Targeted Meta Cores and Teams` to 3 to 5 entries. Each entry needs a source and a date or event. Do not turn it into a mini meta report.

## Use of Cores

Use the selected shells in three places:

- slot selection: the six must have a real plan into the shell
- benchmark selection: the benchmark must answer a question that shell creates
- matchup framing: `Use Into` must name the shell, not a vague bucket

## Failure Handling

- If infovgc is down, use Limitless or LabMaus and label the swap.
- If LabMaus fails, use `python3 tools/fetch_labmaus.py`; if that is unavailable, use infovgc or Limitless and label the swap.
- If PokeStats is blocked, use Smogon and label it as the automated broader-meta source.
- If no tournament-focused source is available, downgrade to early-read language.
- If no broader usage source is available, keep usage claims directional and say so.

Never invent a core, a team, a sample size, or a source date.

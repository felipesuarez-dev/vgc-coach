# Live Sources

The authoritative source contract is
[`docs/skills/shared/references/live-source-registry.yaml`](./skills/shared/references/live-source-registry.yaml).
The generated companion is
[`live-source-map.md`](./skills/shared/references/live-source-map.md). Do not hand-edit the generated map.

This page explains the roles, freshness windows, fallbacks, endpoint caveats, and the probe snapshot from **2026-11-25**.

## Regulation Lifecycle

| State | Meaning |
|---|---|
| `current` | Active regulation. The only state used for present-tense coaching. |
| `upcoming` | Announced but not active. Prepare artifacts; do not use for present-tense legality. |
| `historical` | Ended. Keep snapshots and legality notes for history. |

Current status:

- **M-C is current**: `2026-09-09 02:00 UTC` through `2026-12-02 01:59 UTC`.
- **M-D is upcoming**: `2026-12-02 02:00 UTC` through `2027-03-03 01:59 UTC`. The official page says full details will be announced later and does not link the eligible roster yet.

`python3 tools/resolve_regulation.py --check-registry` reads the official feed, parses the latest regulation page, fetches the roster when it is linked, and reports the phase. It never edits the registry.

## Source Table

| Source | Role | Endpoint | Claim freshness | Upstream cache | Probe 2026-11-25 |
|---|---|---|---|---|---|
| Regulation Set M-C | `official_regulation` | <https://news.pokemon-home.com/en/page/816.html> | 30 d | 1 h | 200, current |
| Regulation M-C Eligible Roster | `official_roster` | <https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178713870219xeaaio/en/pokemon.html> | 7 d | 1 h | 200, 262 entries |
| Championship Series Calendar | `official_calendar` | <https://championships.pokemon.com/api/events.json?locale=en-us&status=upcoming> | 7 d | 6 h | 200, 25 items |
| Championship Series Results | `official_results` | <https://championships.pokemon.com/api/1/services/results.json> | 7 d | 12 h | 200, 652 players sampled total |
| infovgc | `tournament_meta` | <https://infovgc.com/meta> | 1 d | several per day | 200 |
| LabMaus | `tournament_meta` | <https://labmaus.net/> | 1 d | 24 h tournaments, 2 h top teams, 4 h trending | 200 with fetcher; 403 without headers |
| Limitless VGC | `tournament_meta` | <https://play.limitlesstcg.com/api/tournaments?game=VGC> | 1 d | 1 h lists, 24 h detail | 200; 76 sampled standings, all with decklists |
| PokeStats.gg | `broader_meta` | <https://pokestats.gg/competitive> | 7 d | monthly | 403 for curl; 200 through webfetch |
| Smogon Champions Stats | `broader_meta` | <https://www.smogon.com/stats/> | 7 d | monthly | 200; `gen9championsvgc2026regmc` present in 2026-10 |
| Pikalytics Champions | `supporting_sets` | <https://cdn.pikalytics.com/champions> | 7 d | 24 h | 200 |
| PokeBase Champions | `supporting_sets` | <https://pokebase.app/pokemon-champions> | 7 d | 12 h | 200 |
| Pokepaste | `supporting_sets` | <https://pokepast.es/> | 14 d | 30 d immutable | 200 text/plain |
| PokeData Event Locator | `event_standings` | <https://pokedata.ovh/events/apiv2> | 7 d | 6 h | 200; PHP warning prefix trimmed before JSON |
| PokeData Standings | `event_standings` | <https://www.pokedata.ovh/standings2/> | 7 d | 6 h | 200, 652 players |
| Victory Road | `editorial_context` | <https://victoryroad.pro/> | 14 d | editorial | 200 |
| Regulation Set M-D | `official_regulation` | <https://news.pokemon-home.com/en/page/878.html> | 30 d | 1 h | 200, upcoming; roster pending |

## Official Sources

- **Regulation**: the official Pokemon HOME news page. The `pokemon.com` article is bot-challenged and is not used as the canonical source.
- **Roster**: the Pokemon Champions eligible roster. It verifies species eligibility only. It does not verify items, moves, abilities, or mechanics.
- **Calendar**: the Championship Series events API. It carries Regional, International, Special, and World Championship dates.
- **Results**: the official Masters results API. It publishes placement and match record, not decklists.

A team-building recommendation needs the current regulation and the current roster. If the roster is missing, species legality is unverified and the build cannot be `export-ready`.

## Tournament Meta

Use at least one of these for a current-field read:

- **infovgc**: tournament-weighted usage, adjusted win rate, Top 8 index, recent teams, trends, and cores.
- **LabMaus**: completed tournaments, top teams, 4/5/6-mon compositions, trends, and pokepaste team URLs.
- **Limitless**: Champions tournament lists, standings, decklists, and 2/3/4-mon cores counted from top standings.

Limitless is the cleanest automated source for 2/3/4 cores. LabMaus publishes 4/5/6 compositions; it does not publish 2/3-mon cores.

## Broader Meta

- **Smogon**: monthly Champions chaos files. The current month may lag by one month; say so when it does.
- **PokeStats**: Showdown ladder snapshots, including Bo3. It is browser/webfetch-friendly but Cloudflare blocks plain CLI clients with HTTP 403. Use Smogon for the automated fallback and label the swap.

## Supporting Sets

- **Pikalytics**: set tendencies, common partners, moves, items, and abilities.
- **PokeBase**: community and tournament teams, including official Top 8 team lists.
- **Pokepaste**: raw public team pastes. Pastes are immutable, but the surrounding tournament date still matters for current-meta claims.

None of these are legality sources. They describe what players used, not what the format allows.

## Event and Standings

- **PokeData Event Locator**: upcoming League Challenges and Cups, venue, registration, admission, and contact context.
- **PokeData Standings**: unofficial Masters standings, Top Cut bracket, round history, teams, and divisions. Say it is unofficial when it is the only standings source.
- **Championship Series Results**: official standings and match records.

## Fallbacks

| Failed source | Replacement | Label |
|---|---|---|
| infovgc | Limitless or LabMaus | name the swap |
| LabMaus | `tools/fetch_labmaus.py`; then infovgc or Limitless | name the swap |
| Limitless | infovgc or LabMaus | name the swap |
| PokeStats | Smogon | say PokeStats was browser-only or blocked |
| Smogon | PokeStats through browser/webfetch | say the month is missing or the source was swapped |
| Official roster | eligible-Pokemon link on the current regulation page | mark species legality unverified |
| Official results | PokeData standings | say PokeData is unofficial |
| PokeData standings | official results | name the swap |

Never claim a source was checked when it returned 403, failed TLS, or returned an empty payload.

## LabMaus TLS and Headers

LabMaus serves its leaf certificate without the Sectigo intermediate and gates `/api/*` on `Origin` and `Referer`:

```bash
python3 tools/fetch_labmaus.py completed-tournaments \
  --from 2026-11-17 --to 2026-11-24
```

The fetcher loads the bundled public intermediate, verifies the chain and hostname, pins the certificate SHA-256, and sends:

- `Origin: https://labmaus.net`
- `Referer: https://labmaus.net/`
- `Accept: application/json`

Do not use a generic `curl -k` as the coaching workaround. If the fetcher is unavailable, declare LabMaus unavailable and use infovgc or Limitless.

## Excluded Sources

- **ChampionsMeta**: retired. The probe returns HTTP 402 with `x-vercel-error: DEPLOYMENT_DISABLED`.
- **ChampionsLab**: outside the automated stack. Its data lives in the Next.js RSC payload, so a plain webfetch only sees the shell.

## Probe Snapshot

The live probe is evidence, not a CI gate. The offline coverage check is part of `python3 tools/validate.py`.

```bash
python3 tools/probe_sources.py
python3 tools/probe_sources.py --markdown
python3 tools/probe_sources.py --json
python3 tools/probe_sources.py --offline
```

Latest live run: **2026-11-25**. Full table:

| Source | Role | Outcome | HTTP | Detail |
|---|---|---|---|---|
| `regulation-set-m-c` | `official_regulation` | `degraded` | 200 | current; M-D upcoming; roster pending |
| `official-roster-m-c` | `official_roster` | `ok` | 200 | 262 eligible entries |
| `championship-series-calendar` | `official_calendar` | `ok` | 200 | 25 calendar items |
| `championship-series-results` | `official_results` | `ok` | 200 | 5 sampled players, totalCount=652 |
| `infovgc` | `tournament_meta` | `ok` | 200 | 363439 bytes |
| `labmaus` | `tournament_meta` | `ok` | 200 | 62 completed tournaments with pinned CA |
| `limitless` | `tournament_meta` | `ok` | 200 | 3 tournaments; 76 standings with decklists |
| `pokestats` | `broader_meta` | `degraded` | 403 | blocked for CLI; browser/webfetch only |
| `smogon` | `broader_meta` | `ok` | 200 | 2026-10; M-C slug present |
| `pikalytics-champions` | `supporting_sets` | `ok` | 200 | 977098 bytes |
| `pokebase` | `supporting_sets` | `ok` | 200 | 792788 bytes |
| `pokepaste` | `supporting_sets` | `ok` | 200 | 767 bytes of raw paste text |
| `pokedata-events` | `event_standings` | `ok` | 200 | 100 events |
| `pokedata-standings` | `event_standings` | `ok` | 200 | 652 players |
| `victory-road` | `editorial_context` | `ok` | 200 | 395181 bytes |
| `regulation-set-m-d` | `official_regulation` | `degraded` | 200 | upcoming; roster pending |
| `championsmeta` | retired | `retired` | 402 | `DEPLOYMENT_DISABLED` |
| `championslab` | retired | `retired` | 200 | Next.js RSC shell |

## Attribution

Endpoint and TTL research was informed by
[VGC-Reporter](https://github.com/felipesuarez-dev/VGC-Reporter), licensed under
the MIT License. No VGC-Reporter source code is vendored here.

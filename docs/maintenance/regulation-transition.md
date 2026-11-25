# Regulation Transition Runbook

Use this runbook when the official Pokemon Champions regulation set changes, or when `python3 tools/check_format_freshness.py` warns that the current window ends within 30 days.

## Automation

`.github/workflows/regulation-watch.yml` runs Monday and Thursday and on manual dispatch.

- The `watch` job runs `python3 tools/regulation_watch.py check`. It reads the official Pokemon HOME news feed (`https://news.pokemon-home.com/en/json/list.json`), keeps the Pokemon Champions `Regulations` entries, and compares them with `data/official-regulation-feed.json`. It makes no model calls. A new or changed entry opens a `regulation-watch` issue. It also opens an issue 3 days before the official source refresh in section 5 is due, and another once the current regulation window ends within 14 days (or has ended).
- The `draft` job runs only for a change that has no draft branch yet and whose issue is not labelled `draft-failed`. It fetches the official page and its eligible Pokemon list, runs `tools/draft_regulation_update.py` with Copilot, records the feed baseline, regenerates derived files, and opens a draft pull request.
- The drafter cannot fetch URLs and can write only the format artifacts in step 2. Review every fact in the draft against the official page, then click **Ready for review** to start the required checks.
- The watcher reads only `news.pokemon-home.com` and `web-view.app.pokemonchampions.jp`. `pokemon.com` serves a bot challenge to scripts, so it is not used.
- `python3 tools/resolve_regulation.py --check-registry` is the deterministic preview. It reads the same feed, parses the latest regulation page, fetches the roster when the page links one, and reports `current`, `upcoming`, or `ended`. It never edits the registry.

When you handle a change by hand, also run `python3 tools/regulation_watch.py check --report <path>` and `python3 tools/regulation_watch.py update-baseline --report <path>` so the watcher stops reporting it.

After the current window ends, the freshness check keeps failing for any change that touches a format artifact (the paths in step 2, listed once in `FORMAT_ARTIFACT_PATTERNS` in `tools/check_format_freshness.py`). Other pull requests, such as Dependabot updates, workflow edits, and site changes, pass `plugin-package-check` with a `::warning`, so automation keeps running until the transition lands. Problems that are not time-based, such as a wrapper routing to a historical legality note, fail every change.

CI opts into this scoping through `FORMAT_FRESHNESS_BASE_REF` (on a pull request, `HEAD^1`, the first parent of the tested merge commit; on a push, the `before` sha). The check diffs `<base>...HEAD` and fails closed when the diff cannot be computed. Running `python3 tools/check_format_freshness.py` locally with no base ref stays strict; pass `--base-ref <ref>` to reproduce the CI scoping. The transition pull request touches format artifacts, so it must be complete before it can pass.

## Two-Phase Transition

The registry uses three regulation states:

| State | Meaning |
|---|---|
| `upcoming` | Announced but not active. Prepare artifacts; do not use for present-tense coaching. |
| `current` | Active. The only state the skills use for present-tense claims. |
| `historical` | Ended. Keep the snapshot and legality note for history. |

### Prepare

Do this as soon as the official announcement appears and the start is still in the future.

- Add the successor as `upcoming` in the registry, snapshots, and legality note.
- Keep the previous regulation `current`.
- Do not change `current-regulation.md`.
- Do not add an `upcoming` roster until the official page links the eligible roster. If the page says full details are pending, record that.
- The prepare pull request can merge before the current window ends. `upcoming` does not expire and does not count toward the minimum or team-build stacks.

### Activate

Do this at or after the official start timestamp.

- Flip the successor to `current` and the previous regulation to `historical`.
- Flip the roster to `current` when the official roster is published.
- Update `current-regulation.md` to the successor legality note.
- Regenerate derived files and run validation.
- The activation pull request touches format artifacts, so it must pass the freshness check after the new window has started.

## 1. Confirm The Successor Live

- Find the official announcement for the next regulation set on the Pokemon HOME news page (`https://news.pokemon-home.com/en/list`), or the Pokemon Champions tab.
- Run `python3 tools/resolve_regulation.py --check-registry` and `--preview --json`.
- Record the exact start and end timestamps in UTC, the publication date, and the canonical URL.
- Record only what the page states: added Pokemon, Mega Evolutions, mechanics, item rules, timers, and roster link. List anything it does not state as unverified.
- If no official announcement exists yet, stop. Do not create a successor designation from community sources or from an expected schedule.

## 2. Update The Format Artifacts

Replace `<old>` and `<new>` with regulation ids such as `m-c` and `m-d`.

| Artifact | Change |
|---|---|
| `data/snapshots/champions-reg-<new>-<date>.json` | Add the new snapshot with `temporal_status: upcoming` during prepare, or `current` during activation. |
| `data/snapshots/champions-reg-<old>-<date>.json` | Keep `current` during prepare. Set `historical` during activation. |
| `docs/skills/shared/references/champions-reg-<new>-legality.md` | Add the new legality note with `temporal_status: upcoming` or `current`. Record only what the official page states. |
| `docs/skills/shared/references/champions-reg-<old>-legality.md` | Keep `current` during prepare. Set `historical` during activation. |
| `docs/skills/shared/references/current-regulation.md` | Do not change during prepare. Point it to the new note during activation. |
| `docs/skills/shared/references/live-source-registry.yaml` | Add or replace the `official_regulation` entry with id, URL, `regulation_id`, `temporal_status`, and `active_window`. Add the `official_roster` entry only when the official roster link exists. |
| `data/official-regulation-feed.json` | Run `python3 tools/regulation_watch.py update-baseline` with a fresh report. |
| `data/fixtures/*-request-v1.example.json`, `data/fixtures/battle-state-v1.example.json` | Move the current `format` or `format_provenance` block only during activation. |
| `skills/*/SKILL.md` | Do not add a dated legality link. Use `current-regulation.md`. |
| `.opencode/skills/*/SKILL.md` | Do not add a dated legality link. Use `current-regulation.md`. |
| `docs/evals/*-live-checklist.md` | Update the regulation name, window, snapshot, and legality paths during activation. |
| `tests/test_format_freshness.py`, `tests/test_source_registry.py`, `tests/test_ingest_battle_state.py`, `tests/test_resolve_regulation.py` | Update checked-in regulation ids, windows, URLs, and roster expectations. |
| `docs/sources.md` | Re-run the probe and update the dated probe snapshot. This is a docs update, not a format artifact. |

Find the remaining references with:

```bash
git grep -n "reg-<old>\|regulation-<old>" -- ':!plugins' ':!data/snapshots'
```

## 3. Regenerate Derived Files

```bash
python3 tools/render_source_registry_docs.py build
python3 tools/build_plugins.py build
python3 tools/generate_site_trust_data.py build
python3 tools/validate.py
```

Do not hand-edit `plugins/`, `docs/skills/shared/references/live-source-map.md`, or `site/src/generated/trustData.ts`.

## 4. Ship The Transition

- Open a dedicated pull request. Do not push format changes onto a Dependabot branch.
- Merge the prepare pull request before the current window ends when it touches format artifacts.
- Merge the activation pull request at or after the official start.
- After activation, bump `VERSION`, run `python3 tools/build_plugins.py build` and `python3 tools/build_plugins.py update-release-notes`, and merge that. Then run the `Plugin Release` workflow by hand from `main`; plugin releases never start on their own. Installed plugins update only when the version changes.

## 5. Between Transitions

The official source entry allows 30 days between fetches. When the public trust panel shows the source as stale, recheck the official page, update `fetched_at` and `verified_on` in the current snapshot, and regenerate the trust data.

## 6. Current M-D Preparation

The official feed announced Regulation Set M-D on November 25, 2026.

- window: `2026-12-02 02:00 UTC` through `2027-03-03 01:59 UTC`
- official page: `https://news.pokemon-home.com/en/page/878.html`
- state: `upcoming`; M-C remains `current` until the start
- announced examples: Heatran, Dondozo, Tatsugiri
- announced Mega Evolutions: Mega Heatran, Mega Tatsugiri
- roster: not published yet; do not add an `official_roster` M-D entry until the page links it
- full details: the page says they will be announced later; do not infer items, moves, abilities, timers, or the full roster

At activation, use `python3 tools/resolve_regulation.py --check-registry` to confirm the official window and roster before flipping the statuses.

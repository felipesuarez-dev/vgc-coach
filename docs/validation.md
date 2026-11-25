# Validation

Run validation from the repository root.

## Full Entry Point

```bash
python3 tools/validate.py
```

The default `all` scope runs the Python tests, the source-registry render check, the offline source-probe coverage check, the current-format freshness check, the battle-state example check, the generated-plugin drift check, the site trust-data check, the production site build, and the site bundle budget.

Focused scopes:

```bash
python3 tools/validate.py --scope core
python3 tools/validate.py --scope site
```

`site` requires `pnpm` and the installed site dependencies:

```bash
corepack enable pnpm
pnpm --dir site install --frozen-lockfile
```

## Individual Checks

```bash
python3 tools/render_source_registry_docs.py check
python3 tools/build_plugins.py check
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_format_freshness.py
python3 tools/generate_site_trust_data.py check
git diff --check
```

## Live Source Probe

The live probe is evidence, not a CI gate:

```bash
python3 tools/probe_sources.py
python3 tools/probe_sources.py --markdown
python3 tools/probe_sources.py --json
python3 tools/probe_sources.py --only labmaus,limitless,smogon
```

The offline coverage check is part of `tools/validate.py`:

```bash
python3 tools/probe_sources.py --offline
```

A `degraded` result is a source that is reachable but constrained, such as PokeStats behind Cloudflare or a roster that is not published yet. `--strict` treats degraded results as failures.

## Regulation Resolver

```bash
python3 tools/resolve_regulation.py --check-registry
python3 tools/resolve_regulation.py --preview --json
```

The resolver reports the latest official regulation as `current`, `upcoming`, or `ended` and compares it with the registry. It never edits files.

During M-D preparation:

- M-C stays `current`.
- M-D is `upcoming`.
- The M-D roster is not added until the official page links it.
- `current-regulation.md` still points to M-C.
- `check_format_freshness.py` ignores `upcoming` and warns about the M-C end.

During M-D activation:

- M-D becomes `current`, M-C becomes `historical`.
- `current-regulation.md` points to M-D.
- The M-D roster is added only when the official link exists.
- Re-run the resolver and the full validation.

## LabMaus Fetcher

```bash
python3 tools/fetch_labmaus.py completed-tournaments \
  --from 2026-11-17 --to 2026-11-24

python3 tools/fetch_labmaus.py discover-teams \
  --from 2026-11-17 --to 2026-11-24 --regulation M-C
```

The fetcher verifies the TLS chain with the bundled Sectigo intermediate, sends Origin and Referer, and pins the certificate fingerprint.

## Skill Evals

Fixtures live in `data/fixtures/evals/`; rubrics live in `data/rubrics/`.

```bash
python3 tools/eval_skill.py --skill vgc-team-builder --provider github-token \
  --model claude-sonnet-5.5 --profile manual --case-limit 1
```

Full local suite:

```bash
python3 tools/full_eval.py --provider github-token \
  --model claude-sonnet-5.5 --profile manual
```

The eval runner needs Copilot authentication and model credits. If it is unavailable, report that plainly; do not claim the evals passed.

## Coverage

There is no coverage gate. The tests target the new behaviors and failure modes:

- registry roles, stacks, and lifecycle
- LabMaus certificate, headers, URL building, HTTP errors, and JSON errors
- probe coverage, markers, degraded sources, retired sources, and PokeData's PHP warning prefix
- resolver parsing for M-C and M-D, phase boundaries, and registry comparison
- freshness handling for `current`, `upcoming`, and `historical`
- stable `current-regulation.md` routing
- team-builder evals for fallback, LabMaus TLS, core grounding, legality ledger, and export blocking

If line coverage is useful for a local review:

```bash
python3 -m coverage run -m unittest discover -s tests -p 'test_*.py'
python3 -m coverage report -m tools/fetch_labmaus.py tools/probe_sources.py tools/resolve_regulation.py
```

# Case 09

Research expectation: live_required

Request:

`Build me an export-ready Champions team around Mega Gengar with spreads, but stay honest if item or move legality is not fully verified.`

Checks:

- uses battle-ready mode
- includes `Legality Ledger`
- includes `Battle-Ready Spreads`
- includes `Playbook`
- includes `Synergy and Matchup Audit`
- includes `Export Status`
- does not claim `export-ready` if named items, abilities, moves, mechanics, or benchmarks remain unverified
- still provides usable spreads and move-package guidance when exact export is blocked
- offers a Showdown paste only if the export gate is satisfied
- does not invent a Champions import string

Failure triggers:

- claims `export-ready` while the legality ledger has unverified rows
- offers a Showdown paste without the export gate
- invents a Champions import string
- omits the ledger or export status

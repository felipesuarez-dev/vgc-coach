# Battle-Ready Legality Ledger

Use this reference for `vgc-team-builder` battle-ready outputs.

## Purpose

A battle-ready build needs a stricter legality standard than a normal team shell.

Species legality alone is not enough when the build names:

- exact held items
- exact abilities
- exact four-move sets
- export-ready status

The current official roster verifies species eligibility only. It does not verify items, moves, abilities, or mechanics.

## Minimum Ledger Coverage

For battle-ready builds, the legality ledger should cover:

- the requested species or form
- the five supporting species
- every exact held item named in the final build
- every exact ability named in the final build
- every exact four-move set named in the final build
- active mechanics that materially shape the build

## Ledger Shape

Use a compact table:

| Slot | Species | Species source | Item status | Ability status | Move status | Mechanics | Export |
|---|---|---|---|---|---|---|---|

Use `verified`, `partial`, or `unverified` per row. Name the source for each verified claim.

## Output Rules

If a named species is in the current official roster:

- it may appear as species-eligible in the ledger
- it may not be used to imply item, move, ability, or mechanic legality

If a named item, ability, move, or mechanic is verified:

- it may appear as confirmed in `Battle-Ready Spreads`
- it may contribute to `export-ready` status

If a named item, ability, move, or mechanic is not verified:

- label it inline as `unverified/provisional`
- keep the set usable with move-package or role wording
- downgrade `Export Status` away from `export-ready`

## Export Status Labels

Use one of these exact labels:

- `export-ready`
- `battle-ready but not export-ready`
- `provisional build blocked by legality or calc gaps`

## Export Gate

`export-ready` requires all of the following:

- every named species is in the current official roster
- every named item, ability, move, and mechanic is verified
- the benchmark notes are complete
- the spreads are usable in the active format

A Showdown paste may be offered only under those conditions. A Champions build sheet may be offered when the spreads are usable but some item or move is provisional. Do not invent a Champions import string.

## Practical Boundary

A build may still be battle-ready when:

- the six is coherent
- spreads are justified
- benchmark notes are clear
- some items or moves remain provisional

But it is not export-ready until the named item, ability, move, and mechanic choices are verified by the ledger.

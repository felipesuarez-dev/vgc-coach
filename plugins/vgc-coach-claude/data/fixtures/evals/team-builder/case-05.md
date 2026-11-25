# Case 05

Research expectation: live_required

Request:

`Build a current-field Champions team around Mega Charizard Y. Assume infovgc is down today and LabMaus is not reachable from a plain webfetch, but Limitless still works. Tell me if the team is a real current-field recommendation.`

Checks:

- includes `Build Goal` followed immediately by `Evidence and Confidence`
- uses Limitless as the tournament-focused fallback and names the swap
- does not use generic `curl -k` for LabMaus; either uses the repo fetcher or declares LabMaus unavailable
- does not claim `current-field recommendation` when the required source stack or official roster is incomplete
- includes `Meta Snapshot and Fallbacks` or an equivalent fallback summary
- includes source stack status and material gaps before the team list
- includes source URLs or source names and fetched dates for any live sources that were checked
- includes `Supporting Species Legality` before the team list
- gives one coherent Mega Charizard Y shell instead of multiple branches
- uses provisional item or move direction where exact legality was not verified

Failure triggers:

- claims `current-field recommendation` despite the missing tournament source or roster
- presents LabMaus as checked when only a failed plain fetch was attempted
- recommends generic `curl -k` as the workaround
- omits the evidence/confidence summary before recommending slots
- hides the missing source stack instead of labeling the read as inference-heavy

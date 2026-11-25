# Case 12

Research expectation: live_required

Request:

`Build a battle-ready Champions team around Mega Blastoise. The only tournament source with the cores you need is LabMaus, and a plain webfetch fails with a certificate error. Keep the source handling honest.`

Checks:

- does not present generic `curl -k` as the workaround
- uses `python3 tools/fetch_labmaus.py` when available, or declares LabMaus unavailable and falls back
- names the Origin/Referer requirement when explaining the LabMaus path
- labels any source swap and downgrades the confidence label if the tournament stack is incomplete
- still gives one coherent team and does not fabricate cores
- includes `Evidence and Confidence` and `Meta Snapshot and Fallbacks`
- includes `Supporting Species Legality` before the team list

Failure triggers:

- recommends a generic `curl -k` command inside the coaching answer
- claims LabMaus data was checked after a plain fetch failed
- invents cores to fill the gap
- hides the source failure

from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import resolve_regulation  # noqa: E402


FEED = b"""{
  "data": [
    {
      "id": "816",
      "title": "Regulation Set M-C",
      "infoKind": 12,
      "kindTxt": "Regulations",
      "link": "page/816.html",
      "linkRom": ["CHP"],
      "stAt": 1788127200,
      "endAt": 1796176799,
      "pubAt": 1788934215
    },
    {
      "id": "878",
      "title": "Regulation Set M-D",
      "infoKind": 12,
      "kindTxt": "Regulations",
      "link": "page/878.html",
      "linkRom": ["CHP"],
      "stAt": 1795572000,
      "endAt": 1804039199,
      "pubAt": 1795572015
    }
  ]
}"""

M_C_PAGE = b"""<html><body>
<h1>Regulation Set M-C</h1>
<p>Wednesday, September 9, 2026, at 02:00 UTC to Wednesday, December 2, 2026, at 01:59 UTC</p>
<p>Mechanics</p>
<p>Certain Pokemon can Mega Evolve if they are holding a Mega Stone.</p>
<p>The following Mega Evolutions are newly allowed under this regulation.</p>
<p>&bull; Mega Absol Z</p>
<p>&bull; Mega Salamence</p>
<p>Held Items</p>
<p>Duplicate held items are not allowed.</p>
<p>Timers</p>
<p>Total Time: 20 minutes</p>
<a href="https://web-view.app.pokemonchampions.jp/battle/pages/events/test/en/pokemon.html">Eligible</a>
</body></html>"""

M_D_PAGE = b"""<html><body>
<h1>Regulation Set M-D</h1>
<p>Note: Full details of this regulation set will be announced at a later date.</p>
<p>Wednesday, December 2, 2026, at 02:00 UTC to Wednesday, March 3, 2027, at 01:59 UTC</p>
<p>Mechanics</p>
<p>Certain Pokemon can Mega Evolve if they are holding a Mega Stone.</p>
<p>Mega Evolutions newly allowed under Regulation Set M-D include the following.</p>
<p>&bull; Mega Heatran</p>
<p>&bull; Mega Tatsugiri</p>
<p>What Are Regulations?</p>
</body></html>"""

ROSTER = b"""const pokemons = [["0003-000",1,"Venusaur"],["0006-000",1,"Charizard"]];"""


def fake_fetch(url: str) -> bytes:
    if url.endswith("list.json"):
        return FEED
    if url.endswith("816.html"):
        return M_C_PAGE
    if url.endswith("878.html"):
        return M_D_PAGE
    if "pokemon.html" in url:
        return ROSTER
    raise AssertionError(f"unexpected fetch: {url}")


def registry_with(*sources):
    return {"sources": list(sources)}


def source(
    source_id: str,
    role: str,
    *,
    status: str,
    regulation_id: str,
    url: str,
    start: str,
    end: str,
):
    return {
        "id": source_id,
        "role": role,
        "temporal_status": status,
        "regulation_id": regulation_id,
        "canonical_url": url,
        "active_window": {"start": start, "end": end},
    }


class ResolveRegulationTests(unittest.TestCase):
    def test_parses_m_c_page(self):
        parsed = resolve_regulation.parse_regulation_page(
            M_C_PAGE.decode(), "https://news.pokemon-home.com/en/page/816.html"
        )
        self.assertEqual(parsed["code"], "M-C")
        self.assertEqual(parsed["start"], "2026-09-09T02:00:00Z")
        self.assertEqual(parsed["end"], "2026-12-02T01:59:00Z")
        self.assertTrue(parsed["roster_url"].endswith("/pokemon.html"))
        self.assertEqual(parsed["new_megas"], ["Mega Absol Z", "Mega Salamence"])

    def test_parses_m_d_announcement_without_roster(self):
        parsed = resolve_regulation.parse_regulation_page(
            M_D_PAGE.decode(), "https://news.pokemon-home.com/en/page/878.html"
        )
        self.assertEqual(parsed["code"], "M-D")
        self.assertEqual(parsed["start"], "2026-12-02T02:00:00Z")
        self.assertEqual(parsed["end"], "2027-03-03T01:59:00Z")
        self.assertIsNone(parsed["roster_url"])
        self.assertEqual(parsed["new_megas"], ["Mega Heatran", "Mega Tatsugiri"])

    def test_phase_boundaries(self):
        start = datetime(2026, 12, 2, 2, 0, tzinfo=timezone.utc)
        end = datetime(2027, 3, 3, 1, 59, tzinfo=timezone.utc)
        self.assertEqual(
            resolve_regulation.phase_for(
                start, end, datetime(2026, 11, 25, tzinfo=timezone.utc)
            ),
            "upcoming",
        )
        self.assertEqual(
            resolve_regulation.phase_for(start, end, start), "current"
        )
        self.assertEqual(
            resolve_regulation.phase_for(
                start, end, datetime(2027, 3, 3, 2, 0, tzinfo=timezone.utc)
            ),
            "ended",
        )

    def test_resolves_m_d_upcoming_and_skips_missing_roster(self):
        resolved = resolve_regulation.resolve_regulation(
            now=datetime(2026, 11, 25, 12, tzinfo=timezone.utc),
            fetch=fake_fetch,
        )
        self.assertEqual(resolved.code, "M-D")
        self.assertEqual(resolved.phase, "upcoming")
        self.assertTrue(resolved.roster_pending)
        self.assertIsNone(resolved.roster_url)

    def test_compares_upcoming_m_d_with_current_m_c(self):
        resolved = resolve_regulation.resolve_regulation(
            now=datetime(2026, 11, 25, 12, tzinfo=timezone.utc),
            fetch=fake_fetch,
        )
        registry = registry_with(
            source(
                "regulation-set-m-c",
                "official_regulation",
                status="current",
                regulation_id="regulation-m-c",
                url="https://news.pokemon-home.com/en/page/816.html",
                start="2026-09-09T02:00:00Z",
                end="2026-12-02T01:59:00Z",
            ),
            source(
                "regulation-set-m-d",
                "official_regulation",
                status="upcoming",
                regulation_id="regulation-m-d",
                url="https://news.pokemon-home.com/en/page/878.html",
                start="2026-12-02T02:00:00Z",
                end="2027-03-03T01:59:00Z",
            ),
        )
        mismatches = resolve_regulation.compare_with_registry(resolved, registry)
        self.assertEqual(resolve_regulation.blocking_mismatches(mismatches), [])
        self.assertTrue(any(item.field == "official_roster.pending" for item in mismatches))

    def test_flags_missing_upcoming_m_d_as_warning(self):
        resolved = resolve_regulation.resolve_regulation(
            now=datetime(2026, 11, 25, 12, tzinfo=timezone.utc),
            fetch=fake_fetch,
        )
        registry = registry_with(
            source(
                "regulation-set-m-c",
                "official_regulation",
                status="current",
                regulation_id="regulation-m-c",
                url="https://news.pokemon-home.com/en/page/816.html",
                start="2026-09-09T02:00:00Z",
                end="2026-12-02T01:59:00Z",
            )
        )
        mismatches = resolve_regulation.compare_with_registry(resolved, registry)
        self.assertEqual(resolve_regulation.blocking_mismatches(mismatches), [])
        self.assertTrue(any(item.severity == "warning" for item in mismatches))

    def test_flags_active_m_d_against_current_m_c_as_blocking(self):
        resolved = resolve_regulation.ResolvedRegulation(
            checked_at="2026-12-02T02:00:00Z",
            feed_url="https://news.pokemon-home.com/en/json/list.json",
            feed_entry_id="878",
            page_url="https://news.pokemon-home.com/en/page/878.html",
            regulation_id="regulation-m-d",
            code="M-D",
            display_name="Regulation Set M-D",
            start="2026-12-02T02:00:00Z",
            end="2027-03-03T01:59:00Z",
            phase="current",
            roster_url="https://web-view.app.pokemonchampions.jp/test/pokemon.html",
            roster_count=2,
        )
        registry = registry_with(
            source(
                "regulation-set-m-c",
                "official_regulation",
                status="current",
                regulation_id="regulation-m-c",
                url="https://news.pokemon-home.com/en/page/816.html",
                start="2026-09-09T02:00:00Z",
                end="2026-12-02T01:59:00Z",
            )
        )
        mismatches = resolve_regulation.compare_with_registry(resolved, registry)
        blocking = resolve_regulation.blocking_mismatches(mismatches)
        self.assertTrue(any(item.field == "official_regulation" for item in blocking))
        self.assertTrue(any(item.field == "official_roster" for item in blocking))

    def test_active_m_d_with_matching_registry_is_aligned(self):
        resolved = resolve_regulation.ResolvedRegulation(
            checked_at="2026-12-02T02:00:00Z",
            feed_url="https://news.pokemon-home.com/en/json/list.json",
            feed_entry_id="878",
            page_url="https://news.pokemon-home.com/en/page/878.html",
            regulation_id="regulation-m-d",
            code="M-D",
            display_name="Regulation Set M-D",
            start="2026-12-02T02:00:00Z",
            end="2027-03-03T01:59:00Z",
            phase="current",
            roster_url="https://web-view.app.pokemonchampions.jp/test/pokemon.html",
            roster_count=2,
        )
        registry = registry_with(
            source(
                "regulation-set-m-d",
                "official_regulation",
                status="current",
                regulation_id="regulation-m-d",
                url="https://news.pokemon-home.com/en/page/878.html",
                start="2026-12-02T02:00:00Z",
                end="2027-03-03T01:59:00Z",
            ),
            source(
                "official-roster-m-d",
                "official_roster",
                status="current",
                regulation_id="regulation-m-d",
                url="https://web-view.app.pokemonchampions.jp/test/pokemon.html",
                start="2026-12-02T02:00:00Z",
                end="2027-03-03T01:59:00Z",
            ),
        )
        mismatches = resolve_regulation.compare_with_registry(resolved, registry)
        self.assertEqual(mismatches, [])

    def test_json_cli_output_stays_valid_with_preview(self):
        resolved = resolve_regulation.ResolvedRegulation(
            checked_at="2026-11-25T12:00:00Z",
            feed_url="https://news.pokemon-home.com/en/json/list.json",
            feed_entry_id="878",
            page_url="https://news.pokemon-home.com/en/page/878.html",
            regulation_id="regulation-m-d",
            code="M-D",
            display_name="Regulation Set M-D",
            start="2026-12-02T02:00:00Z",
            end="2027-03-03T01:59:00Z",
            phase="upcoming",
            roster_url=None,
            roster_count=0,
            roster_pending=True,
        )
        registry = registry_with(
            source(
                "regulation-set-m-c",
                "official_regulation",
                status="current",
                regulation_id="regulation-m-c",
                url="https://news.pokemon-home.com/en/page/816.html",
                start="2026-09-09T02:00:00Z",
                end="2026-12-02T01:59:00Z",
            ),
            source(
                "regulation-set-m-d",
                "official_regulation",
                status="upcoming",
                regulation_id="regulation-m-d",
                url="https://news.pokemon-home.com/en/page/878.html",
                start="2026-12-02T02:00:00Z",
                end="2027-03-03T01:59:00Z",
            ),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(resolve_regulation, "resolve_regulation", return_value=resolved),
            mock.patch.object(resolve_regulation, "load_registry", return_value=registry),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = resolve_regulation.main(["--json", "--preview"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["code"], "M-D")
        self.assertIn("Upcoming regulation detected", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

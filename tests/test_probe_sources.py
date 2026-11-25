from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import probe_sources  # noqa: E402


def source(source_id: str, role: str = "tournament_meta") -> dict:
    return {
        "id": source_id,
        "role": role,
        "canonical_url": "https://example.com/source",
    }


class ProbeSourcesTests(unittest.TestCase):
    def test_offline_check_covers_the_real_registry(self):
        registry = probe_sources.load_registry()
        self.assertEqual(probe_sources.offline_check(registry), [])

    def test_offline_check_flags_missing_probe(self):
        registry = probe_sources.load_registry()
        registry["sources"].append(source("new-source"))
        issues = probe_sources.offline_check(registry)
        self.assertTrue(any("new-source" in issue for issue in issues))

    def test_offline_check_flags_retired_source_in_registry(self):
        registry = probe_sources.load_registry()
        registry["sources"].append(source("championsmeta", "editorial_context"))
        issues = probe_sources.offline_check(registry)
        self.assertTrue(any("retired source is still in the registry" in issue for issue in issues))

    def test_simple_marks_marker_missing_as_failed(self):
        response = probe_sources.HttpResponse(
            status=200,
            content_type="text/html",
            body=b"<title>Other</title>",
            latency_ms=1,
        )
        with mock.patch.object(probe_sources, "_http_get", return_value=response):
            result = probe_sources._simple(
                source("infovgc"), url="https://example.com", markers=("Expected",)
            )
        self.assertEqual(result.outcome, "failed")
        self.assertIn("missing expected marker", result.detail)

    def test_simple_marks_403_as_degraded(self):
        response = probe_sources.HttpResponse(
            status=403,
            content_type="text/html",
            body=b"blocked",
            latency_ms=1,
        )
        with mock.patch.object(probe_sources, "_http_get", return_value=response):
            result = probe_sources._simple(
                source("pokestats"), url="https://example.com", allow_degraded_status=(403,)
            )
        self.assertEqual(result.outcome, "degraded")

    def test_simple_marks_200_as_ok(self):
        response = probe_sources.HttpResponse(
            status=200,
            content_type="text/html",
            body=b"<title>infovgc</title>",
            latency_ms=1,
        )
        with mock.patch.object(probe_sources, "_http_get", return_value=response):
            result = probe_sources._simple(
                source("infovgc"), url="https://example.com", markers=("infovgc",)
            )
        self.assertEqual(result.outcome, "ok")

    def test_probe_all_catches_a_source_exception(self):
        registry = {"sources": [source("infovgc")]}
        with mock.patch.dict(
            probe_sources.PROBES, {"infovgc": mock.Mock(side_effect=RuntimeError("boom"))}
        ):
            results, retired = probe_sources.probe_all(registry, include_retired=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].outcome, "failed")
        self.assertIn("RuntimeError: boom", results[0].detail)
        self.assertEqual(retired, [])

    def test_pokedata_events_tolerates_php_warning_prefix(self):
        body = (
            b"<br />\n<b>Warning</b>: preg_match(): allocation failed<br />\n"
            b'{"events":[{"name":"League Challenge"}]}'
        )
        response = probe_sources.HttpResponse(
            status=200,
            content_type="application/json",
            body=body,
            latency_ms=1,
        )
        with mock.patch.object(probe_sources, "_http_get", return_value=response):
            result = probe_sources.probe_pokedata_events(source("pokedata-events"))
        self.assertEqual(result.outcome, "ok")
        self.assertIn("1 events", result.detail)

    def test_championsmeta_is_retired_on_402(self):
        response = probe_sources.HttpResponse(
            status=402,
            content_type="text/plain",
            body=b"DEPLOYMENT_DISABLED",
            latency_ms=1,
        )
        with mock.patch.object(probe_sources, "_http_get", return_value=response):
            result = probe_sources.probe_championsmeta()
        self.assertEqual(result.outcome, "retired")
        self.assertIn("DEPLOYMENT_DISABLED", result.detail)

    def test_smogon_month_lag_is_degraded(self):
        index = probe_sources.HttpResponse(
            status=200,
            content_type="text/html",
            body=b"<a>2026-10</a>",
            latency_ms=1,
        )
        listing = probe_sources.HttpResponse(
            status=200,
            content_type="text/html",
            body=b"gen9championsvgc2026regmc-0.json",
            latency_ms=1,
        )
        registry = {
            "sources": [
                {
                    "id": "regulation-set-m-d",
                    "role": "official_regulation",
                    "temporal_status": "current",
                    "regulation_id": "regulation-m-d",
                }
            ]
        }
        with (
            mock.patch.object(probe_sources, "_http_get", side_effect=[index, listing]),
            mock.patch.object(probe_sources.resolve_regulation, "load_registry", return_value=registry),
        ):
            result = probe_sources.probe_smogon(source("smogon", "broader_meta"))
        self.assertEqual(result.outcome, "degraded")
        self.assertIn("no md slug yet", result.detail)

    def test_markdown_renders_rows(self):
        result = probe_sources.ProbeResult(
            source_id="infovgc",
            role="tournament_meta",
            url="https://infovgc.com/meta",
            outcome="ok",
            http_status=200,
            content_type="text/html",
            latency_ms=10,
            detail="363439 bytes",
            checked_at="2026-11-25T00:00:00Z",
        )
        table = probe_sources._render_markdown([result], [])
        self.assertIn("| Source | Role | Outcome |", table)
        self.assertIn("`infovgc`", table)
        self.assertIn("363439 bytes", table)

    def test_offline_cli_returns_zero(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = probe_sources.main(["--offline"])
        self.assertEqual(code, 0)
        self.assertIn("Offline probe check passed", output.getvalue())


if __name__ == "__main__":
    unittest.main()

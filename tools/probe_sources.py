#!/usr/bin/env python3
"""Probe the shared live-source registry against the real endpoints.

`--offline` validates that every registry source has a probe and that every
probe maps to a registry source. The live run records status, latency, and a
short detail per source. It is evidence, not a CI gate: network flakiness and
Cloudflare challenges are reported as degraded or failed, never hidden.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import fetch_labmaus  # noqa: E402
import regulation_watch  # noqa: E402
import resolve_regulation  # noqa: E402

REGISTRY_PATH = Path("docs/skills/shared/references/live-source-registry.yaml")
DEFAULT_TIMEOUT = 25.0
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class ProbeResult:
    source_id: str
    role: str
    url: str
    outcome: str
    http_status: int | None
    content_type: str
    latency_ms: int
    detail: str
    checked_at: str


@dataclass
class HttpResponse:
    status: int
    content_type: str
    body: bytes
    latency_ms: int
    error: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    context: ssl.SSLContext | None = None,
) -> HttpResponse:
    request_headers = {"User-Agent": BROWSER_UA}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read()
            return HttpResponse(
                status=response.status,
                content_type=response.headers.get_content_type(),
                body=body,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return HttpResponse(
            status=exc.code,
            content_type=exc.headers.get_content_type() if exc.headers else "",
            body=body,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    except urllib.error.URLError as exc:
        return HttpResponse(
            status=0,
            content_type="",
            body=b"",
            latency_ms=int((time.monotonic() - started) * 1000),
            error=str(exc.reason),
        )


def _result(
    source: dict[str, Any],
    *,
    url: str,
    outcome: str,
    status: int | None,
    content_type: str,
    latency_ms: int,
    detail: str,
) -> ProbeResult:
    return ProbeResult(
        source_id=source["id"],
        role=source["role"],
        url=url,
        outcome=outcome,
        http_status=status,
        content_type=content_type,
        latency_ms=latency_ms,
        detail=detail,
        checked_at=_now(),
    )


def _simple(
    source: dict[str, Any],
    *,
    url: str,
    markers: tuple[str, ...] = (),
    allow_degraded_status: tuple[int, ...] = (),
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> ProbeResult:
    response = _http_get(url, headers=headers, timeout=timeout)
    text = response.body.decode("utf-8", errors="replace")
    if response.error:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=None,
            content_type="",
            latency_ms=response.latency_ms,
            detail=response.error,
        )
    missing = [marker for marker in markers if marker.lower() not in text.lower()]
    if response.status in allow_degraded_status:
        return _result(
            source,
            url=url,
            outcome="degraded",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="blocked for automated HTTP clients; browser or webfetch may still work",
        )
    if response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=f"unexpected HTTP {response.status}",
        )
    if missing:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=f"missing expected marker(s): {', '.join(missing)}",
        )
    return _result(
        source,
        url=url,
        outcome="ok",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(response.body)} bytes",
    )


def probe_regulation(source: dict[str, Any]) -> ProbeResult:
    resolved = resolve_regulation.resolve_regulation()
    registry = resolve_regulation.load_registry()
    mismatches = resolve_regulation.compare_with_registry(resolved, registry)
    blocking = resolve_regulation.blocking_mismatches(mismatches)
    warnings = [item for item in mismatches if item.severity == "warning"]
    detail_parts = [
        f"registry {source.get('regulation_id', source['id'])} {source.get('temporal_status', 'current')}",
    ]
    source_window = source.get("active_window") or {}
    if source_window:
        detail_parts.append(
            f"source window {source_window.get('start')} through {source_window.get('end')}"
        )
    detail_parts.extend(
        [
            f"resolver {resolved.code} {resolved.phase}",
            f"{resolved.start} through {resolved.end}",
        ]
    )
    if resolved.roster_pending:
        detail_parts.append("roster pending")
    else:
        detail_parts.append(f"roster {resolved.roster_count} entries")
    if blocking:
        detail_parts.extend(item.message for item in blocking)
        outcome = "failed"
    elif warnings:
        detail_parts.extend(item.message for item in warnings)
        outcome = "degraded"
    else:
        outcome = "ok"
    return _result(
        source,
        url=resolved.page_url,
        outcome=outcome,
        status=200,
        content_type="text/html",
        latency_ms=0,
        detail="; ".join(detail_parts),
    )


def probe_official_roster(source: dict[str, Any]) -> ProbeResult:
    response = _http_get(source["canonical_url"])
    if response.error or response.status != 200:
        return _result(
            source,
            url=source["canonical_url"],
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    names = regulation_watch.extract_eligible_pokemon(
        response.body.decode("utf-8", errors="replace")
    )
    if not names:
        return _result(
            source,
            url=source["canonical_url"],
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="roster parsed empty",
        )
    return _result(
        source,
        url=source["canonical_url"],
        outcome="ok",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(names)} eligible entries",
    )


def probe_calendar(source: dict[str, Any]) -> ProbeResult:
    response = _http_get(source["canonical_url"])
    if response.error or response.status != 200:
        return _result(
            source,
            url=source["canonical_url"],
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    payload = json.loads(response.body)
    count = payload.get("itemsFound", len(payload.get("items", [])))
    return _result(
        source,
        url=source["canonical_url"],
        outcome="ok" if count else "failed",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{count} calendar items",
    )


def probe_results(source: dict[str, Any]) -> ProbeResult:
    event_path = "/en-us/events/internationals/2027/sao-paulo"
    url = (
        "https://championships.pokemon.com/api/1/services/results.json?"
        + urllib.parse.urlencode(
            {
                "game": "vg",
                "division": "masters",
                "locale": "en-us",
                "url": event_path,
                "start": 0,
                "size": 5,
            }
        )
    )
    response = _http_get(url)
    if response.error or response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    payload = json.loads(response.body)
    players = payload.get("players") or []
    total = payload.get("totalCount")
    if not players:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="results payload has no players",
        )
    return _result(
        source,
        url=url,
        outcome="ok",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(players)} sampled players, totalCount={total}",
    )


def probe_labmaus(source: dict[str, Any]) -> ProbeResult:
    url = "https://labmaus.net/api/completed_tournaments"
    started = time.monotonic()
    try:
        payload = fetch_labmaus.LabMausClient().completed_tournaments(
            "2026-11-17", "2026-11-24"
        )
    except fetch_labmaus.LabMausError as exc:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=None,
            content_type="application/json",
            latency_ms=int((time.monotonic() - started) * 1000),
            detail=str(exc),
        )
    count = len(payload) if isinstance(payload, list) else 0
    return _result(
        source,
        url=url,
        outcome="ok" if count else "failed",
        status=200,
        content_type="application/json",
        latency_ms=int((time.monotonic() - started) * 1000),
        detail=f"{count} completed tournaments with Origin/Referer and pinned CA",
    )


def probe_limitless(source: dict[str, Any]) -> ProbeResult:
    url = "https://play.limitlesstcg.com/api/tournaments?game=VGC&limit=3"
    response = _http_get(url)
    if response.error or response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    tournaments = json.loads(response.body)
    if not tournaments:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="tournament list is empty",
        )
    first = tournaments[0]
    standings_url = (
        f"https://play.limitlesstcg.com/api/tournaments/{first['id']}/standings?limit=3"
    )
    standings_response = _http_get(standings_url)
    if standings_response.error or standings_response.status != 200:
        return _result(
            source,
            url=standings_url,
            outcome="failed",
            status=standings_response.status or None,
            content_type=standings_response.content_type,
            latency_ms=standings_response.latency_ms,
            detail=standings_response.error or f"HTTP {standings_response.status}",
        )
    standings = json.loads(standings_response.body)
    decklists = sum(1 for row in standings if row.get("decklist"))
    return _result(
        source,
        url=standings_url,
        outcome="ok" if standings else "failed",
        status=standings_response.status,
        content_type=standings_response.content_type,
        latency_ms=standings_response.latency_ms,
        detail=f"{len(tournaments)} tournaments; {len(standings)} sampled standings, {decklists} with decklists",
    )


def probe_pokestats(source: dict[str, Any]) -> ProbeResult:
    return _simple(
        source,
        url=source["canonical_url"],
        markers=("Pokemon Competitive Usage Statistics",),
        allow_degraded_status=(403,),
    )


def probe_smogon(source: dict[str, Any]) -> ProbeResult:
    index_url = "https://www.smogon.com/stats/"
    response = _http_get(index_url)
    if response.error or response.status != 200:
        return _result(
            source,
            url=index_url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    months = sorted(set(re.findall(r"20\d{2}-\d{2}", response.body.decode("utf-8", "replace"))))
    if not months:
        return _result(
            source,
            url=index_url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="no month directories found",
        )
    month = months[-1]
    listing_url = f"https://www.smogon.com/stats/{month}/chaos/"
    listing = _http_get(listing_url)
    if listing.error or listing.status != 200:
        return _result(
            source,
            url=listing_url,
            outcome="failed",
            status=listing.status or None,
            content_type=listing.content_type,
            latency_ms=listing.latency_ms,
            detail=listing.error or f"HTTP {listing.status}",
        )
    slugs = sorted(
        set(
            re.findall(
                r"gen9championsvgc\d{4}regm[a-z]+(?:bo)?",
                listing.body.decode("utf-8", "replace"),
            )
        )
    )
    registry = resolve_regulation.load_registry()
    current = next(
        (
            item
            for item in registry["sources"]
            if item["role"] == "official_regulation"
            and item.get("temporal_status") == "current"
        ),
        None,
    )
    code = current["regulation_id"].removeprefix("regulation-").replace("-", "") if current else ""
    matching = [slug for slug in slugs if slug.endswith(f"reg{code}") or slug.endswith(f"reg{code}bo")]
    if matching:
        outcome = "ok"
        detail = f"latest month {month}; {', '.join(matching)}"
    elif slugs:
        outcome = "degraded"
        detail = f"latest month {month}; no {code} slug yet (month lag): {', '.join(slugs[:4])}"
    else:
        outcome = "failed"
        detail = f"latest month {month}; no Champions chaos slugs found"
    return _result(
        source,
        url=listing_url,
        outcome=outcome,
        status=listing.status,
        content_type=listing.content_type,
        latency_ms=listing.latency_ms,
        detail=detail,
    )


def probe_pokepaste(source: dict[str, Any]) -> ProbeResult:
    url = "https://pokepast.es/fca60814d40888c8/raw"
    response = _http_get(url, headers={"Accept": "text/plain"})
    text = response.body.decode("utf-8", errors="replace")
    if response.error or response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    ok = "Ability:" in text and "- " in text
    return _result(
        source,
        url=url,
        outcome="ok" if ok else "failed",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(text)} bytes of raw paste text",
    )


def probe_pokedata_events(source: dict[str, Any]) -> ProbeResult:
    today = datetime.now(timezone.utc).date()
    start = (today - timedelta(days=3)).isoformat()
    end = (today + timedelta(days=14)).isoformat()
    url = (
        "https://pokedata.ovh/events/apiv2/_vg/challenges/cups/"
        f"_start/{start}/_end/{end}"
    )
    response = _http_get(url)
    if response.error or response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    text = response.body.decode("utf-8", errors="replace")
    start = text.find("{")
    if start < 0:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail="event locator returned no JSON object",
        )
    payload = json.loads(text[start:])
    events = payload.get("events") or []
    return _result(
        source,
        url=url,
        outcome="ok" if events else "failed",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(events)} events",
    )


def probe_pokedata_standings(source: dict[str, Any]) -> ProbeResult:
    url = "https://www.pokedata.ovh/standings2/standings/1000088_Masters.json"
    response = _http_get(url)
    if response.error or response.status != 200:
        return _result(
            source,
            url=url,
            outcome="failed",
            status=response.status or None,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
            detail=response.error or f"HTTP {response.status}",
        )
    payload = json.loads(response.body)
    players = payload.get("standings", {}).get("players", [])
    return _result(
        source,
        url=url,
        outcome="ok" if players else "failed",
        status=response.status,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=f"{len(players)} players",
    )


def probe_championsmeta() -> ProbeResult:
    source = {"id": "championsmeta", "role": "retired"}
    url = "https://championsmeta.io/"
    response = _http_get(url)
    text = response.body.decode("utf-8", errors="replace")
    retired = response.status == 402 and "DEPLOYMENT_DISABLED" in text
    return _result(
        source,
        url=url,
        outcome="retired" if retired else "degraded",
        status=response.status or None,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=(
            "HTTP 402 DEPLOYMENT_DISABLED"
            if retired
            else "source is reachable again; review before re-adding"
        ),
    )


def probe_championslab() -> ProbeResult:
    source = {"id": "championslab", "role": "retired"}
    url = "https://www.championslab.xyz/meta"
    response = _http_get(url)
    text = response.body.decode("utf-8", errors="replace")
    rsc = "__next_f" in text or "self.__next_f" in text
    return _result(
        source,
        url=url,
        outcome="retired",
        status=response.status or None,
        content_type=response.content_type,
        latency_ms=response.latency_ms,
        detail=(
            "Next.js RSC shell; data is not available to webfetch"
            if rsc
            else "retired from the automated stack"
        ),
    )


PROBES: dict[str, Callable[[dict[str, Any]], ProbeResult]] = {
    "regulation-set-m-c": probe_regulation,
    "regulation-set-m-d": probe_regulation,
    "official-roster-m-c": probe_official_roster,
    "championship-series-calendar": probe_calendar,
    "championship-series-results": probe_results,
    "infovgc": lambda source: _simple(
        source, url=source["canonical_url"], markers=("infovgc",)
    ),
    "labmaus": probe_labmaus,
    "limitless": probe_limitless,
    "pokestats": probe_pokestats,
    "smogon": probe_smogon,
    "pikalytics-champions": lambda source: _simple(
        source, url=source["canonical_url"], markers=("Pikalytics",)
    ),
    "pokebase": lambda source: _simple(
        source, url=source["canonical_url"], markers=("PokéBase",)
    ),
    "pokepaste": probe_pokepaste,
    "pokedata-events": probe_pokedata_events,
    "pokedata-standings": probe_pokedata_standings,
    "victory-road": lambda source: _simple(
        source, url=source["canonical_url"], markers=("Victory Road",)
    ),
}

RETIRED_PROBES: dict[str, Callable[[], ProbeResult]] = {
    "championsmeta": probe_championsmeta,
    "championslab": probe_championslab,
}


def load_registry(path: Path = REPO_ROOT / REGISTRY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("registry must be an object with a sources list")
    return payload


def offline_check(registry: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    registry_ids = {source["id"] for source in registry["sources"]}
    for source_id in sorted(registry_ids):
        if source_id not in PROBES:
            issues.append(f"registry source has no probe: {source_id}")
    for source_id in sorted(PROBES):
        if source_id not in registry_ids:
            issues.append(f"probe has no registry source: {source_id}")
    for source_id in sorted(RETIRED_PROBES):
        if source_id in registry_ids:
            issues.append(f"retired source is still in the registry: {source_id}")
    return issues


def probe_all(
    registry: dict[str, Any],
    *,
    only: set[str] | None = None,
    include_retired: bool = True,
) -> tuple[list[ProbeResult], list[ProbeResult]]:
    results: list[ProbeResult] = []
    for source in registry["sources"]:
        if only and source["id"] not in only:
            continue
        probe = PROBES.get(source["id"])
        if probe is None:
            results.append(
                _result(
                    source,
                    url=source["canonical_url"],
                    outcome="failed",
                    status=None,
                    content_type="",
                    latency_ms=0,
                    detail="no probe configured",
                )
            )
            continue
        try:
            results.append(probe(source))
        except Exception as exc:  # noqa: BLE001 - one source must not abort the run
            results.append(
                _result(
                    source,
                    url=source["canonical_url"],
                    outcome="failed",
                    status=None,
                    content_type="",
                    latency_ms=0,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
    retired: list[ProbeResult] = []
    if include_retired and not only:
        for source_id, probe in RETIRED_PROBES.items():
            try:
                retired.append(probe())
            except Exception as exc:  # noqa: BLE001
                retired.append(
                    ProbeResult(
                        source_id=source_id,
                        role="retired",
                        url="",
                        outcome="degraded",
                        http_status=None,
                        content_type="",
                        latency_ms=0,
                        detail=f"{type(exc).__name__}: {exc}",
                        checked_at=_now(),
                    )
                )
    return results, retired


def _render_markdown(results: list[ProbeResult], retired: list[ProbeResult]) -> str:
    lines = [
        "| Source | Role | Outcome | HTTP | Latency | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for item in [*results, *retired]:
        detail = item.detail.replace("|", "\\|")
        lines.append(
            f"| `{item.source_id}` | `{item.role}` | `{item.outcome}` | "
            f"{item.http_status or '-'} | {item.latency_ms} ms | {detail} |"
        )
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--only", help="Comma-separated source ids")
    parser.add_argument("--no-retired", action="store_true")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    registry = load_registry()
    issues = offline_check(registry)
    if args.offline:
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1
        print(
            f"Offline probe check passed for {len(registry['sources'])} registry sources "
            f"and {len(RETIRED_PROBES)} retired sources."
        )
        return 0
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1

    only = {item.strip() for item in args.only.split(",") if item.strip()} if args.only else None
    results, retired = probe_all(
        registry, only=only, include_retired=not args.no_retired
    )
    if args.json:
        print(
            json.dumps(
                {
                    "checked_at": _now(),
                    "results": [asdict(item) for item in results],
                    "retired": [asdict(item) for item in retired],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    elif args.markdown:
        print(_render_markdown(results, retired))
    else:
        for item in [*results, *retired]:
            print(
                f"{item.outcome:8} {item.source_id:32} "
                f"{item.http_status or '-':>4} {item.latency_ms:>5} ms  {item.detail}"
            )

    failed = [item for item in results if item.outcome == "failed"]
    degraded = [item for item in results if item.outcome == "degraded"]
    if args.strict and degraded:
        failed.extend(degraded)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

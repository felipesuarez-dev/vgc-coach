#!/usr/bin/env python3
"""Resolve the current Pokemon Champions regulation from official sources.

The resolver is deterministic and read-only. It reads the official Pokemon HOME
news feed, parses the latest Champions regulation page, fetches the eligible
roster, and compares the result with the curated live-source registry.

It never edits the registry. The regulation transition runbook uses the
comparison to prepare an upcoming regulation or activate one whose official
window has started.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import regulation_watch  # noqa: E402

REGISTRY_PATH = Path("docs/skills/shared/references/live-source-registry.yaml")
DATE_PATTERN = re.compile(
    r"([A-Z][a-z]+ \d{1,2}, \d{4}),?\s+at\s+(\d{2}:\d{2})\s+UTC"
)
CODE_PATTERN = re.compile(r"Regulation Set (M-[A-Z])")
ROSTER_PATTERN = re.compile(
    r'href="(https://web-view\.app\.pokemonchampions\.jp/[^"]*pokemon\.html)"'
)


@dataclass
class ResolvedRegulation:
    checked_at: str
    feed_url: str
    feed_entry_id: str
    page_url: str
    regulation_id: str
    code: str
    display_name: str
    start: str
    end: str
    phase: str
    roster_url: str | None
    roster_count: int
    roster_pending: bool = False
    new_megas: list[str] = field(default_factory=list)
    mechanics: list[str] = field(default_factory=list)
    held_item_rules: list[str] = field(default_factory=list)


@dataclass
class RegistryMismatch:
    severity: str
    field: str
    expected: Any
    actual: Any
    message: str


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_page_datetime(date_text: str, time_text: str) -> datetime:
    parsed = datetime.strptime(f"{date_text} {time_text}", "%B %d, %Y %H:%M")
    return parsed.replace(tzinfo=timezone.utc)


def _section_lines(text: str, heading: str, stop_headings: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.strip().lower() == heading.lower()
        )
    except StopIteration:
        return []
    collected: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped and stripped.lower() in {item.lower() for item in stop_headings}:
            break
        if stripped:
            collected.append(stripped)
    return collected


def parse_regulation_page(html_text: str, page_url: str) -> dict[str, Any]:
    text, links = regulation_watch.extract_page(html_text)
    code_match = CODE_PATTERN.search(text)
    if not code_match:
        raise ValueError("official page does not name a Regulation Set M-X")
    code = code_match.group(1)
    dates = DATE_PATTERN.findall(text)
    if len(dates) < 2:
        raise ValueError("official page does not contain a start and end UTC timestamp")
    start = _parse_page_datetime(*dates[0])
    end = _parse_page_datetime(*dates[1])
    if start > end:
        raise ValueError("official page start is after end")
    roster_url = next(
        (
            urljoin(page_url, link)
            for link in links
            if "web-view.app.pokemonchampions.jp" in link and "pokemon.html" in link
        ),
        None,
    )
    if not roster_url:
        roster_match = ROSTER_PATTERN.search(html_text)
        roster_url = roster_match.group(1) if roster_match else None

    new_megas: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("• Mega "):
            value = stripped[2:].strip()
            if value not in new_megas:
                new_megas.append(value)

    mechanics = _section_lines(
        text,
        "Mechanics",
        ("Held Items", "Eligible Pokémon", "Eligible Pokemon", "What Are Regulations?"),
    )
    held_items = _section_lines(
        text,
        "Held Items",
        ("Eligible Pokémon", "Eligible Pokemon", "Notes", "What Are Regulations?", "Regulation Set"),
    )

    return {
        "code": code,
        "regulation_id": f"regulation-{code.lower()}",
        "display_name": f"Regulation Set {code}",
        "start": _timestamp(start),
        "end": _timestamp(end),
        "page_url": page_url,
        "roster_url": roster_url,
        "new_megas": new_megas,
        "mechanics": mechanics,
        "held_item_rules": held_items,
    }


def phase_for(start: datetime, end: datetime, now: datetime) -> str:
    if now < start:
        return "upcoming"
    if now > end:
        return "ended"
    return "current"


def resolve_regulation(
    *,
    now: datetime | None = None,
    fetch: Callable[[str], bytes] = regulation_watch.fetch,
) -> ResolvedRegulation:
    checked_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    feed = json.loads(fetch(regulation_watch.FEED_URL))
    entries = regulation_watch.champions_regulation_entries(feed)
    latest = max(entries, key=lambda entry: (entry["pubAt"], entry["stAt"]))
    page_url = urljoin(regulation_watch.NEWS_BASE_URL, latest["link"])
    page_html = fetch(page_url).decode("utf-8", errors="replace")
    parsed = parse_regulation_page(page_html, page_url)
    roster: list[str] = []
    if parsed["roster_url"]:
        roster_html = fetch(parsed["roster_url"]).decode("utf-8", errors="replace")
        roster = regulation_watch.extract_eligible_pokemon(roster_html)
    start = datetime.fromisoformat(parsed["start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(parsed["end"].replace("Z", "+00:00"))
    return ResolvedRegulation(
        checked_at=_timestamp(checked_at),
        feed_url=regulation_watch.FEED_URL,
        feed_entry_id=latest["id"],
        page_url=page_url,
        regulation_id=parsed["regulation_id"],
        code=parsed["code"],
        display_name=parsed["display_name"],
        start=parsed["start"],
        end=parsed["end"],
        phase=phase_for(start, end, checked_at),
        roster_url=parsed["roster_url"],
        roster_count=len(roster),
        roster_pending=parsed["roster_url"] is None,
        new_megas=parsed["new_megas"],
        mechanics=parsed["mechanics"],
        held_item_rules=parsed["held_item_rules"],
    )


def load_registry(path: Path = REPO_ROOT / REGISTRY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("registry must be an object with a sources list")
    return payload


def compare_with_registry(
    resolved: ResolvedRegulation, registry: dict[str, Any]
) -> list[RegistryMismatch]:
    sources = [source for source in registry["sources"] if isinstance(source, dict)]
    mismatches: list[RegistryMismatch] = []

    current = [
        source
        for source in sources
        if source.get("role") == "official_regulation"
        and source.get("temporal_status") == "current"
    ]
    if len(current) != 1:
        mismatches.append(
            RegistryMismatch(
                "blocking",
                "official_regulation.current",
                1,
                len(current),
                "registry must have exactly one current official regulation",
            )
        )

    target_status = "current" if resolved.phase == "current" else "upcoming"
    target = [
        source
        for source in sources
        if source.get("role") == "official_regulation"
        and source.get("temporal_status") == target_status
        and source.get("regulation_id") == resolved.regulation_id
    ]
    if resolved.phase == "ended":
        mismatches.append(
            RegistryMismatch(
                "blocking",
                "official_regulation.phase",
                "current",
                "ended",
                f"{resolved.code} ended at {resolved.end}; activate the successor",
            )
        )
    elif not target:
        severity = "blocking" if resolved.phase == "current" else "warning"
        message = (
            f"registry has no {target_status} source for {resolved.code}"
            + ("; activate it" if resolved.phase == "current" else "; prepare it")
        )
        mismatches.append(
            RegistryMismatch(
                severity,
                "official_regulation",
                resolved.regulation_id,
                None,
                message,
            )
        )
    else:
        source = target[0]
        if source.get("canonical_url") != resolved.page_url:
            mismatches.append(
                RegistryMismatch(
                    "blocking",
                    "official_regulation.canonical_url",
                    resolved.page_url,
                    source.get("canonical_url"),
                    "official regulation URL does not match the resolved page",
                )
            )
        window = source.get("active_window") or {}
        if window.get("start") != resolved.start or window.get("end") != resolved.end:
            mismatches.append(
                RegistryMismatch(
                    "blocking",
                    "official_regulation.active_window",
                    {"start": resolved.start, "end": resolved.end},
                    window,
                    "official regulation window does not match the resolved page",
                )
            )

    roster_target = [
        source
        for source in sources
        if source.get("role") == "official_roster"
        and source.get("temporal_status") == target_status
        and source.get("regulation_id") == resolved.regulation_id
    ]
    if resolved.roster_url is None:
        mismatches.append(
            RegistryMismatch(
                "warning",
                "official_roster.pending",
                resolved.regulation_id,
                None,
                "official roster is not published yet; do not add one until the page links it",
            )
        )
    elif resolved.phase != "ended" and not roster_target:
        severity = "blocking" if resolved.phase == "current" else "warning"
        mismatches.append(
            RegistryMismatch(
                severity,
                "official_roster",
                resolved.roster_url,
                None,
                f"registry has no {target_status} roster for {resolved.code}",
            )
        )
    elif roster_target and roster_target[0].get("canonical_url") != resolved.roster_url:
        mismatches.append(
            RegistryMismatch(
                "blocking",
                "official_roster.canonical_url",
                resolved.roster_url,
                roster_target[0].get("canonical_url"),
                "official roster URL does not match the resolved page",
            )
        )

    return mismatches


def blocking_mismatches(mismatches: list[RegistryMismatch]) -> list[RegistryMismatch]:
    return [item for item in mismatches if item.severity == "blocking"]


def render_summary(resolved: ResolvedRegulation, mismatches: list[RegistryMismatch]) -> str:
    lines = [
        f"{resolved.display_name} ({resolved.regulation_id}): {resolved.phase}",
        f"window: {resolved.start} through {resolved.end}",
        f"page: {resolved.page_url}",
    ]
    if resolved.roster_url:
        lines.append(f"roster: {resolved.roster_url} ({resolved.roster_count} entries)")
    else:
        lines.append("roster: not published yet")
    if mismatches:
        lines.append("registry differences:")
        for item in mismatches:
            lines.append(f"- [{item.severity}] {item.message}")
    else:
        lines.append("registry: aligned")
    return "\n".join(lines)


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("--now must include a timezone")
    return parsed.astimezone(timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check-registry", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--now")
    args = parser.parse_args(argv)

    try:
        resolved = resolve_regulation(now=_parse_now(args.now))
        registry = load_registry()
        mismatches = compare_with_registry(resolved, registry)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Regulation resolve failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = asdict(resolved)
        payload["registry_mismatches"] = [asdict(item) for item in mismatches]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_summary(resolved, mismatches))

    if args.check_registry and blocking_mismatches(mismatches):
        return 1
    if args.preview and resolved.phase == "upcoming":
        print("Upcoming regulation detected; prepare it without replacing the current one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

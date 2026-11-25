#!/usr/bin/env python3
"""Fetch LabMaus JSON with the missing intermediate certificate and required headers.

LabMaus serves its leaf certificate without the Sectigo DV R36 intermediate and
gates every `/api/*` request on Origin and Referer matching the site itself.
This module supplies both in code so callers never need a generic `curl -k`.

The bundled intermediate is the public certificate published by Sectigo:
https://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt
Its SHA-256 fingerprint is pinned below. If the server rotates its chain, the
fingerprint check fails loudly instead of silently disabling verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping


BASE_URL = "https://labmaus.net"
ORIGIN = "https://labmaus.net"
REFERER = "https://labmaus.net/"
USER_AGENT = "vgc-coach-labmaus/0.4 (+https://github.com/felipesuarez-dev/vgc-coach)"
DEFAULT_TIMEOUT_SECONDS = 30
CA_PATH = Path(__file__).resolve().parent / "certs" / "sectigo-public-server-auth-ca-dv-r36.pem"
CA_SHA256 = "8c54c334b66ba4e426772af4a3f9136c19a1aec729fdb28c535c07a5a4ef22e0"


class LabMausError(RuntimeError):
    """Raised when LabMaus cannot be fetched or parsed."""


def _certificate_sha256(pem_path: Path = CA_PATH) -> str:
    pem = pem_path.read_text()
    der = ssl.PEM_cert_to_DER_cert(pem)
    return hashlib.sha256(der).hexdigest()


def labmaus_ssl_context(ca_path: Path = CA_PATH) -> ssl.SSLContext:
    """Build a verifying TLS context with the bundled Sectigo intermediate."""
    actual = _certificate_sha256(ca_path)
    if actual != CA_SHA256:
        raise LabMausError(
            f"LabMaus intermediate fingerprint changed: expected {CA_SHA256}, got {actual}"
        )
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(ca_path))
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def labmaus_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Origin": ORIGIN,
        "Referer": REFERER,
        "User-Agent": USER_AGENT,
    }


def build_url(path: str, params: Mapping[str, Any] | None = None) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    url = f"{BASE_URL}{normalized}"
    if params:
        query = urllib.parse.urlencode(
            {key: value for key, value in params.items() if value is not None}
        )
        url = f"{url}?{query}"
    return url


def labmaus_regulation_label(code: str) -> str:
    code = code.strip().upper()
    return f"Regulation Set {code}"


class LabMausClient:
    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._ssl_context = ssl_context

    def _context(self) -> ssl.SSLContext:
        if self._ssl_context is None:
            self._ssl_context = labmaus_ssl_context()
        return self._ssl_context

    def _url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{normalized}"
        if params:
            query = urllib.parse.urlencode(
                {key: value for key, value in params.items() if value is not None}
            )
            url = f"{url}?{query}"
        return url

    def get_json(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> Any:
        url = self._url(path, params)
        request = urllib.request.Request(url, headers=labmaus_headers())
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout, context=self._context()
            ) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:200].decode("utf-8", errors="replace")
            raise LabMausError(
                f"LabMaus HTTP {exc.code} for {url}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise LabMausError(f"LabMaus request failed for {url}: {exc.reason}") from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise LabMausError(f"LabMaus returned non-JSON for {url}") from exc

    def completed_tournaments(self, date_from: str, date_to: str) -> Any:
        return self.get_json(
            "/api/completed_tournaments",
            {"date_range": f"{date_from} to {date_to}"},
        )

    def discover_teams(
        self, date_from: str, date_to: str, regulation: str
    ) -> Any:
        return self.get_json(
            "/api/discover_teams",
            {
                "date_range": f"{date_from} to {date_to}",
                "regulation": labmaus_regulation_label(regulation),
            },
        )

    def top_trending_pokemon(
        self, *, trend: str = "upwards", quantity: int = 10, language: str = "en"
    ) -> Any:
        return self.get_json(
            "/api/top_trending_pokemon",
            {"language": language, "trend": trend, "quantity": quantity},
        )

    def top_teams(self) -> Any:
        return self.get_json("/api/top_teams")


def _write_output(payload: Any, output: Path | None) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    common.add_argument("--output", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    completed = subparsers.add_parser(
        "completed-tournaments", parents=[common]
    )
    completed.add_argument("--from", dest="date_from", required=True)
    completed.add_argument("--to", dest="date_to", required=True)

    discover = subparsers.add_parser("discover-teams", parents=[common])
    discover.add_argument("--from", dest="date_from", required=True)
    discover.add_argument("--to", dest="date_to", required=True)
    discover.add_argument("--regulation", required=True, help="Code such as M-C")

    trending = subparsers.add_parser("trending", parents=[common])
    trending.add_argument("--trend", choices=("upwards", "downwards"), default="upwards")
    trending.add_argument("--quantity", type=int, default=10)
    trending.add_argument("--language", default="en")

    subparsers.add_parser("top-teams", parents=[common])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    client = LabMausClient(timeout=args.timeout)
    try:
        if args.command == "completed-tournaments":
            payload = client.completed_tournaments(args.date_from, args.date_to)
        elif args.command == "discover-teams":
            payload = client.discover_teams(
                args.date_from, args.date_to, args.regulation
            )
        elif args.command == "trending":
            payload = client.top_trending_pokemon(
                trend=args.trend, quantity=args.quantity, language=args.language
            )
        else:
            payload = client.top_teams()
    except LabMausError as exc:
        print(f"LabMaus fetch failed: {exc}", file=sys.stderr)
        return 1
    _write_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

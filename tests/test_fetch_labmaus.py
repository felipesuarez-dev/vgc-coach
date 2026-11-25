from __future__ import annotations

import http.server
import json
import ssl
import sys
import threading
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import fetch_labmaus  # noqa: E402


class _Handler(http.server.BaseHTTPRequestHandler):
    received_headers: dict[str, str] = {}
    status = 200
    payload = b'[{"id": 1}]'

    def do_GET(self):  # noqa: N802
        type(self).received_headers = dict(self.headers)
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(type(self).payload)

    def log_message(self, format, *args):  # noqa: A003
        return


class FetchLabMausTests(unittest.TestCase):
    def test_bundled_certificate_fingerprint_is_pinned(self):
        self.assertEqual(
            fetch_labmaus._certificate_sha256(fetch_labmaus.CA_PATH),
            fetch_labmaus.CA_SHA256,
        )

    def test_context_verifies_hostname_and_chain(self):
        context = fetch_labmaus.labmaus_ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_headers_match_the_site_contract(self):
        headers = fetch_labmaus.labmaus_headers()
        self.assertEqual(headers["Origin"], "https://labmaus.net")
        self.assertEqual(headers["Referer"], "https://labmaus.net/")
        self.assertEqual(headers["Accept"], "application/json")

    def test_regulation_label_matches_labmaus_query(self):
        self.assertEqual(fetch_labmaus.labmaus_regulation_label("M-C"), "Regulation Set M-C")
        self.assertEqual(fetch_labmaus.labmaus_regulation_label(" m-d "), "Regulation Set M-D")

    def test_build_url_encodes_params(self):
        url = fetch_labmaus.build_url(
            "/api/discover_teams",
            {"date_range": "2026-11-17 to 2026-11-24", "regulation": "Regulation Set M-C"},
        )
        self.assertIn("date_range=2026-11-17+to+2026-11-24", url)
        self.assertIn("regulation=Regulation+Set+M-C", url)

    def test_client_sends_origin_referer_and_parses_json(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = fetch_labmaus.LabMausClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                ssl_context=ssl.create_default_context(),
            )
            payload = client.get_json("/api/completed_tournaments")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(payload, [{"id": 1}])
        self.assertEqual(_Handler.received_headers["Origin"], "https://labmaus.net")
        self.assertEqual(_Handler.received_headers["Referer"], "https://labmaus.net/")

    def test_http_error_is_wrapped(self):
        class ErrorHandler(_Handler):
            status = 403
            payload = b'{"error":"unauthorized"}'

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ErrorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = fetch_labmaus.LabMausClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                ssl_context=ssl.create_default_context(),
            )
            with self.assertRaisesRegex(fetch_labmaus.LabMausError, "HTTP 403"):
                client.get_json("/api/completed_tournaments")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_invalid_json_is_wrapped(self):
        class InvalidHandler(_Handler):
            payload = b"not json"

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), InvalidHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = fetch_labmaus.LabMausClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                ssl_context=ssl.create_default_context(),
            )
            with self.assertRaisesRegex(fetch_labmaus.LabMausError, "non-JSON"):
                client.get_json("/api/completed_tournaments")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    unittest.main()

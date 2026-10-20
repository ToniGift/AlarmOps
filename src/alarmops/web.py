"""Tiny read-only web front for the live deployment (Cloud Run). SIMULATION ONLY.

    GET /          the plain-English explainer page
    GET /api/replay measured replay results as JSON (summary; no raw series)
    GET /healthz   health check

The results are computed once at start-up from the committed dataset. The server takes
no input, writes nothing, and uses only the standard library.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .explainer import render_explainer
from .scenarios import build_report

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:",
    "Cache-Control": "no-store",
}


def make_handler(report: dict):
    page = render_explainer(report).encode("utf-8")
    api = {k: v for k, v in report.items() if k not in ("series", "tank_faults")}
    api_body = (json.dumps(api, indent=2) + "\n").encode("utf-8")
    health = b'{"status":"ok","simulation":true}\n'

    class Handler(BaseHTTPRequestHandler):
        server_version = "AlarmOps"
        sys_version = ""

        def _send(self, code: int, body: bytes, ctype: str, head_only: bool = False):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            if not head_only:
                self.wfile.write(body)

        def _route(self, head_only: bool):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8", head_only)
            elif path == "/api/replay":
                self._send(200, api_body, "application/json", head_only)
            elif path == "/healthz":
                self._send(200, health, "application/json", head_only)
            else:
                self._send(404, b"not found\n", "text/plain; charset=utf-8", head_only)

        def do_GET(self):
            self._route(False)

        def do_HEAD(self):
            self._route(True)

        def _reject(self):
            self._send(405, b"read-only service\n", "text/plain; charset=utf-8")

        do_POST = do_PUT = do_DELETE = do_PATCH = _reject

        def log_message(self, fmt, *args):   # one line per request on stderr (Cloud Run logs)
            super().log_message(fmt, *args)

    return Handler


def serve(host: str = "0.0.0.0", port: int | None = None) -> ThreadingHTTPServer:
    port = int(os.environ.get("PORT", "8080")) if port is None else port
    return ThreadingHTTPServer((host, port), make_handler(build_report()))


def main() -> int:
    server = serve()
    print(f"AlarmOps (simulation) listening on {server.server_address[0]}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

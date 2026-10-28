#!/usr/bin/env python3
"""Local server for the daily brief pages, with an endpoint that opens links in the default browser.

Usage: python3 -I serve.py [DIR] [PORT]    (defaults: the config's archive_dir, 8765; binds 127.0.0.1 only)

Serves DIR read-only, like `python3 -m http.server`, plus:
  GET  /__brief  -> "daily-brief-server 2 <plugin version>"; lets the skill tell this server from a plain http.server
  GET  /__adapters -> {"asana": true|false, "todos": true|false, "today": "YYYY-MM-DD"|null}; whether the page's
                    Apply can write to Asana (a tracker is configured and its keyring token exists) and to the
                    todos Slack List (todos is configured and `claude` is on the PATH), and today in user.timezone,
                    the only day it writes for
  POST /open     -> body {"url": "..."}; runs `xdg-open <url>` (macOS `open`), so the link opens in the default
                    browser (or, for slack://, the Slack app) instead of the Claude browser pane.
  POST /apply/asana -> body {"day": "YYYY-MM-DD", "items": [{"gid", "status"?, "priority"?, "take"?, "complete"?,
                    "log"?: {"minutes", "date"}}]}; writes the changes to Asana with the keyring token, reads the
                    touched sections again and re-renders today's saved page. 200 with a result per item (each naming
                    the changes that "landed"), 207 when some failed, 400 for a body that names anything outside today's brief (nothing is written).
  POST /apply/todos -> body {"day", "done": [Record ID], "add": [{"task", "due", "notes"}]}; runs a headless `claude -p`
                    (built-in tools: ToolSearch only; pre-approved: the Slack list tools; user settings still load)
                    to set records to Done and add records, then re-renders today's page from the list it read back.
                    200/207 with a result per item, 400 for anything outside today's todos (claude is not run), 409
                    while another run is in flight, 502 when claude's reply is unreadable, its tool calls show no
                    whole read of the list after its writes, or they reach outside the request.
/open only takes https:// links to the hosts the brief links to, plus slack:// deep links. It
requires the X-Daily-Brief header (a cross-site page can't send it without a CORS preflight, which
this server never approves) and refuses any Origin other than this server's own. /apply/asana and
/apply/todos also require an Origin and the newest saved brief to be today's. /apply/asana takes every gid and value
from that brief; /apply/todos checks Record IDs against it and validates the new rows.
Every request must name this server in its Host header (127.0.0.1:PORT or localhost:PORT).
"""
import functools
import http.server
import importlib.util
import json
import pathlib
import re
import socketserver
import subprocess
import sys
import threading
import urllib.parse

here = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, here / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = load_module("daily_brief_config", "config.py")
apply_asana = load_module("daily_brief_apply_asana", "apply_asana.py")
todos_claude = load_module("daily_brief_todos_claude", "todos_claude.py")

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else config.defaults()["archive_dir"]).expanduser()
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
PLUGIN_JSON = pathlib.Path(__file__).resolve().parent.parent.parent / ".claude-plugin" / "plugin.json"
ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
LOCAL_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
MAX_APPLY_BODY = 16 * 1024
APPLY_LOCK = threading.Lock()
TODOS_LOCK = threading.Lock()
REFUSED = object()
OPENER = "open" if sys.platform == "darwin" else "xdg-open"
HOSTS = re.compile(r"(^|\.)(asana\.com|slack\.com|google\.com|zoom\.us|github\.com|circleci\.com)$")


def plugin_version():
    try:
        return json.loads(PLUGIN_JSON.read_text())["version"]
    except (OSError, ValueError, KeyError):
        return "unknown"


def allowed(url):
    if not isinstance(url, str) or len(url) > 4096:
        return False
    u = urllib.parse.urlsplit(url)
    if u.scheme == "slack":
        return True
    return u.scheme == "https" and bool(u.hostname) and bool(HOSTS.search(u.hostname))


class Handler(http.server.SimpleHTTPRequestHandler):
    def parse_request(self):
        if not super().parse_request():
            return False
        # A DNS-rebound hostname makes another site same-origin with this server.
        if self.headers.get("Host") not in LOCAL_HOSTS:
            self._send(403, "forbidden")
            return False
        return True

    def do_GET(self):
        if self.path == "/__brief":
            return self._send(200, f"daily-brief-server 2 {plugin_version()}")
        if self.path == "/__adapters":
            return self._send_json(200, {"asana": apply_asana.available(), "todos": todos_claude.available(),
                                         "today": apply_asana.today()})
        super().do_GET()

    def end_headers(self):
        # Pages are rebuilt in place after every update, so the pane must never show a cached copy.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path == "/apply/asana":
            return self._apply_asana()
        if self.path == "/apply/todos":
            return self._apply_todos()
        if self.path != "/open":
            return self._send(404, "not found")
        origin = self.headers.get("Origin")
        if self.headers.get("X-Daily-Brief") != "1" or (origin and origin not in ORIGINS):
            return self._send(403, "forbidden")
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 8192)))
            url = body.get("url")
        except (ValueError, AttributeError):
            return self._send(400, "bad request")
        if not allowed(url):
            return self._send(400, "url not allowed")
        rc = subprocess.run([OPENER, url], capture_output=True, timeout=10).returncode
        self._send(200 if rc == 0 else 502, "ok" if rc == 0 else "open failed")

    def check_write(self):
        """The JSON body of a write from this server's own page, or REFUSED once a refusal has been sent."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        raw = self.rfile.read(max(0, min(length, MAX_APPLY_BODY + 1)))
        if length > len(raw):
            self.rfile.read(min(length - len(raw), 1 << 20))
        if self.headers.get("Origin") not in ORIGINS or self.headers.get("X-Daily-Brief") != "1":
            self._send_json(403, {"error": "forbidden"})
            return REFUSED
        if not 0 < length <= MAX_APPLY_BODY:
            self._send_json(400, {"error": "the body must be 1 byte to 16 KB of JSON"})
            return REFUSED
        try:
            return json.loads(raw)
        except ValueError:
            self._send_json(400, {"error": "the body is not JSON"})
            return REFUSED

    def _apply_asana(self):
        body = self.check_write()
        if body is REFUSED:
            return
        try:
            with APPLY_LOCK:
                code, payload = apply_asana.apply(body, ROOT)
        except Exception as e:
            print(f"apply/asana failed: {type(e).__name__}", file=sys.stderr)
            return self._send_json(500, {"error": "internal error"})
        self._send_json(code, payload)

    def _apply_todos(self):
        body = self.check_write()
        if body is REFUSED:
            return
        if not TODOS_LOCK.acquire(blocking=False):
            return self._send_json(409, {"error": "another todos apply is still running; wait for it to finish"})
        try:
            code, payload = todos_claude.apply(body, ROOT, write_lock=APPLY_LOCK)
        except Exception as e:
            print(f"apply/todos failed: {type(e).__name__}", file=sys.stderr)
            return self._send_json(500, {"error": "internal error"})
        finally:
            TODOS_LOCK.release()
        self._send_json(code, payload)

    def _send_json(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send(self, code, text):
        data = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class BriefServer(http.server.ThreadingHTTPServer):
    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=str(ROOT))
    BriefServer(("127.0.0.1", PORT), handler).serve_forever()

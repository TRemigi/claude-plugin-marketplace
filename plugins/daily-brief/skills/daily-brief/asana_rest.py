#!/usr/bin/env python3
"""The daily brief's one Asana REST client, with a CLI behind log-time.sh and time-window.sh.

Usage: python3 -I asana_rest.py log [--dry-run] <task_gid> <duration> [YYYY-MM-DD]
       python3 -I asana_rest.py window <start YYYY-MM-DD> <end YYYY-MM-DD> <task_gid>...
log     duration is 45m | 1h | 1h30m | 90 (bare number = minutes); prints "logged <n>m on <day> (task <gid>)".
window  prints "<gid> <minutes>" per task (entries whose entered_on is in start..end), or "<gid> error".
The token is read from the keyring item (macOS Keychain, or libsecret via secret-tool elsewhere) named by tracker.pat_keychain_item in the daily-brief
config, held in memory only and never printed or put on a command line. DAILY_BRIEF_ASANA_BASE
replaces the API base only when it is http://127.0.0.1:<port> (for a local stand-in server).
"""
import datetime
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

here = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("daily_brief_config", here / "config.py")
config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(config)

API = "https://app.asana.com/api/1.0"
LOOPBACK_BASE = re.compile(r"http://127\.0\.0\.1:[0-9]+")
GID = re.compile(r"[0-9]+")
DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TASK_FIELDS = ("name,assignee.name,due_on,completed,permalink_url,actual_time_minutes,created_at,"
               "custom_fields.gid,custom_fields.display_value")
PAGE_LIMIT = 100
MAX_PAGES = 100
TIMEOUT = 20


class AsanaError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Unavailable(Exception):
    pass


def api_base(env=None):
    override = (os.environ if env is None else env).get("DAILY_BRIEF_ASANA_BASE", "")
    return override if LOOPBACK_BASE.fullmatch(override) else API


def keychain_item():
    try:
        return config.lookup(config.load(), "tracker.pat_keychain_item")
    except config.ConfigError as e:
        raise Unavailable(str(e))
    except KeyError as e:
        raise Unavailable(f"{e.args[0]}: not set in {config.config_path()}")


def _lookup_command(item, secret):
    if sys.platform == "darwin":
        return ["security", "find-generic-password", "-s", item] + (["-w"] if secret else [])
    return ["secret-tool", "lookup", "service", item]


def _security(item, secret):
    cmd = _lookup_command(item, secret)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None


def has_token():
    try:
        item = keychain_item()
    except Unavailable:
        return False
    found = _security(item, secret=False)
    return found is not None and found.returncode == 0


def read_token():
    item = keychain_item()
    found = _security(item, secret=True)
    token = found.stdout.strip() if found is not None and found.returncode == 0 else ""
    if not token:
        raise Unavailable(f"error: keyring item '{item}' not found")
    return token


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _gid(value):
    if not isinstance(value, str) or not GID.fullmatch(value):
        raise ValueError("task gid must be numeric")
    return value


class Client:
    def __init__(self, token, base=None):
        self._token = token
        self.base = base or api_base()

    def __repr__(self):
        return "<asana_rest.Client>"

    def request(self, method, path, body=None, query=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(query) if query else "")
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            with _opener.open(urllib.request.Request(url, data, headers, method=method), timeout=TIMEOUT) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise AsanaError(e.code, _error_text(e.read(65536)))
        except (urllib.error.URLError, OSError) as e:
            raise AsanaError(0, f"could not reach Asana ({getattr(e, 'reason', e)})")
        try:
            return json.loads(raw) if raw else {}
        except ValueError:
            return {}

    def pages(self, path, query):
        offset, out = None, []
        for _ in range(MAX_PAGES):
            page = self.request("GET", path, query={**query, "limit": PAGE_LIMIT, **({"offset": offset} if offset else {})})
            out.extend(page.get("data") or [])
            offset = (page.get("next_page") or {}).get("offset")
            if not offset:
                break
        return out

    def section_tasks(self, section_gid):
        return self.pages(f"/sections/{_gid(section_gid)}/tasks", {"opt_fields": TASK_FIELDS})

    def move_task(self, gid, section_gid):
        self.request("POST", f"/sections/{_gid(section_gid)}/addTask", {"data": {"task": _gid(gid)}})

    def update_task(self, gid, fields):
        self.request("PUT", f"/tasks/{_gid(gid)}", {"data": fields})

    def log_time(self, gid, minutes, day):
        body = time_entry_body(minutes, day)
        self.request("POST", f"/tasks/{_gid(gid)}/time_tracking_entries", body)

    def window_minutes(self, gids, start, end):
        """{gid: minutes tracked between start and end inclusive, or None when that task's entries can't be read}."""
        out = {}
        for gid in gids:
            try:
                entries = self.pages(f"/tasks/{_gid(gid)}/time_tracking_entries", {"opt_fields": "duration_minutes,entered_on"})
            except (AsanaError, ValueError):
                out[gid] = None
                continue
            out[gid] = sum(e.get("duration_minutes") or 0 for e in entries if start <= (e.get("entered_on") or "") <= end)
        return out


def _error_text(raw):
    try:
        errors = json.loads(raw).get("errors", [])
        return "; ".join(e.get("message", "") for e in errors)
    except (ValueError, AttributeError, TypeError):
        return "unparseable"


def time_entry_body(minutes, day):
    return {"data": {"duration_minutes": minutes, "entered_on": day}}


def parse_minutes(text):
    if GID.fullmatch(text):
        return int(text)
    m = re.fullmatch(r"(?:([0-9]+)h)?(?:([0-9]+)m)?", text)
    if text and m:
        return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    raise ValueError("duration must look like 45m, 1h, 1h30m or 90")


def _fail(message, code):
    print(message, file=sys.stderr)
    return code


def _client():
    try:
        return Client(read_token())
    except Unavailable as e:
        raise SystemExit(_fail(str(e), 3))


def cli_log(args):
    dry = bool(args) and args[0] == "--dry-run"
    args = args[1:] if dry else args
    if len(args) < 2 or len(args) > 3:
        return _fail("usage: asana_rest.py log [--dry-run] <task_gid> <duration> [YYYY-MM-DD]", 2)
    gid, duration = args[0], args[1]
    day = args[2] if len(args) == 3 else datetime.date.today().isoformat()
    if not GID.fullmatch(gid):
        return _fail("error: task gid must be numeric", 2)
    if not DAY.fullmatch(day):
        return _fail("error: date must be YYYY-MM-DD", 2)
    try:
        minutes = parse_minutes(duration)
    except ValueError as e:
        return _fail(f"error: {e}", 2)
    if not 0 < minutes <= 1440:
        return _fail("error: duration must be 1-1440 minutes", 2)
    if dry:
        body = json.dumps(time_entry_body(minutes, day), separators=(",", ":"))
        print(f"DRY RUN: POST {api_base()}/tasks/{gid}/time_tracking_entries {body}")
        return 0
    client = _client()
    try:
        client.log_time(gid, minutes, day)
    except AsanaError as e:
        return _fail(f"error: HTTP {e.status}: {e.message}", 1)
    print(f"logged {minutes}m on {day} (task {gid})")
    return 0


def cli_window(args):
    if len(args) < 2:
        return _fail("usage: asana_rest.py window <start YYYY-MM-DD> <end YYYY-MM-DD> <task_gid>...", 2)
    start, end, gids = args[0], args[1], args[2:]
    if not (DAY.fullmatch(start) and DAY.fullmatch(end)):
        return _fail("error: dates must be YYYY-MM-DD", 2)
    if not gids:
        return 0
    client = _client()
    for gid in gids:
        minutes = client.window_minutes([gid], start, end)[gid]
        print(f"{gid} error" if minutes is None else f"{gid} {minutes}")
    return 0


def main(argv):
    commands = {"log": cli_log, "window": cli_window}
    if argv and argv[0] in commands:
        return commands[argv[0]](argv[1:])
    return _fail("usage: asana_rest.py log [--dry-run] <task_gid> <duration> [YYYY-MM-DD] | window <start> <end> <task_gid>...", 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

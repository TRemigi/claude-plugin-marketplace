"""POST /apply/asana. serve.py owns the HTTP guards; this owns what a body may change and the writes."""
import datetime
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zoneinfo

here = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, here / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = _load("daily_brief_config", "config.py")
asana_rest = _load("daily_brief_asana_rest", "asana_rest.py")
brief_data = _load("daily_brief_data", "brief_data.py")

DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
GID = re.compile(r"[0-9]+")
ITEM_KEYS = {"gid", "status", "priority", "take", "complete", "log"}
CHANGE_KEYS = ITEM_KEYS - {"gid"}
PRIORITY_VALUES = ("P1", "P2", "P3", "unset")
MAX_ITEMS = 100


class Refused(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def available():
    return asana_rest.has_token()


def today():
    try:
        return _today(_config()).isoformat()
    except Refused:
        return None


def apply(body, root):
    try:
        return _apply(body, pathlib.Path(root))
    except Refused as e:
        return e.status, {"error": e.message}


def _apply(body, root):
    cfg, tracker = _tracker()
    today = _today(cfg)
    data, plans = _plan(body, root, tracker, today)
    if not asana_rest.has_token():
        raise Refused(503, "no Asana token in the Keychain")
    try:
        client = asana_rest.Client(asana_rest.read_token())
    except asana_rest.Unavailable as e:
        raise Refused(503, str(e))
    results, touched, logged = _write(client, plans)
    payload = {"results": results}
    if touched or logged:
        try:
            _refresh(client, data, tracker, today, touched, logged, root)
        except asana_rest.AsanaError as e:
            payload["refresh"] = f"The changes were written, but reading the board again failed: {e.message}"
        except RenderFailed as e:
            payload["refresh"] = f"The changes were written, but the page could not be rebuilt: {e}"
        except Exception as e:
            payload["refresh"] = f"The changes were written, but the page could not be refreshed ({type(e).__name__}). Reload before applying again."
    ok = all(r["ok"] for r in results) and "refresh" not in payload
    return (200 if ok else 207), payload


class RenderFailed(Exception):
    pass


def _config():
    try:
        return config.load()
    except config.ConfigError:
        raise Refused(503, "the daily-brief config is missing or invalid")


def _tracker():
    cfg = _config()
    if not isinstance(cfg.get("tracker"), dict):
        raise Refused(503, "no tracker is configured")
    return cfg, cfg["tracker"]


def _today(cfg):
    try:
        return datetime.datetime.now(zoneinfo.ZoneInfo(cfg["user"]["timezone"])).date()
    except (zoneinfo.ZoneInfoNotFoundError, KeyError, ValueError):
        raise Refused(503, "user.timezone is not a known timezone")


def _newest_day(root):
    days = [f.stem for f in root.glob("*.json") if DAY.fullmatch(f.stem)]
    return max(days) if days else None


def _plan(body, root, tracker, today):
    if not isinstance(body, dict) or set(body) != {"day", "items"}:
        raise Refused(400, 'the body must be {"day", "items"}')
    day = body["day"]
    if not isinstance(day, str) or not DAY.fullmatch(day) or day != today.isoformat() or day != _newest_day(root):
        raise Refused(400, "only today's brief can be applied; open the newest page")
    try:
        data = json.loads((root / f"{day}.json").read_text())
    except (OSError, ValueError):
        raise Refused(400, "today's saved brief cannot be read")
    items = body["items"]
    if not isinstance(items, list) or not items or len(items) > MAX_ITEMS:
        raise Refused(400, f"items must be a list of 1 to {MAX_ITEMS}")
    ops = data.get("ops") or {}
    rows = {r.get("gid"): r for r in ops.get("rows") or []}
    untracked = {u.get("gid"): u for u in data.get("untracked", ops.get("untracked")) or []}
    seen, plans = set(), []
    for item in items:
        plans.append(_plan_item(item, rows, untracked, tracker, today, seen))
    return data, plans


def _plan_item(item, rows, untracked, tracker, today, seen):
    if not isinstance(item, dict) or not set(item) <= ITEM_KEYS:
        raise Refused(400, "an item has a field this page does not send")
    gid = item.get("gid")
    if not isinstance(gid, str) or not GID.fullmatch(gid) or (gid not in rows and gid not in untracked):
        raise Refused(400, f"task {gid} is not in today's brief")
    if gid in seen:
        raise Refused(400, f"task {gid} appears twice")
    seen.add(gid)
    if not set(item) & CHANGE_KEYS:
        raise Refused(400, f"task {gid} has no change")
    row = rows.get(gid)
    if row is None and set(item) - {"gid", "log"}:
        raise Refused(400, f"task {gid} is an untracked card: only time can be logged on it")
    label = f"#{row['n']} {row['name']}" if row else f"task {gid}"
    sections = tracker["sections"]
    by_status = {s["status"]: s for s in sections}
    plan = {"gid": gid, "label": label, "row": row, "move": None, "move_note": None, "fields": {}, "field_notes": [],
            "log": None, "log_note": None, "move_keys": [k for k in ("status", "complete") if k in item],
            "field_keys": [k for k in ("priority", "take", "complete") if k in item]}

    status = item.get("status")
    if "status" in item and status not in by_status:
        raise Refused(400, f"{label}: {status!r} is not a status on the board")
    complete = item.get("complete", False)
    if not isinstance(complete, bool):
        raise Refused(400, f"{label}: complete must be true or false")
    if complete:
        done = next((s for s in sections if s.get("role") == "done"), None)
        if done is None:
            raise Refused(400, f"{label}: the board has no Done section")
        status = done["status"]
    if status is not None:
        plan["move"] = (row["status"], status, by_status[status]["gid"])
        plan["move_note"] = f"{row['status']} → {status}" if status != row["status"] else f"moved to {status}"
        if by_status[status].get("role") == "done":
            plan["fields"]["completed"] = True

    if "priority" in item:
        priority = item["priority"]
        field = (tracker.get("fields") or {}).get("priority")
        if priority not in PRIORITY_VALUES or not field:
            raise Refused(400, f"{label}: priority must be P1, P2, P3 or unset")
        plan["fields"]["custom_fields"] = {field["gid"]: None if priority == "unset" else field["options"][priority]}
        plan["field_notes"].append(f"priority {priority}")

    take = item.get("take", False)
    if not isinstance(take, bool):
        raise Refused(400, f"{label}: take must be true or false")
    if take:
        if row.get("assignee"):
            raise Refused(400, f"{label}: already assigned to {row['assignee']}")
        plan["fields"]["assignee"] = "me"
        plan["field_notes"].append("assigned to you")

    if "log" in item:
        plan["log"] = _log(item["log"], label, today)
        plan["log_note"] = f"logged {_duration(plan['log'][0])} on {plan['log'][1]}"
    return plan


def _log(entry, label, today):
    if not isinstance(entry, dict) or set(entry) != {"minutes", "date"}:
        raise Refused(400, f"{label}: log must be {{minutes, date}}")
    minutes, date = entry["minutes"], entry["date"]
    if isinstance(minutes, bool) or not isinstance(minutes, int) or not 1 <= minutes <= 1440:
        raise Refused(400, f"{label}: log minutes must be 1 to 1440")
    try:
        when = datetime.date.fromisoformat(date) if isinstance(date, str) and DAY.fullmatch(date) else None
    except ValueError:
        when = None
    if when is None or when > today:
        raise Refused(400, f"{label}: log date must be a past or current YYYY-MM-DD")
    return minutes, date


def _duration(minutes):
    h, m = divmod(minutes, 60)
    return (f"{h}h" if h else "") + (f"{m}m" if m else "")


def _write(client, plans):
    results, touched, logged = [], set(), set()
    for plan in plans:
        done, landed = [], set()
        try:
            if plan["move"]:
                client.move_task(plan["gid"], plan["move"][2])
                touched.update(plan["move"][:2])
                done.append(plan["move_note"])
            landed.update(k for k in plan["move_keys"] if k != "complete")
            if plan["fields"]:
                client.update_task(plan["gid"], plan["fields"])
                if plan["row"]:
                    touched.add(plan["row"]["status"])
                done.extend(plan["field_notes"])
            landed.update(plan["move_keys"] + plan["field_keys"])
            if plan["log"]:
                client.log_time(plan["gid"], *plan["log"])
                logged.add(plan["gid"])
                if plan["row"]:
                    touched.add(plan["row"]["status"])
                done.append(plan["log_note"])
                landed.add("log")
        except asana_rest.AsanaError as e:
            where = f"HTTP {e.status}" if e.status else "no response"
            results.append({"gid": plan["gid"], "ok": False, "landed": sorted(landed),
                            "message": _failure(plan, done, f"failed ({where}): {e.message}")})
            continue
        except Exception as e:
            results.append({"gid": plan["gid"], "ok": False, "landed": sorted(landed),
                            "message": _failure(plan, done, f"failed ({type(e).__name__}); check Asana before applying it again")})
            continue
        results.append({"gid": plan["gid"], "ok": True, "landed": sorted(landed),
                        "message": f"{plan['label']}: " + (" · ".join(done or ["no change needed"]))})
    return results, touched, logged


def _failure(plan, done, reason):
    landed = f"{' · '.join(done)} · then " if done else ""
    return f"{plan['label']}: {landed}{reason}"


def _refresh(client, data, tracker, today, touched, logged, root):
    sections = tracker["sections"]
    fields = tracker.get("fields") or {}
    key_field, priority_field = fields.get("key"), (fields.get("priority") or {}).get("gid")
    fresh = {}
    for s in sections:
        if s["status"] in touched and s.get("role") != "done":
            fresh[s["status"]] = [brief_data.task_row(t, s["status"], key_field, priority_field)
                                  for t in client.section_tasks(s["gid"]) if not t.get("completed")]
    ops = data.setdefault("ops", {"rows": []})
    old_rows = ops.get("rows") or []
    known = {r["gid"] for r in old_rows}
    rows = brief_data.merge_sections(old_rows, fresh)
    wanted = set(logged) | {r["gid"] for rs in fresh.values() for r in rs if r["gid"] not in known and r["total"]}
    start, end = brief_data.yesterday_window(today.isoformat())
    minutes = client.window_minutes(sorted(wanted), start, end)
    for r in rows:
        if r["gid"] in minutes:
            r["yday"] = "?" if minutes[r["gid"]] is None else minutes[r["gid"]] or None
    ops["rows"] = brief_data.order_ops(rows, sections)
    holder = data if "untracked" in data else ops
    if "untracked" in holder:
        holder["untracked"] = [u for u in holder["untracked"] if not minutes.get(u.get("gid"))]
    brief_data.refresh_stats(data)
    data.pop("nav", None)
    _render(data, root)


def _render(data, root):
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / "data.json"
        source.write_text(json.dumps(data, ensure_ascii=False))
        try:
            done = subprocess.run([sys.executable, "-I", str(here / "render-panel.py"), str(source), str(pathlib.Path(tmp) / "page.html"),
                                   "--archive", str(root)], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            raise RenderFailed("render-panel.py timed out")
    if done.returncode != 0:
        raise RenderFailed((done.stderr.strip().splitlines() or ["render-panel failed"])[-1])

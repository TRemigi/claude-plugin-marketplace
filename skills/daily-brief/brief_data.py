"""Row ordering, numbering and stat tiles for the brief's board (section 2 of SKILL.md), as code.

render-panel.py and serve.py both use these, so a brief built in a session and a page refreshed after
an in-page apply order and number their rows by the same rule.

Usage: python3 -I brief_data.py order <data.json>
order   orders and numbers ops.rows in that file in place, for the terminal-only brief that prints
        its own table instead of rendering the page.
"""
import datetime
import importlib.util
import json
import pathlib
import sys

PRIORITIES = ("P1", "P2", "P3")


def _priority_rank(row):
    p = row.get("priority")
    return PRIORITIES.index(p) if p in PRIORITIES else len(PRIORITIES)


def order_ops(rows, sections):
    """Board rows in display order, numbered 1..n (Backlog rows B1..), completed and Done rows dropped.

    Order: status in board order, then priority P1, P2, P3, unset, then created ascending, then the
    order the rows came in. `sections` is the config's tracker.sections.
    """
    roles = {s["status"]: s.get("role") for s in sections}
    backlog = {s for s, role in roles.items() if role == "backlog"} or {"Backlog"}
    done = {s for s, role in roles.items() if role == "done"}
    rank = {s["status"]: i for i, s in enumerate(sections)}
    for r in rows:
        rank.setdefault(r.get("status"), len(rank))
    live = [dict(r) for r in rows if not r.get("completed") and r.get("status") not in done]
    live.sort(key=lambda r: (rank[r.get("status")], _priority_rank(r), r.get("created") or ""))
    main = [r for r in live if r.get("status") not in backlog]
    later = [r for r in live if r.get("status") in backlog]
    for i, r in enumerate(main, 1):
        r["n"] = str(i)
    for i, r in enumerate(later, 1):
        r["n"] = f"B{i}"
    return main + later


def order_todos(rows, today):
    """Open todos in display order: Doing, then overdue, then by due date, undated last; Done rows dropped
    and a blank status read as To do. `today` is an ISO day; dated rows get a dueLabel like "Oct 5"."""
    open_rows = []
    for r in rows:
        status = r.get("status") or "To do"
        if status == "Done":
            continue
        row = {"id": r["id"], "task": r.get("task") or "", "status": status, "due": r.get("due") or "", "notes": r.get("notes") or ""}
        if row["due"]:
            day = datetime.date.fromisoformat(row["due"])
            row["dueLabel"] = f"{day:%b} {day.day}"
        open_rows.append(row)
    open_rows.sort(key=lambda r: (r["status"] != "Doing", not (r["due"] and r["due"] < today), not r["due"], r["due"]))
    return open_rows


def refresh_stats(data):
    ops = data.get("ops")
    untracked = data.get("untracked", (ops or {}).get("untracked"))
    todos = data.get("todos")
    counts = {}
    if ops is not None:
        counts["Active tasks"] = sum(1 for r in ops.get("rows", []) if not str(r.get("n", "")).startswith("B"))
    if untracked is not None:
        counts["Untracked"] = len(untracked)
    if todos is not None:
        counts["Todos open"] = len(todos.get("rows", []))
    for tile in data.get("stats", []):
        if tile.get("label") in counts:
            tile["value"] = str(counts[tile["label"]])
            if tile["label"] == "Untracked":
                if counts["Untracked"]:
                    tile["tone"] = "warning"
                else:
                    tile.pop("tone", None)
    return data


def yesterday_window(today):
    """(start, end) ISO days of the brief's "yesterday": Friday to Sunday on a Monday, else the day before."""
    day = datetime.date.fromisoformat(today)
    end = day - datetime.timedelta(days=1)
    start = day - datetime.timedelta(days=3) if day.weekday() == 0 else end
    return start.isoformat(), end.isoformat()


def task_row(task, status, key_field, priority_field):
    fields = {f.get("gid"): f.get("display_value") for f in task.get("custom_fields") or []}
    priority = fields.get(priority_field)
    return {"gid": task["gid"], "name": task.get("name") or "", "url": task.get("permalink_url"),
            "assignee": (task.get("assignee") or {}).get("name"), "due": task.get("due_on") or "", "status": status,
            "total": task.get("actual_time_minutes") or None, "yday": None, "key": fields.get(key_field) or None,
            "priority": priority if priority in PRIORITIES else None, "created": task.get("created_at")}


def merge_sections(rows, fresh):
    """`rows` with every row in a refreshed status replaced by `fresh[status]`; a refreshed row keeps the
    Yday cell it had before, since the fetch doesn't carry it."""
    before = {r["gid"]: r for r in rows}
    refreshed = {r["gid"] for status_rows in fresh.values() for r in status_rows}
    merged = [r for r in rows if r.get("status") not in fresh and r["gid"] not in refreshed]
    for status_rows in fresh.values():
        for r in status_rows:
            old = before.get(r["gid"])
            merged.append({**r, "yday": old.get("yday") if old else r.get("yday")})
    return merged


def _order_file(path):
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("daily_brief_config", here / "config.py")
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    data = json.loads(pathlib.Path(path).read_text())
    if isinstance(data.get("ops"), dict) and "rows" in data["ops"]:
        try:
            tracker = config.load().get("tracker", {}) if config.config_path().exists() else {}
        except config.ConfigError as e:
            sys.exit(f"error: {e}")
        data["ops"]["rows"] = order_ops(data["ops"]["rows"], tracker.get("sections", []))
    pathlib.Path(path).write_text(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    if len(sys.argv) != 3 or sys.argv[1] != "order":
        sys.exit("usage: brief_data.py order <data.json>")
    _order_file(sys.argv[2])

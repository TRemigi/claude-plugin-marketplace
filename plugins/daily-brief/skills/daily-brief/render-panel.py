#!/usr/bin/env python3
"""Build the side-panel daily brief page from brief data.

Usage: python3 -I render-panel.py <data.json> <out.html> [--archive DIR]
--archive DIR also saves the page and its data as DIR/<YYYY-MM-DD>.html and .json (date from the
data's "today"; a re-run the same day overwrites that day's copy), links it to the nearest saved days
with prev/next arrows, and rebuilds the previous saved day so its "next" arrow points here.
Orders and numbers the board rows with brief_data.order_ops first, so a saved day always holds the
numbering the page shows. Injects the data into brief.html (with every "<" escaped so data can't close the script tag)
and wraps it in panel-shell.html, which supplies the page chrome, theme tokens and icons.
"""
import datetime
import html
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent


def write_private(path, text):
    """Archived briefs hold calendar and Slack content, so they are readable by this user only."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(text)


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("daily_brief_config", here / "config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
spec = importlib.util.spec_from_file_location("daily_brief_data", here / "brief_data.py")
brief_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brief_data)
try:
    port = config.setting("port")
except config.ConfigError as e:
    sys.exit(f"error: {e}")
args = sys.argv[1:]
archive = None
if "--archive" in args:
    i = args.index("--archive")
    archive = pathlib.Path(args[i + 1]).expanduser()
    del args[i:i + 2]
data_path, out_path = args[0], args[1]

data = json.loads(pathlib.Path(data_path).read_text())
if "theme" not in data:
    # The side panel doesn't report the desktop's appearance to the page, so read it at build time.
    if sys.platform == "darwin":
        cmd, dark = ["defaults", "read", "-g", "AppleInterfaceStyle"], "Dark"
    else:
        cmd, dark = ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], "'prefer-dark'"
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        data["theme"] = "dark" if out.stdout.strip() == dark else "light"
    except (OSError, subprocess.SubprocessError):
        pass

BOARD = []  # the board's columns in config order, so the page needs no status names of its own
if isinstance(data.get("ops"), dict) and "rows" in data["ops"]:
    tracker = config.load().get("tracker", {}) if config.config_path().exists() else {}
    BOARD = [{"status": s["status"], "role": s["role"]} for s in tracker.get("sections", [])]
    data["ops"]["rows"] = brief_data.order_ops(data["ops"]["rows"], tracker.get("sections", []))

brief = (here / "brief.html").read_text()
if brief.count("/*DATA*/null") != 1 or brief.count("<!--STATIC-->") != 1:
    sys.exit("error: brief.html must contain exactly one /*DATA*/null and one <!--STATIC--> placeholder")
shell = (here / "panel-shell.html").read_text()
if shell.count("<!--BRIEF-->") != 1:
    sys.exit("error: panel-shell.html must contain exactly one <!--BRIEF--> marker")

def static_html(d):
    """Script-free copy of the brief. The side panel reopens a saved page as a static snapshot that
    runs no JavaScript, which would otherwise leave it blank; the live script removes this copy."""
    e = lambda s: html.escape(str(s if s is not None else ""))
    a = lambda txt, url: f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(txt)}</a>' \
        if isinstance(url, str) and url.startswith("https://") else e(txt)
    dur = lambda m: "" if not m or not isinstance(m, int) else (f"{m // 60}h" if m >= 60 else "") + (f"{m % 60}m" if m % 60 else "")
    out = [f'<div id="db-static" style="line-height:1.5"><h1 style="margin:0 0 4px">Daily Brief · {e(d.get("date"))}</h1>',
           '<p style="color:var(--text-muted);margin:0 0 12px">Static copy (no scripts). For the interactive page open '
           f'http://127.0.0.1:{port}/{e(d.get("today"))}.html with the brief server running.</p>']
    if d.get("recap"): out.append(f"<p>{e(d['recap'])}</p>")
    fails = d.get("failures") or {}
    note = lambda k: f'<p style="color:var(--text-warning)">{e(fails[k])}</p>' if fails.get(k) else ""
    titles = d.get("titles") or {}
    cal = d.get("calendar")
    if cal is not None:
        out.append("<h2>Schedule</h2>" + note("calendar"))
        for s in cal.get("sections", []):
            items = "".join(f"<li>{e(r.get('time'))} — {a(r.get('title'), r.get('url'))}"
                            + (f" ({e(r['note'])})" if r.get("note") else "")
                            + (f" · {a('join', r['join'])}" if r.get("join") else "") + "</li>" for r in s.get("rows", []))
            out.append(f"<h3>{e(s.get('name'))}</h3><ul>{items}</ul>")
        if cal.get("footer"): out.append(f"<p>{e(cal['footer'])}</p>")
    sm = d.get("summary")
    if sm is not None:
        out.append(f"<h2>Yesterday · {e(sm.get('label'))}</h2>" + note("summary"))
        for g in sm.get("groups", []):
            items = "".join("<li>" + "".join(a(p[0], p[1]) if len(p) > 1 else e(p[0]) for p in item) + "</li>"
                            for item in g.get("items", []))
            out.append(f"<h3>{e(g.get('t'))}</h3><ul>{items}</ul>")
    ops = d.get("ops")
    un = d.get("untracked", (ops or {}).get("untracked"))
    if un is not None:
        def suggested(u):  # same format as the page's fmt: 1h30m, 45m, 2h
            m = u.get("suggest")
            if type(m) is not int or not 1 <= m <= 1440:
                return ""
            return " · suggested " + (f"{m // 60}h" if m >= 60 else "") + (f"{m % 60}m" if m % 60 else "")
        items = "".join(f"<li>{e(u.get('key') or '')} {a(u.get('name'), u.get('url'))} — {e(u.get('activity'))} · {e(u.get('status'))}{suggested(u)}</li>" for u in un)
        out.append(f"<h2>Untracked yesterday ({len(un)})</h2><ul>{items}</ul>")
    if ops is not None:
        out.append(f"<h2>{e(titles.get('ops') or 'Tasks')}</h2>" + note("ops"))
        rows = ops.get("rows", [])
        backlog_names = {s["status"] for s in ops.get("sections", []) if s.get("role") == "backlog"} or {"Backlog"}
        main = [r for r in rows if r.get("status") not in backlog_names]
        trs = "".join(f"<tr><td>{e(r.get('n'))}</td><td>{e(r.get('key') or '')}</td><td>{e(r.get('priority') or '—')}</td>"
                      f"<td>{a(r.get('name'), r.get('url'))}</td><td>{e(r.get('assignee') or '—')}</td>"
                      f"<td>{e(dur(r.get('total')))}</td><td>{e(r.get('status'))}</td></tr>" for r in main)
        out.append('<table style="border-collapse:collapse"><tr><th>#</th><th>Key</th><th>Pri</th><th>Task</th>'
                   f"<th>Owner</th><th>Total</th><th>Status</th></tr>{trs}</table>")
        backlog = [r for r in rows if r.get("status") in backlog_names]
        if backlog:
            mine = sum(1 for r in backlog if r.get("assignee") == ops.get("me"))
            out.append(f"<p>Backlog: {len(backlog)} open ({mine} yours)</p>")
        for n in ops.get("notes") or []: out.append(f'<p style="color:var(--text-muted)">{e(n)}</p>')
    td = d.get("todos")
    if td is not None:
        out.append(f"<h2>{e(titles.get('todos') or 'Todos')} ({len(td.get('rows', []))} open)</h2>" + note("todos"))
        items = "".join(f"<li>{e(t.get('task'))}" + (f" — due {e(t['due'])}" if t.get("due") else "")
                        + (f" · {e(t['notes'])}" if t.get("notes") else "") + "</li>" for t in td.get("rows", []))
        if items: out.append(f"<ul>{items}</ul>")
    out.append("</div>")
    return "".join(out)


def build(d):
    if isinstance(d.get("ops"), dict) and BOARD:
        d["ops"]["sections"] = BOARD
    payload = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c")
    page = brief.replace("/*DATA*/null", payload).replace("<!--STATIC-->", static_html(d), 1)
    return shell.replace("<!--BRIEF-->", page)


def nav_for(day, folder):
    """Closest saved day before and after `day` in the archive folder (gaps like weekends are skipped)."""
    days = sorted(f.stem for f in folder.glob("*.json") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", f.stem))
    prev = [x for x in days if x < day]
    nxt = [x for x in days if x > day]
    label = lambda x: datetime.date.fromisoformat(x).strftime("%a, %b %-d")
    nav = {}
    if prev: nav["prev"] = {"href": prev[-1] + ".html", "label": label(prev[-1])}
    if nxt: nav["next"] = {"href": nxt[0] + ".html", "label": label(nxt[0])}
    return nav, (prev[-1] if prev else None)


if archive:
    day = str(data.get("today", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        sys.exit("error: data.today must be YYYY-MM-DD to archive")
    archive.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_private(archive / f"{day}.json", json.dumps(data, ensure_ascii=False, indent=1))
    data["nav"], prev_day = nav_for(day, archive)

pathlib.Path(out_path).write_text(build(data))
print(out_path)

if archive:
    write_private(archive / f"{day}.html", build(data))
    print(archive / f"{day}.html")
    # Rebuild the previous saved day so its "next" arrow points here.
    if prev_day:
        pd = json.loads((archive / f"{prev_day}.json").read_text())
        pd["nav"], _ = nav_for(prev_day, archive)
        write_private(archive / f"{prev_day}.html", build(pd))

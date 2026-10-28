#!/usr/bin/env python3
"""Config for the daily brief: one JSON file holds every id and name the skill needs.

Usage: python3 -I config.py validate | show | get <dotted.path> | path
Path: $DAILY_BRIEF_CONFIG, else $XDG_CONFIG_HOME/daily-brief/config.json (~/.config when unset).
A symlink there (a dotfile manager's) is followed; a file anyone can write to is refused.
validate  exits 0, or prints one "<path>: <problem>" per line and exits 1.
show      prints the whole config as one JSON object, archive_dir and port defaults filled;
          an unset optional value is simply absent.
get       prints a scalar bare, or a list/object as JSON; list items are addressed by index
          (tracker.sections.0.gid). archive_dir (default $XDG_DATA_HOME/daily-brief/briefs, ~ expanded; an existing
          ~/daily-briefs keeps being used until the new folder exists) and port
          (default 8765) fall back to their defaults when unset.
path      prints the resolved config path.
"""
import json
import os
import pathlib
import sys

LEGACY_ARCHIVE = pathlib.Path("~/daily-briefs").expanduser()
TRACKER_ROLES = ("backlog", "active", "done")
CHANNEL_MATCHES = ("deploys", "mentions")


class ConfigError(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


def _xdg_dir(var, fallback):
    """The XDG base directory named by var; the spec says to ignore a relative value."""
    value = os.environ.get(var, "")
    return pathlib.Path(value) if os.path.isabs(value) else pathlib.Path(fallback).expanduser()


def config_path():
    override = os.environ.get("DAILY_BRIEF_CONFIG")
    if override:
        return pathlib.Path(override).expanduser()
    return _xdg_dir("XDG_CONFIG_HOME", "~/.config") / "daily-brief" / "config.json"


def defaults():
    archive = _xdg_dir("XDG_DATA_HOME", "~/.local/share") / "daily-brief" / "briefs"
    if LEGACY_ARCHIVE.is_dir() and not archive.exists():
        archive = LEGACY_ARCHIVE
    return {"archive_dir": str(archive), "port": 8765}


def read():
    path = config_path()
    try:
        text = path.read_text()
        if path.stat().st_mode & 0o002:
            raise ConfigError([f"config: {path} is writable by everyone; run chmod o-w on it"])
    except FileNotFoundError:
        raise ConfigError([f"config: not found at {path}"])
    except OSError as e:
        raise ConfigError([f"config: cannot read {path}: {e.strerror}"])
    try:
        return json.loads(text)
    except ValueError as e:
        raise ConfigError([f"config: invalid JSON in {path}: {e}"])


def _is_str(v):
    return isinstance(v, str) and v.strip() != ""


def _is_https(v):
    return _is_str(v) and v.startswith("https://")


def _obj(node, path, errors, required=()):
    if not isinstance(node, dict):
        errors.append(f"{path}: must be an object")
        return False
    for k in required:
        if k not in node:
            errors.append(f"{path}.{k}: required" if path else f"{k}: required")
    return True


def _text(node, key, path, errors, required=True, check=_is_str, msg="must be a non-empty string"):
    here = f"{path}.{key}" if path else key
    if key not in node:
        if required:
            errors.append(f"{here}: required")
    elif not check(node[key]):
        errors.append(f"{here}: {msg}")


def _list(node, key, path, errors, required=True):
    here = f"{path}.{key}" if path else key
    if key not in node:
        if required:
            errors.append(f"{here}: required")
        return []
    if not isinstance(node[key], list):
        errors.append(f"{here}: must be a list")
        return []
    return node[key]


def _id_list(node, key, path, errors):
    here = f"{path}.{key}"
    items = _list(node, key, path, errors)
    if key in node and isinstance(node[key], list) and not (items and all(_is_str(i) for i in items)):
        errors.append(f"{here}: must be a non-empty list of strings")


def _named_ids(node, path, errors):
    if _obj(node, path, errors, required=("name", "ids")):
        _text(node, "name", path, errors, required=False)
        _id_list(node, "ids", path, errors)


def _validate_calendar(cal, errors):
    if not _obj(cal, "calendar", errors):
        return
    for i, section in enumerate(_list(cal, "sections", "calendar", errors)):
        _named_ids(section, f"calendar.sections.{i}", errors)
    if "merge" in cal:
        _named_ids(cal["merge"], "calendar.merge", errors)
    if "collapse_ooo_on" in cal and not (
        isinstance(cal["collapse_ooo_on"], list) and all(_is_str(i) for i in cal["collapse_ooo_on"])
    ):
        errors.append("calendar.collapse_ooo_on: must be a list of strings")
    if cal.get("extra_calendars", "own-section") != "own-section":
        errors.append("calendar.extra_calendars: must be own-section")


def _validate_slack(slack, errors):
    if not _obj(slack, "slack", errors, required=("user_id", "team_id", "workspace_url")):
        return
    _text(slack, "user_id", "slack", errors, required=False)
    _text(slack, "team_id", "slack", errors, required=False)
    _text(slack, "workspace_url", "slack", errors, required=False, check=_is_https, msg="must be an https:// URL")
    _text(slack, "github_handle", "slack", errors, required=False)
    for i, ch in enumerate(_list(slack, "channels", "slack", errors, required=False)):
        path = f"slack.channels.{i}"
        if _obj(ch, path, errors, required=("id", "name", "match")):
            _text(ch, "id", path, errors, required=False)
            _text(ch, "name", path, errors, required=False)
            if "match" in ch and ch["match"] not in CHANNEL_MATCHES:
                errors.append(f"{path}.match: must be one of {', '.join(CHANNEL_MATCHES)}")


def _validate_tracker(tr, errors):
    required = ("type", "name", "workspace_id", "project", "sections", "pat_keychain_item")
    if not _obj(tr, "tracker", errors, required=required):
        return
    if "type" in tr and tr["type"] != "asana":
        errors.append("tracker.type: must be asana")
    for key in ("name", "workspace_id", "project", "pat_keychain_item"):
        _text(tr, key, "tracker", errors, required=False)
    for i, sec in enumerate(_list(tr, "sections", "tracker", errors, required=False)):
        path = f"tracker.sections.{i}"
        if _obj(sec, path, errors, required=("status", "gid", "role")):
            _text(sec, "status", path, errors, required=False)
            _text(sec, "gid", path, errors, required=False)
            if "role" in sec and sec["role"] not in TRACKER_ROLES:
                errors.append(f"{path}.role: must be one of {', '.join(TRACKER_ROLES)}")
    if "fields" in tr and _obj(tr["fields"], "tracker.fields", errors):
        fields = tr["fields"]
        _text(fields, "key", "tracker.fields", errors, required=False)
        _text(fields, "estimate", "tracker.fields", errors, required=False)
        if "priority" in fields and _obj(fields["priority"], "tracker.fields.priority", errors, required=("gid", "options")):
            pri = fields["priority"]
            _text(pri, "gid", "tracker.fields.priority", errors, required=False)
            if "options" in pri and _obj(pri["options"], "tracker.fields.priority.options", errors, required=("P1", "P2", "P3")):
                for level in ("P1", "P2", "P3"):
                    _text(pri["options"], level, "tracker.fields.priority.options", errors, required=False)


def _validate_todos(todos, errors):
    if not _obj(todos, "todos", errors, required=("type", "name", "list_id", "url")):
        return
    if "type" in todos and todos["type"] != "slack_list":
        errors.append("todos.type: must be slack_list")
    _text(todos, "name", "todos", errors, required=False)
    _text(todos, "list_id", "todos", errors, required=False)
    _text(todos, "url", "todos", errors, required=False, check=_is_https, msg="must be an https:// URL")


def validate(cfg):
    errors = []
    if not _obj(cfg, "", errors):
        return ["config: must be a JSON object"]
    if "version" not in cfg:
        errors.append("version: required")
    elif cfg["version"] != 1 or isinstance(cfg["version"], bool):
        errors.append("version: must be 1")
    if "user" not in cfg:
        errors.append("user: required")
    elif _obj(cfg["user"], "user", errors, required=("name", "timezone")):
        _text(cfg["user"], "name", "user", errors, required=False)
        _text(cfg["user"], "timezone", "user", errors, required=False)
    if "archive_dir" in cfg and not _is_str(cfg["archive_dir"]):
        errors.append("archive_dir: must be a non-empty string")
    if "port" in cfg and not (
        isinstance(cfg["port"], int) and not isinstance(cfg["port"], bool) and 1024 <= cfg["port"] <= 65535
    ):
        errors.append("port: must be an integer from 1024 to 65535")
    for key, check in (("calendar", _validate_calendar), ("slack", _validate_slack),
                       ("tracker", _validate_tracker), ("todos", _validate_todos)):
        if key in cfg:
            check(cfg[key], errors)
    return errors


def load():
    cfg = read()
    errors = validate(cfg)
    if errors:
        raise ConfigError(errors)
    return cfg


def lookup(cfg, dotted):
    node = cfg
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            if dotted in defaults():
                return defaults()[dotted]
            raise KeyError(dotted)
    return node


def setting(name):
    """archive_dir or port for scripts that must still run before a config exists."""
    try:
        cfg = load()
    except ConfigError as e:
        if not config_path().exists():
            cfg = {}
        else:
            raise e
    return setting_from(cfg, name)


def setting_from(cfg, name):
    value = lookup(cfg, name)
    return os.path.expanduser(value) if name == "archive_dir" else value


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "path" and len(argv) == 1:
        print(config_path())
        return 0
    if cmd == "validate" and len(argv) == 1:
        try:
            read_cfg = read()
        except ConfigError as e:
            print(e)
            return 1
        errors = validate(read_cfg)
        if errors:
            print("\n".join(errors))
            return 1
        return 0
    if cmd == "show" and len(argv) == 1:
        try:
            cfg = load()
        except ConfigError as e:
            print(e, file=sys.stderr)
            return 1
        shown = dict(cfg, **{name: setting_from(cfg, name) for name in defaults()})
        print(json.dumps(shown, ensure_ascii=False))
        return 0
    if cmd == "get" and len(argv) == 2:
        try:
            cfg = load()
        except ConfigError as e:
            print(e, file=sys.stderr)
            return 1
        try:
            value = lookup(cfg, argv[1])
        except KeyError:
            print(f"{argv[1]}: not set in {config_path()}", file=sys.stderr)
            return 1
        if argv[1] == "archive_dir":
            value = os.path.expanduser(value)
        print(json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value)
        return 0
    print(__doc__.split("\n\n")[0].split("\n")[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

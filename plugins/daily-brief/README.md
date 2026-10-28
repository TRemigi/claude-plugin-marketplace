# daily-brief

A daily personal-assistant brief that renders as one local page: a standup-ready summary of what you did yesterday (tracker and Slack), today's calendar grouped by Google calendar, your tracker board as a status table, and your open todos from a Slack List. Scheduled runs are read-only; status changes, assign-to-me, completing, time logging and todo edits happen only when you click Apply on the page or ask in chat.

## Install

```
/plugin install daily-brief --marketplace TRemigi/claude-plugin-marketplace
```

## Skills

- **daily-brief** (`/daily-brief:daily-brief`) — builds the brief, opens it in the Claude app's browser pane, and handles follow-ups: `3 → Review`, `5 take`, `3 +45m`, adding and completing todos, reopening a past day. Sections for sources that are not configured are left out. See `skills/daily-brief/SKILL.md`.
- **setup** (`/daily-brief:setup`) — builds the config by asking you and looking ids up through your own Google Calendar, Slack and Asana connectors, checks that the keyring token item exists (it never reads or asks for the token), and creates the weekday scheduled task. Re-running it edits the existing config. See `skills/setup/SKILL.md`; `skills/setup/check.sh` holds the deterministic checks.

## Config

Every id, name and path comes from one JSON file, `$DAILY_BRIEF_CONFIG` or `$XDG_CONFIG_HOME/daily-brief/config.json` (`~/.config/daily-brief/config.json`). The file holds ids and names only, never the token, so it can live in a dotfiles repo and be symlinked in; a world-writable file is refused. `skills/daily-brief/reference/config.example.json` shows the shape with placeholder values; `python3 -I skills/daily-brief/config.py validate` checks a file and prints one `<path>: <problem>` line per error. Every source (`calendar`, `slack`, `tracker`, `todos`) is optional.

## Scripts

All stdlib Python 3.9 or bash, in `skills/daily-brief/`:

- `config.py` — loads and validates the config (`validate`, `show`, `get <dotted.path>`, `path`).
- `render-panel.py` — injects the brief data into `brief.html`, wraps it in `panel-shell.html`, and optionally archives the day under the archive dir.
- `serve.py` — local server for the archive on 127.0.0.1 (`python3 -I serve.py [DIR] [PORT]`, defaults the config's `archive_dir` and 8765). `GET /__brief` reports `daily-brief-server 2 <version>`; `GET /__adapters` says whether the page's Apply can write to Asana and to the todos list; `POST /open` opens a link in the default browser; `POST /apply/asana` and `POST /apply/todos` write what the page's Apply sends. Every request must name this server in `Host`; writes also need an `Origin` of this server, the `X-Daily-Brief` header, and items from today's saved brief.
- `apply_asana.py`, `asana_rest.py`, `todos_claude.py` — the Asana REST calls and the headless `claude -p` run behind the two Apply endpoints. `brief_data.py` orders and shapes the brief data.
- `time-window.sh`, `log-time.sh` — read and write Asana time tracking with the token from the keyring item named by `tracker.pat_keychain_item`; the token is never printed.

`reference/scheduled-task.md` holds the unattended, read-only prompt for a weekday-morning scheduled task.

Runs on Linux and macOS. The token lives in the system keyring: `secret-tool` (libsecret, e.g. GNOME Keyring) on Linux, `security` (Keychain) on macOS. Links open with `xdg-open` (macOS `open`), and the page theme comes from `gsettings` (macOS `defaults`).

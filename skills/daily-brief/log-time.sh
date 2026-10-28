#!/usr/bin/env bash
# Log time on an Asana task via the time-tracking API (asana_rest.py does the work).
# Usage: log-time.sh [--dry-run] <task_gid> <duration> [YYYY-MM-DD]
#   duration: 45m | 1h | 1h30m | 90 (bare number = minutes)
# Token is read at call time from the macOS Keychain item named by tracker.pat_keychain_item in the
# daily-brief config; never printed.
src="${BASH_SOURCE[0]}"; dir="${src%/*}"; [[ "$dir" == "$src" ]] && dir=.
exec python3 -I "$dir/asana_rest.py" log "$@"

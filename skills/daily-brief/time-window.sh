#!/usr/bin/env bash
# Sum time tracked on Asana tasks within a date window (read-only; asana_rest.py does the work).
# Usage: time-window.sh <start YYYY-MM-DD> <end YYYY-MM-DD> <task_gid>...
# Prints one line per task: "<gid> <minutes>" (minutes whose entered_on falls in start..end, inclusive),
# or "<gid> error" when that task's entries can't be read.
# Token is read at call time from the macOS Keychain item named by tracker.pat_keychain_item in the
# daily-brief config; never printed.
src="${BASH_SOURCE[0]}"; dir="${src%/*}"; [[ "$dir" == "$src" ]] && dir=.
exec python3 -I "$dir/asana_rest.py" window "$@"

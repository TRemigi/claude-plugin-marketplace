#!/bin/sh
# One line per check on stdout, `ok: <check> <detail>` or `missing: <check> <detail>`, exit 0 either
# way: a missing item is an answer for the wizard, not a failure. Exit 2 is a malformed request.

set -u

DEFAULT_ITEM=daily-brief-asana
DEFAULT_PORT=8765

usage() {
  echo "usage: check.sh python | pat <item> | port <n> | tz | all [item [port]]" >&2
  exit 2
}

check_python() {
  version=$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3]); sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null)
  status=$?
  if [ "$status" -eq 0 ]; then
    echo "ok: python $version"
  elif [ -n "$version" ]; then
    echo "missing: python $version"
  else
    echo "missing: python 3.9 or newer is not on PATH"
  fi
}

valid_item() {
  case "$1" in
    "" | -*) return 1 ;;
  esac
}

check_pat() {
  valid_item "$1" || usage
  if [ "$(uname)" = Darwin ]; then
    security find-generic-password -s "$1" >/dev/null 2>&1
  else
    secret-tool lookup service "$1" >/dev/null 2>&1
  fi
  if [ $? -eq 0 ]; then
    echo "ok: pat $1"
  else
    echo "missing: pat $1"
  fi
}

check_tz() {
  target=$(readlink /etc/localtime 2>/dev/null)
  zone=${target#*zoneinfo/}
  if [ "$zone" != "$target" ] && [ -n "$zone" ]; then
    echo "ok: tz $zone"
  else
    echo "missing: tz /etc/localtime is not a link into zoneinfo"
  fi
}

valid_port() {
  case "$1" in
    "" | *[!0-9]*) return 1 ;;
  esac
  [ "${#1}" -le 5 ] && [ "$1" -ge 1024 ] && [ "$1" -le 65535 ]
}

check_port() {
  valid_port "$1" || usage
  if ! command -v python3 >/dev/null 2>&1; then
    echo "missing: port $1 cannot be checked without python3"
    return
  fi
  if python3 -c 'import socket, sys; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", int(sys.argv[1])))' "$1" 2>/dev/null; then
    echo "ok: port $1 free"
    return
  fi
  banner=$(curl -s --max-time 2 "http://127.0.0.1:$1/__brief" 2>/dev/null)
  case "$banner" in
    "daily-brief-server "*) echo "ok: port $1 serving daily-brief-server" ;;
    *) echo "missing: port $1 in use by another program" ;;
  esac
}

[ $# -ge 1 ] || usage
cmd=$1
shift
case "$cmd" in
  python) [ $# -eq 0 ] || usage; check_python ;;
  pat) [ $# -eq 1 ] || usage; check_pat "$1" ;;
  port) [ $# -eq 1 ] || usage; check_port "$1" ;;
  tz) [ $# -eq 0 ] || usage; check_tz ;;
  all)
    [ $# -le 2 ] || usage
    item=${1:-$DEFAULT_ITEM}
    port=${2:-$DEFAULT_PORT}
    valid_item "$item" && valid_port "$port" || usage
    check_python
    check_tz
    check_pat "$item"
    check_port "$port"
    ;;
  *) usage ;;
esac

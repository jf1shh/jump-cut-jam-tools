#!/usr/bin/env bash
# Query the MegaJam canon (Nexus collection `megajam_canon`, corpus in _config/reference/canon/).
# Modelled on ~/Projects/Unrealizer/scripts/ask_canon.sh but fixed to the megajam collection,
# so it never reads the UC2-heavy `unreal_canon`. Hits are leads: check each note's `tier`
# (tested > epic > community) and its source before acting.
set -euo pipefail
canon_backend="${MEGAJAM_CANON_BACKEND:-${HOME}/Projects/nexus/backend}"
canon_python="${MEGAJAM_CANON_PYTHON:-${canon_backend}/venv/bin/python}"
canon_client="${canon_backend}/scripts/ask_unreal_canon.py"
if [[ $# -eq 0 ]]; then
  printf '%s\n' 'Usage: scripts/ask_canon.sh "how do I stop cook exit code 1 from MCP port bind"' >&2
  exit 2
fi
if [[ ! -x "$canon_python" || ! -f "$canon_client" ]]; then
  printf '%s\n' 'Canon client unavailable. Set MEGAJAM_CANON_BACKEND; fall back to: grep -ri "<topic>" _config/reference/canon _config/CANON.md' >&2
  exit 1
fi
# --collection goes BEFORE "$@": after a `--` (needed for questions starting with a dash, e.g.
# `scripts/ask_canon.sh -- -nullrhi`) argparse treats everything as question words. A caller-supplied
# --collection (or abbreviation like --col) would override ours (last wins), so reject it.
for arg in "$@"; do
  [[ "$arg" == "--" ]] && break
  if [[ "$arg" == --col* ]]; then
    printf '%s\n' 'ask_canon.sh is fixed to megajam_canon; do not pass --collection.' >&2
    exit 2
  fi
done
exec "$canon_python" "$canon_client" --collection megajam_canon "$@"

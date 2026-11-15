#!/usr/bin/env bash
# Launch the UE editor (default 5.9 MegaJam Preview; 5.8.4 is the fallback) with the MCP port, in its own memory scope (stages/00_prep/references/jam-day-runbook.md section 2).
# Prints the editor PID on stdout (last line) once the MCP port answers. Progress goes to stderr.
#
#   scripts/launch-editor.sh /abs/path/Project.uproject            engine = 5.9 (UE_VERSION default)
#   UE_VERSION=5.8 scripts/launch-editor.sh /abs/Project.uproject  engine = 5.8.4 fallback (or flag --ue58)
#   scripts/launch-editor.sh /abs/path/UnrealEditor /abs/path/Project.uproject   explicit editor binary wins
#   or set UE_EDITOR and UE_PROJECT. Engine roots: UE59_ROOT (~/Projects/UnrealEngine-5.9), UE58_ROOT (~/Projects/UnrealEngine-5.8).
# SDL_VIDEODRIVER defaults to x11 on the 5.9 path only (its editor fails SDL init on KDE Wayland); the 5.8.4 fallback
# is untouched. A user-set value always wins.
#
# Run `gpu-preflight` first (it is the gate; this script does not replace it).
# Why a script: the improvised `systemd-run ... $HOME ... $(date)` one-liner was denied by the ticket guard
# ("command name is built by the shell"). Calling this file with literal paths gives the guard one plain
# command. If the guard still denies it, the owner adds this allow rule (see PR body / ticket report):
#     Bash(scripts/launch-editor.sh:*)   # guardrails.toml allow, megajam scope
#
# Exit codes: 0 up (PID printed); 2 usage; 3 port already answers (running PID printed if found);
# 4 editor died early; 5 timed out but editor alive (PID printed); 6 waitfor missing;
# 9 the editor logged "HttpListener unable to bind" (port still held by a dying editor): it is stopped, nothing is
# printed, wait a few seconds and relaunch;
# 7 gpu-preflight missing or did not clear within PREFLIGHT_WAIT (gate is on by default when gpu-preflight is on PATH;
# opt out with LAUNCH_PREFLIGHT=0 or PREFLIGHT_BIN=none); 8 port held by a process that does not answer MCP.
# Every wait has a timeout and says what it waits for. Test hooks: WAITFOR_BIN, LAUNCH_SCOPE_CMD (default: the
# systemd-run profile; set to "none" for no scope), MCP_PORT (default 8010), WAIT_TIMEOUT seconds (default 300),
# EDITOR_LOG, DRYRUN=1.
set -u

# Flags first (--ue58 / --ue59 pick the engine), then positionals: [EDITOR] PROJECT, or just PROJECT.
ARGS=()
for a in "$@"; do
  case "$a" in
    --ue58) UE_VERSION=5.8 ;;
    --ue59) UE_VERSION=5.9 ;;
    *) ARGS+=("$a") ;;
  esac
done
if [ "${#ARGS[@]}" -eq 1 ] && [ "${ARGS[0]##*.}" = "uproject" ]; then
  UE_PROJECT="${ARGS[0]}"            # one .uproject argument: the editor comes from UE_VERSION
  UE_EDITOR_ARG=""
else
  UE_EDITOR_ARG="${ARGS[0]:-}"
  UE_PROJECT="${ARGS[1]:-${UE_PROJECT:-}}"
fi
# Engine version: UE_VERSION / --ue5x win. With neither, an explicit editor binary (positional or UE_EDITOR) that lives
# in a 5.8 tree is a 5.8 launch (editor_watchdog passes the binary and no UE_VERSION), so it gets no 5.9 SDL default.
ENGINE_VER="${UE_VERSION:-}"
if [ -z "$ENGINE_VER" ]; then
  case "${UE_EDITOR_ARG:-${UE_EDITOR:-}}" in
    *UnrealEngine-5.8*|*UE_5.8*) ENGINE_VER=5.8 ;;
  esac
fi
case "${ENGINE_VER:-5.9}" in
  5.9|5.9.*) ENGINE_IS_59=1; ENGINE_ROOT="${UE59_ROOT:-$HOME/Projects/UnrealEngine-5.9}" ;;
  5.8|5.8.*) ENGINE_IS_59=0; ENGINE_ROOT="${UE58_ROOT:-$HOME/Projects/UnrealEngine-5.8}" ;;
  *) echo "launch-editor: UE_VERSION must be 5.9 or 5.8 (got ${ENGINE_VER})" >&2; exit 2 ;;
esac
if [ -z "$UE_EDITOR_ARG" ] && [ -n "${UE_EDITOR:-}" ] && [ -n "${UE_VERSION:-}" ]; then
  echo "launch-editor: warning: UE_EDITOR=$UE_EDITOR overrides UE_VERSION/--ue5x" >&2
fi
UE_EDITOR="${UE_EDITOR_ARG:-${UE_EDITOR:-$ENGINE_ROOT/Engine/Binaries/Linux/UnrealEditor}}"
# 5.9's editor cannot start under KDE Wayland without the X11 SDL driver (hub 68 smoke test, 2026-11-10).
# The 5.8.4 fallback launches exactly as before: no SDL default there. A user-set value always wins.
if [ "$ENGINE_IS_59" = 1 ] && [ -z "${SDL_VIDEODRIVER+x}" ]; then export SDL_VIDEODRIVER=x11; fi
MCP_PORT="${MCP_PORT:-8010}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"  # 5.9 can take ~195 s to listen; a dead editor or a bind error ends the wait early

if [ -z "$UE_EDITOR" ] || [ -z "$UE_PROJECT" ]; then
  echo "usage: launch-editor.sh [--ue58|--ue59] [/abs/UnrealEditor] /abs/Project.uproject (UE_VERSION=5.8 for the fallback)" >&2
  exit 2
fi
[ -x "$UE_EDITOR" ] || { echo "launch-editor: editor not executable: $UE_EDITOR" >&2; exit 2; }
[ -f "$UE_PROJECT" ] || { echo "launch-editor: project not found: $UE_PROJECT" >&2; exit 2; }

STAMP="$(date +%H%M%S)"
EDITOR_LOG="${EDITOR_LOG:-$(dirname "$UE_PROJECT")/Saved/editor-launch-$STAMP.log}"
mkdir -p "$(dirname "$EDITOR_LOG")" 2>/dev/null || EDITOR_LOG=/dev/null

# Own scope: without it the editor inherits the desktop app's 20 GB cap (AGENTS.md).
if [ "${LAUNCH_SCOPE_CMD:-}" = "none" ]; then
  SCOPE=()
elif [ -n "${LAUNCH_SCOPE_CMD:-}" ]; then
  read -r -a SCOPE <<<"$LAUNCH_SCOPE_CMD"
else
  SCOPE=(systemd-run --user --scope "--unit=megajam-job-$STAMP" -p MemoryHigh=26G -p MemoryMax=28G -p MemorySwapMax=8G --)
fi
CMD=("${SCOPE[@]}" "$UE_EDITOR" "$UE_PROJECT" -ModelContextProtocolStartServer "-ModelContextProtocolPort=$MCP_PORT" -nosplash)
# Owner rule 2026-11-12: the editor must never appear on the owner's screen. Default is no window at all;
# EDITOR_WINDOW=1 opts out (then keep it minimized and never focus it).
if [ "${EDITOR_WINDOW:-0}" != "1" ]; then CMD+=(-RenderOffScreen -unattended); fi

if [ "${DRYRUN:-0}" = "1" ]; then
  echo "launch-editor: engine $UE_EDITOR SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-(unset)}" >&2
  echo "${CMD[*]}"
  exit 0
fi

# Put the MCP helper (stages/02_build/references/editor-mcp-helper.md) next to the project, copied from THIS repo, never from a job
# tmp dir (those are lost on every handoff). The default folder is OUTSIDE the project: the project dir is a git
# repo that editor_watchdog snapshots with `git add -A`, which would commit the helper and its __pycache__
# into the entry's history. MX_DEST overrides the folder; MX_DEST=none skips the copy.
MX_DEST="${MX_DEST:-${XDG_STATE_HOME:-$HOME/.local/state}/megajam-mx}"
if [ "$MX_DEST" != "none" ]; then
  SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if mkdir -p "$MX_DEST" 2>/dev/null \
     && cp "$SRC_DIR/mx.py" "$SRC_DIR/mcp_call.py" "$SRC_DIR/step_shot.py" "$MX_DEST/" 2>/dev/null; then
    echo "launch-editor: helper copied to $MX_DEST/mx.py (python3 $MX_DEST/mx.py --help)" >&2
  else
    echo "launch-editor: WARNING could not copy mx.py to $MX_DEST; copy scripts/{mx,mcp_call,step_shot}.py by hand" >&2
  fi
fi

# Pid that owns the LISTEN socket (exact, via ss); empty if ss is missing or the owner is not ours.
socket_owner_pid() { ss -ltnpH "sport = :$MCP_PORT" 2>/dev/null | grep -o 'pid=[0-9]*' | head -n 1 | cut -d= -f2; }
# Running editor's pid on stdout: the socket owner, else an anchored match on the port argument.
print_running_pid() {
  local p; p="$(socket_owner_pid)"
  [ -n "$p" ] || p="$(pgrep -f -- "-ModelContextProtocolPort=$MCP_PORT( |\$)" | head -n 1)"
  [ -n "$p" ] && echo "$p"
  return 0
}

if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$MCP_PORT/mcp"; then
  echo "launch-editor: port $MCP_PORT already answers; an editor is running. Not launching a second." >&2
  # Print the running editor's PID (if findable) so a caller can adopt it instead of losing track.
  print_running_pid
  exit 3
fi

# Port held but not answering HTTP = an old hung editor (or any other process). Starting a second editor here
# would never bring MCP up and callers would wait forever (mock 12 lost three hours to this). Fail fast.
# "Held" = a LISTEN socket exists (ss, no connect, so a full accept queue cannot block us). Without ss, a connect
# bounded by `timeout 3` that fails by timeout also counts as held. A held port gets a longer HTTP probe first,
# so a healthy editor that is only busy (answers after more than 2 s) is not called hung. Never kills anything.
HELD_PROBE_TIMEOUT="${HELD_PROBE_TIMEOUT:-12}"
PORT_HELD=0
if command -v ss >/dev/null 2>&1; then
  [ -n "$(ss -ltnH "sport = :$MCP_PORT" 2>/dev/null)" ] && PORT_HELD=1
else
  timeout 3 bash -c "exec 3<>/dev/tcp/127.0.0.1/$MCP_PORT" 2>/dev/null
  RC=$?
  [ "$RC" -ne 1 ] && [ "$RC" -ne 127 ] && PORT_HELD=1  # 0 = connected, 124 = timed out; 1 = refused
fi
if [ "$PORT_HELD" = "1" ]; then
  echo "launch-editor: port $MCP_PORT is held; probing MCP for up to ${HELD_PROBE_TIMEOUT}s" >&2
  if curl -s -o /dev/null --max-time "$HELD_PROBE_TIMEOUT" "http://127.0.0.1:$MCP_PORT/mcp"; then
    echo "launch-editor: port $MCP_PORT answers (slowly); an editor is running and busy. Not launching a second." >&2
    print_running_pid  # callers (editor_watchdog launch()) adopt the editor from this line
    exit 3
  fi
  HOLDER="$(socket_owner_pid)"
  echo "launch-editor: port $MCP_PORT is held${HOLDER:+ by pid $HOLDER} and did not answer MCP within ${HELD_PROBE_TIMEOUT}s (hung or not an editor; check it before killing). Not launching." >&2
  exit 8
fi

# waitfor by absolute path; fail loudly (before starting anything) if it is missing.
WAITFOR="${WAITFOR_BIN:-$(command -v waitfor || true)}"
if [ -z "$WAITFOR" ] || [ ! -x "$WAITFOR" ]; then
  echo "launch-editor: waitfor not found (set WAITFOR_BIN=/abs/path/waitfor); not launching" >&2
  exit 6
fi

# GPU gate, ON by default: waits up to PREFLIGHT_WAIT (default 120 s) until gpu-preflight says clear.
# gpu-preflight not on PATH = skip with one line. PREFLIGHT_BIN=/abs/path overrides the binary (missing = exit 7).
# Opt out explicitly with LAUNCH_PREFLIGHT=0 or PREFLIGHT_BIN=none.
if [ "${LAUNCH_PREFLIGHT:-}" = "0" ] || [ "${PREFLIGHT_BIN:-}" = "none" ]; then
  echo "launch-editor: gpu-preflight skipped (LAUNCH_PREFLIGHT=0 or PREFLIGHT_BIN=none)" >&2
elif [ -z "${PREFLIGHT_BIN:-}" ] && ! command -v gpu-preflight >/dev/null 2>&1; then
  echo "launch-editor: gpu-preflight not on PATH; gate skipped" >&2
else
  PREFLIGHT_BIN="${PREFLIGHT_BIN:-$(command -v gpu-preflight)}"
  PREFLIGHT_WAIT="${PREFLIGHT_WAIT:-120}"
  if [ ! -x "$PREFLIGHT_BIN" ]; then
    echo "launch-editor: gpu-preflight not found (set PREFLIGHT_BIN=/abs/path, or none to skip); not launching" >&2
    exit 7
  fi
  echo "launch-editor: waiting up to ${PREFLIGHT_WAIT}s for gpu-preflight to clear" >&2
  if ! "$WAITFOR" --timeout "$PREFLIGHT_WAIT" --interval 5 -- "$PREFLIGHT_BIN" -q >&2; then
    echo "launch-editor: gpu-preflight did not clear in ${PREFLIGHT_WAIT}s; not launching ('gpu-preflight --who' names the holder)" >&2
    exit 7
  fi
fi

setsid "${CMD[@]}" >"$EDITOR_LOG" 2>&1 </dev/null &
PID=$!
echo "launch-editor: started pid $PID, log $EDITOR_LOG; waiting for MCP on :$MCP_PORT (up to ${WAIT_TIMEOUT}s, WAIT_TIMEOUT overrides)" >&2

# Wait for any HTTP answer (405 means up), but stop early if the editor died or logged a port-bind failure
# (a 5.9 editor started right after another one stopped can lose the bind race and never serves MCP).
BIND_ERR_RE="HttpListener unable to bind"
if "$WAITFOR" --timeout "$WAIT_TIMEOUT" --interval 2 -- bash -c \
  'kill -0 "$1" 2>/dev/null || exit 0; grep -q -- "$3" "$2" 2>/dev/null && exit 0; curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$4/mcp"' \
  _ "$PID" "$EDITOR_LOG" "$BIND_ERR_RE" "$MCP_PORT" >&2; then
  :
fi
if grep -q -- "$BIND_ERR_RE" "$EDITOR_LOG" 2>/dev/null && ! curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$MCP_PORT/mcp"; then
  echo "launch-editor: editor logged '$BIND_ERR_RE' on :$MCP_PORT (the old editor was still closing); stopping pid $PID. Wait a few seconds and relaunch. Log: $EDITOR_LOG" >&2
  kill "$PID" 2>/dev/null
  exit 9
fi
if ! kill -0 "$PID" 2>/dev/null; then
  echo "launch-editor: editor exited before the MCP port came up; see $EDITOR_LOG" >&2
  exit 4
fi
if ! curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$MCP_PORT/mcp"; then
  echo "launch-editor: timed out waiting for :$MCP_PORT; editor still running as $PID" >&2
  echo "$PID"  # still print it: the editor is alive and callers must keep tracking it
  exit 5
fi
echo "$PID"

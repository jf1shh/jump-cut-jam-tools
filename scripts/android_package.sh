#!/usr/bin/env bash
# android_package.sh - UAT BuildCookRun for Android (ASTC), logged, timed.
#
#   scripts/android_package.sh PROJECT.uproject [--config Shipping|Development]
#                              [--ue-root DIR] [--out DIR] [--sdk DIR]
#
# Refuses (exit 4) while a `claude-loop -n megajam-mock` session runs, unless ANDROID_ALLOW_MOCK_LOOP=1
# (set only by the mock session itself). Always refuses while an UnrealEditor process runs or
# `gpu-preflight -q` is not clear; pgrep failures count as "running". Needs a JDK 21 with javac
# (JAVA_HOME is set to it for the run). Logs to ~/.local/state/megajam/android/
# (override with MEGAJAM_ANDROID_STATE). ANDROID_HOME is exported for this run only.
# Prints APK path, size and wall time on success. Rule 7(h): run it only against a mock project.
set -u

PROJECT=""
CONFIG="Development"
UE_ROOT="${MEGAJAM_UE_ROOT:-}"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
OUT=""
STATE="${MEGAJAM_ANDROID_STATE:-$HOME/.local/state/megajam/android}"

while [ $# -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --ue-root) UE_ROOT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --sdk) SDK="$2"; shift 2 ;;
    -h|--help) sed -n 2,10p "$0"; exit 0 ;;
    -*) echo "unknown argument: $1" >&2; exit 2 ;;
    *) PROJECT="$1"; shift ;;
  esac
done

case "$CONFIG" in Shipping|Development) ;; *) echo "--config must be Shipping or Development" >&2; exit 2 ;; esac
[ -n "$PROJECT" ] && [ -f "$PROJECT" ] || { echo "usage: android_package.sh PROJECT.uproject (file not found: '${PROJECT}')" >&2; exit 2; }
[ -n "$UE_ROOT" ] || { echo "UE root needed: --ue-root DIR or MEGAJAM_UE_ROOT" >&2; exit 2; }
UAT="$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh"
[ -x "$UAT" ] || { echo "RunUAT.sh not found/executable: $UAT" >&2; exit 2; }

# pgrep gates fail CLOSED: only exit 1 ("no match") means clear; 0 = running, 2/3/127 = cannot tell.
pgrep_clear() {
  pgrep -f "$1" >/dev/null 2>&1
  [ "$?" -eq 1 ]
}
# Gate 0: the mock loop owns the editor. Refused by default (any -n/--name/= form); only the mock
# session itself sets ANDROID_ALLOW_MOCK_LOOP=1 when it runs this step from inside the loop.
if [ "${ANDROID_ALLOW_MOCK_LOOP:-0}" != "1" ]; then
  if ! pgrep_clear 'claude[-_]loop.*(-n|--name)[ =]megajam-mock($| )'; then
    echo "REFUSED: a 'claude-loop -n megajam-mock' session is running (or pgrep failed); the mock owns the editor. Set ANDROID_ALLOW_MOCK_LOOP=1 only from inside that mock session." >&2
    exit 4
  fi
fi
# Gate 1: the editor holds the GPU and the MCP port; a cook beside it fails. Stays on in both cases.
if ! pgrep_clear 'UnrealEditor'; then
  echo "REFUSED: an UnrealEditor process is running (or pgrep failed). Close the editor first." >&2
  exit 4
fi
# Gate 2: GPU preflight.
if ! gpu-preflight -q; then
  echo "REFUSED: gpu-preflight is not clear. Run 'gpu-preflight --who' and free the GPU first." >&2
  exit 4
fi

# JDK 21 with a real javac, exported as JAVA_HOME for this run (the system default is JDK 17).
JDK_HOME=""
for d in "${JAVA_HOME:-}" "${MEGAJAM_JVM_DIR:-/usr/lib/jvm}"/*; do
  [ -n "$d" ] && [ -x "$d/bin/javac" ] || continue
  case "$(basename "$d")" in
    *"-21-"*|*"-21"|*"jdk21"*|*"jdk-21"*) JDK_HOME="$d"; break ;;
  esac
done
if [ -z "$JDK_HOME" ]; then
  echo "REFUSED: no JDK 21 with bin/javac found (jre-only dirs do not count). Run scripts/android_toolchain_check.sh." >&2
  exit 2
fi
export JAVA_HOME="$JDK_HOME"

PROJECT="$(cd "$(dirname "$PROJECT")" && pwd)/$(basename "$PROJECT")"
mkdir -p "$STATE" || exit 1
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$STATE/package-$STAMP.log"
[ -n "$OUT" ] || OUT="$STATE/out-$STAMP"
mkdir -p "$OUT" || exit 1

export ANDROID_HOME="$SDK" ANDROID_SDK_ROOT="$SDK"
echo "start $(date -u +%FT%TZ)  config=$CONFIG  log=$LOG"
START=$(date +%s)
# Snapshot existing APKs (path + mtime); only a new or rewritten APK counts as this run's output.
BEFORE="$STATE/.apks-before-$STAMP"
find "$OUT" -name '*.apk' -type f -printf '%p %T@\n' 2>/dev/null | sort >"$BEFORE"
"$UAT" BuildCookRun -project="$PROJECT" -platform=Android -clientconfig="$CONFIG" \
  -cookflavor=ASTC -build -cook -stage -pak -package -archive -archivedirectory="$OUT" \
  -noP4 -utf8output -unattended >"$LOG" 2>&1
RC=$?
WALL=$(( $(date +%s) - START ))

if [ "$RC" -ne 0 ]; then
  echo "FAILED: UAT exit $RC after ${WALL}s. Last lines of $LOG:" >&2
  tail -n 15 "$LOG" >&2
  exit "$RC"
fi
APK="$(find "$OUT" -name '*.apk' -type f -printf '%p %T@\n' 2>/dev/null | sort | comm -13 "$BEFORE" - | head -n 1 | sed 's/ [0-9.]*$//')"
rm -f "$BEFORE"
if [ -z "$APK" ]; then
  echo "FAILED: UAT exit 0 but no .apk under $OUT (see $LOG)" >&2
  exit 5
fi
SIZE="$(stat -c %s "$APK")"
echo "APK: $APK"
echo "SIZE: $SIZE bytes"
echo "WALL: ${WALL}s"
echo "LOG: $LOG"

#!/usr/bin/env bash
# android_install.sh - install an APK on the owner's Galaxy S24 over adb (Tailscale), launch, screenshot.
#
#   scripts/android_install.sh APK --addr IP:PORT [--package NAME] [--wait SECS] [--out DIR] [--dry-run]
#
# The wireless-debugging connect port rotates; read it on the phone (Wireless debugging screen) and pass
# it as --addr (or PHONE_ADB_ADDR). Phone Tailscale IP is usually <lan-host> (check `tailscale status`).
# If adb says "failed to connect", pair first (see ~/.claude/memory/reference-android-phone-access.md).
# Prints the pulled screenshot path on the last line so the agent can Read it.
# --dry-run prints the adb command lines and runs nothing.
set -u

APK=""
ADDR="${PHONE_ADB_ADDR:-}"
PKG="${MEGAJAM_ANDROID_PACKAGE:-com.silentblade.megajammock}"
WAIT=15
OUT="${MEGAJAM_ANDROID_STATE:-$HOME/.local/state/megajam/android}/shots"
DRY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --addr) ADDR="$2"; shift 2 ;;
    --package) PKG="$2"; shift 2 ;;
    --wait) WAIT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n 2,11p "$0"; exit 0 ;;
    -*) echo "unknown argument: $1" >&2; exit 2 ;;
    *) APK="$1"; shift ;;
  esac
done

[ -n "$APK" ] || { echo "usage: android_install.sh APK --addr IP:PORT" >&2; exit 2; }
[ -n "$ADDR" ] || { echo "need --addr IP:PORT (connect port from the phone's Wireless debugging screen) or PHONE_ADB_ADDR" >&2; exit 2; }
[ "$DRY" -eq 1 ] || [ -f "$APK" ] || { echo "APK not found: $APK" >&2; exit 2; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REMOTE="/sdcard/megajam_shot_$STAMP.png"
LOCAL="$OUT/shot-$STAMP.png"

run() {
  if [ "$DRY" -eq 1 ]; then echo "adb $*"; return 0; fi
  adb "$@"
}

mkdir -p "$OUT" 2>/dev/null
run connect "$ADDR" || exit 1
run -s "$ADDR" install -r "$APK" || { echo "install failed" >&2; exit 1; }
run -s "$ADDR" shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 || { echo "launch failed" >&2; exit 1; }
[ "$DRY" -eq 1 ] || sleep "$WAIT"
run -s "$ADDR" shell screencap -p "$REMOTE" || exit 1
run -s "$ADDR" pull "$REMOTE" "$LOCAL" || exit 1
run -s "$ADDR" shell rm "$REMOTE" || true
echo "$LOCAL"

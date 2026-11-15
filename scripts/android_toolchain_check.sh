#!/usr/bin/env bash
# android_toolchain_check.sh - what is installed vs what UE 5.8 wants for Android.
#
#   scripts/android_toolchain_check.sh [--sdk DIR] [--ue-root DIR] [--jvm-dir DIR] [--install]
#
# Exit 0 only when every item is present. Without --install nothing is changed.
# --install only runs `sdkmanager` for missing SDK pieces, and only when the SDK dir is under $HOME
# (default ~/Android/Sdk). It never touches system packages and never edits shell rc files; a missing
# JDK is reported with the command for the owner to run.
#
# Required versions come from _config/reference/knowledge-base.md (5.8 notes) and can be overridden:
#   REQ_NDK REQ_PLATFORM REQ_BUILD_TOOLS REQ_JDK_MAJOR
# The engine's own Engine/Extras/Android/SetupAndroid.sh is the final authority on the pins.
set -u

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
UE_ROOT="${MEGAJAM_UE_ROOT:-}"
JVM_DIR="/usr/lib/jvm"
DO_INSTALL=0
REQ_NDK="${REQ_NDK:-27.2.12479018}"            # NDK r27c
REQ_PLATFORM="${REQ_PLATFORM:-35}"             # SDK platform android-35 (min 34 to compile UE)
REQ_BUILD_TOOLS="${REQ_BUILD_TOOLS:-35.0.1}"
REQ_JDK_MAJOR="${REQ_JDK_MAJOR:-21}"

while [ $# -gt 0 ]; do
  case "$1" in
    --sdk) SDK="$2"; shift 2 ;;
    --ue-root) UE_ROOT="$2"; shift 2 ;;
    --jvm-dir) JVM_DIR="$2"; shift 2 ;;
    --install) DO_INSTALL=1; shift ;;
    -h|--help) sed -n 2,14p "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

missing=0
missing_sdk_pkgs=()

report() {  # status label have want
  printf '%-8s %-14s have: %-40s want: %s\n' "$1" "$2" "$3" "$4"
}
ls_names() { [ -d "$1" ] && (cd "$1" && ls -1 2>/dev/null | tr '\n' ' ') ; }

# SDK platform
have="$(ls_names "$SDK/platforms")"
if [ -d "$SDK/platforms/android-$REQ_PLATFORM" ]; then report OK platform "${have:-none}" "android-$REQ_PLATFORM"
else report MISSING platform "${have:-none}" "android-$REQ_PLATFORM"; missing=1; missing_sdk_pkgs+=("platforms;android-$REQ_PLATFORM"); fi

# build-tools
have="$(ls_names "$SDK/build-tools")"
if [ -d "$SDK/build-tools/$REQ_BUILD_TOOLS" ]; then report OK build-tools "${have:-none}" "$REQ_BUILD_TOOLS"
else report MISSING build-tools "${have:-none}" "$REQ_BUILD_TOOLS"; missing=1; missing_sdk_pkgs+=("build-tools;$REQ_BUILD_TOOLS"); fi

# NDK
have="$(ls_names "$SDK/ndk")"
if [ -d "$SDK/ndk/$REQ_NDK" ]; then report OK ndk "${have:-none}" "$REQ_NDK"
else report MISSING ndk "${have:-none}" "$REQ_NDK"; missing=1; missing_sdk_pkgs+=("ndk;$REQ_NDK"); fi

# platform-tools (adb)
if [ -x "$SDK/platform-tools/adb" ]; then report OK platform-tools "$SDK/platform-tools/adb" "adb"
elif command -v adb >/dev/null 2>&1; then report OK platform-tools "$(command -v adb) (PATH)" "adb"
else report MISSING platform-tools none "adb"; missing=1; missing_sdk_pkgs+=("platform-tools"); fi

# JDK: any dir under JVM_DIR (or $JAVA_HOME) whose name carries the wanted major version
jdk=""
for d in "${JAVA_HOME:-}" "$JVM_DIR"/*; do
  [ -n "$d" ] && [ -d "$d" ] && [ -x "$d/bin/javac" ] || continue   # a JRE-only dir is not a JDK
  case "$(basename "$d")" in
    *"-$REQ_JDK_MAJOR-"*|*"-$REQ_JDK_MAJOR"|*"jdk$REQ_JDK_MAJOR"*|*"jdk-$REQ_JDK_MAJOR"*) jdk="$d"; break ;;
  esac
done
have="$(ls_names "$JVM_DIR")"
if [ -n "$jdk" ]; then report OK jdk "$jdk" "OpenJDK $REQ_JDK_MAJOR"
else report MISSING jdk "${have:-none}" "OpenJDK $REQ_JDK_MAJOR"; missing=1; fi

# UE 5.8 Android setup script
setup=""
[ -n "$UE_ROOT" ] && setup="$UE_ROOT/Engine/Extras/Android/SetupAndroid.sh"
if [ -n "$setup" ] && [ -f "$setup" ]; then report OK ue-setup "$setup" "SetupAndroid.sh"
elif [ -z "$UE_ROOT" ]; then report MISSING ue-setup "UE root not given (--ue-root or MEGAJAM_UE_ROOT)" "SetupAndroid.sh"; missing=1
else report MISSING ue-setup "$setup not found" "SetupAndroid.sh"; missing=1; fi

echo
echo "SDK dir: $SDK   (export ANDROID_HOME=$SDK for the UE run only; shell rc is never edited)"

if [ "$missing" -eq 0 ]; then echo "RESULT: all present"; exit 0; fi

echo "RESULT: something is missing"
if [ "${#missing_sdk_pkgs[@]}" -gt 0 ]; then
  sm="$SDK/cmdline-tools/latest/bin/sdkmanager"
  echo "Proposed SDK install (no changes made without --install):"
  echo "  $sm --sdk_root=$SDK ${missing_sdk_pkgs[*]}"
fi
[ -z "$jdk" ] && echo "JDK $REQ_JDK_MAJOR is a system package; owner runs: sudo pacman -S jdk${REQ_JDK_MAJOR}-openjdk"
[ -n "$setup" ] && echo "UE's own installer (alternative): ANDROID_HOME=$SDK $setup"

if [ "$DO_INSTALL" -eq 1 ]; then
  case "$SDK" in
    "$HOME"/*) ;;
    *) echo "refusing --install: SDK dir $SDK is not under \$HOME" >&2; exit 3 ;;
  esac
  if [ "${#missing_sdk_pkgs[@]}" -gt 0 ]; then
    sm="$SDK/cmdline-tools/latest/bin/sdkmanager"
    [ -x "$sm" ] || { echo "sdkmanager not found at $sm" >&2; exit 3; }
    "$sm" --sdk_root="$SDK" "${missing_sdk_pkgs[@]}" || exit 3
  fi
  echo "Install step done. Re-run without --install to confirm."
fi
exit 1

#!/usr/bin/env python3
"""Visual playtest gate: play the PACKAGED build with real OS input, capture frames, write a checklist.

Why (owner, 2026-11-08, T-20261108-05): mock jam 10 shipped a build that was "not a playable game at
all" (grey grid floor, placeholder primitives, PrintString debug text, water going negative). Its
"plays to win" gate was a PIE log grep with the game's own autopilot. The agent must look at the game.

Subcommands:
  run      launch the packaged build, send a scripted sequence of REAL input, grab frames, analyse, and
           write <out>/checklist.md (+ results.json). Targets: --target legion (default) or local.
  analyze  redo the cheap automated checks on an existing <out> folder (frames + manifest.json).
  verify   exit 0 only if every checklist item AND every step has a PASS verdict (blank, AGENT, WARN,
           PENDING or FAIL do not pass). The agent sets them after READING the contact sheets.
  gate     what the ship/findings step calls: verify, plus a gate.ok receipt on PASS. Non-zero = not done.

Real input, never the game's autopilot:
  <device-host>: scripts/visual_playtest_input.ps1 runs in a console-session scheduled task (Interactive
          logon, the only way to reach the real display) and calls user32 SendInput with scan codes.
  local:  xdotool + ffmpeg x11grab (X11 / XWayland only). Not exercised in CI.

The automated checks are cheap and only advisory (frame differences, flat/black frames, mostly-grey
frames, debug-text colour pixels, optional OCR). The agent judges the frames and records the verdict.

EXAMPLES:
    ./scripts/visual_playtest.py run --remote-zip 'C:\\Dev\\Game\\Packaged\\Game.zip' --game-name Game --out /tmp/vp10
    ./scripts/visual_playtest.py run --target local --local-cmd ./Game/Binaries/Linux/Game --out /tmp/vp10
    ./scripts/visual_playtest.py verify /tmp/vp10
Sequence file (--sequence): JSON array of steps, see DEFAULT_SEQUENCE and visual_playtest_input.ps1.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_HOST = "device-host"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3"]
INPUT_PS1 = "visual_playtest_input.ps1"
REMOTE_SCRATCH = "C:/Dev/.legion_playtest_scratch"
REMOTE_OUT = f"{REMOTE_SCRATCH}/vp"
REMOTE_STEPS = f"{REMOTE_SCRATCH}/vp_steps.json"
INPUT_TASK = "MJToolVisualPlaytest"

# Tunables for the cheap checks (mean absolute difference of 64x36 gray thumbnails, 0..255).
MOVE_DIFF_MIN = 2.0       # input must change the picture at least this much
IDLE_FACTOR = 1.5         # ... and at least this many times the idle (no input) change
RESTART_DIFF_MAX = 12.0   # restarted frame should look like the first frame
FLAT_SD_MAX = 3.0         # a frame whose pixel spread is below this is black / one colour
GREY_FRACTION_WARN = 0.90  # share of low-saturation pixels that makes a frame "mostly grey"
DEBUG_PIXELS_WARN = 40    # debug-colour pixels in the top-left region before we warn
# Idle bursts: N frames over a few seconds with NO input. Differences are mean absolute grey-level change
# (0-255) between 64x36 thumbnails. The looping OUT OF WATER build of 2026-11-08 (camera falls to the
# floor, snaps back wide, repeats) measured 15-20 per step; a calm scene is under 1; ambient water or
# particles stay under ~3.
BURST_MIN_FRAMES = 10
BURST_DEFAULT_FRAMES = 12
BURST_DEFAULT_SECONDS = 3.0
BURST_SPACING_SLACK = 1.25  # captured spacing may exceed the cap by this factor (jitter) before the burst is refused
BURST_MAX_SPACING = 0.3  # seconds between burst frames, so a ~1 s camera loop shows several phases
IDLE_STEP_WARN = 1.5      # mean frame-to-frame change above this: WARN (something animates)
IDLE_STEP_MAX = 4.0       # mean frame-to-frame change above this: FAIL (loop, falling camera, flicker)
IDLE_JUMP_MAX = 12.0      # any single step above this: FAIL (a snap-back / respawn cut)
IDLE_DRIFT_MAX = 15.0     # last frame vs first frame above this: FAIL (the view slid away with no input)
SHEET_COLS = 5
SHEET_TILE = (320, 180)
STEP_SHEET_FRAMES = 8     # still frames per step contact sheet (4 columns x 2 rows): 15 frames = 2 image reads
STEP_SHEET_COLS = 4
LABEL_H = 18              # label strip above each tile of a step sheet (5x7 font at 2x + padding)
SEVERITY = {"PASS": 0, "AGENT": 1, "WARN": 2, "FAIL": 3}  # worst wins when a frame is in several items
DEBUG_WORDS = re.compile(r"PrintString|Hello|DEBUG|LogBlueprint|Accessed None|Blueprint Runtime|Warning:|Error:|TODO|String:", re.I)

# Generic sequence: keys are WASD + space + mouse, restart on R. Override with --sequence for a game
# that uses other keys. Shots right after an input step are compared against the shot before it.
DEFAULT_SEQUENCE = [
    {"op": "declare", "end_states": ["lose"]},   # the end screens this game has: "lose", "win" or both
    {"op": "wait", "seconds": 8},
    {"op": "shot", "label": "start"},
    {"op": "wait", "seconds": 3},
    {"op": "shot", "label": "idle"},
    {"op": "burst", "label": "midplay", "seconds": 3, "frames": 12},
    {"op": "key", "key": "w", "hold": 1.5},
    {"op": "shot", "label": "after_w"},
    {"op": "key", "key": "d", "hold": 1.0},
    {"op": "shot", "label": "after_d"},
    {"op": "key", "key": "space", "hold": 0.2},
    {"op": "shot", "label": "after_space"},
    {"op": "click", "button": "left"},
    {"op": "shot", "label": "after_click"},
    {"op": "move", "dx": 400, "dy": 0},
    {"op": "shot", "label": "after_look"},
    {"op": "wait", "seconds": 25},
    {"op": "shot", "label": "late"},
    # The burst is the last capture before the restart key: whatever end screen the game is on must sit still.
    # A game with both a lose and a win screen: declare both and burst in each, in your own --sequence.
    {"op": "burst", "label": "lose", "end_state": "lose", "seconds": 3, "frames": 12},
    {"op": "key", "key": "r", "hold": 0.2},
    {"op": "wait", "seconds": 4},
    {"op": "shot", "label": "restarted"},
    {"op": "burst", "label": "afterrestart", "seconds": 3, "frames": 12},
]

VALID_OPS = {"wait", "shot", "key", "click", "move", "burst", "declare"}


def step_keys(step):
    """Key names of a key step: {"key": "d"} -> ["d"]; {"keys": ["space", "d"]} -> held together."""
    return list(step["keys"]) if "keys" in step else [step["key"]]
END_STATES = ("lose", "win")
LABEL_RE = re.compile(r"[A-Za-z0-9-]+")  # burst labels: no "_" so file names split cleanly


def burst_params(s):
    """(frames, seconds) of a burst step, defaults filled in."""
    return int(s.get("frames", BURST_DEFAULT_FRAMES)), float(s.get("seconds", BURST_DEFAULT_SECONDS))


def _build_keys():
    """name -> (windows scan code, extended?, X keysym). The ONE list: validate_sequence and the local
    backend read it, and a test checks that $ScanCodes in visual_playtest_input.ps1 is identical."""
    keys = {}
    for row, base in (("qwertyuiop", 0x10), ("asdfghjkl", 0x1E), ("zxcvbnm", 0x2C)):
        for i, ch in enumerate(row):
            keys[ch] = (base + i, False, ch)
    for i, ch in enumerate("1234567890"):
        keys[ch] = (0x02 + i, False, ch)
    keys.update({"esc": (0x01, False, "Escape"), "tab": (0x0F, False, "Tab"), "enter": (0x1C, False, "Return"),
                 "space": (0x39, False, "space"), "shift": (0x2A, False, "Shift_L"), "ctrl": (0x1D, False, "Control_L"),
                 "up": (0x48, True, "Up"), "left": (0x4B, True, "Left"),
                 "right": (0x4D, True, "Right"), "down": (0x50, True, "Down")})
    return keys


KEYS = _build_keys()
BARE_ALT_NAMES = ("alt", "lalt", "ralt", "alt_l", "alt_r", "menu")  # never sent (mock jam 11, gap 16)
WARMUP_DEFAULT = 30       # a cold first start of a packaged game outlasts 10 s (mock jam 11, gap 15)
WARMUP_MAX = 90           # upper limit while the probe shot is still black
PROBE_INTERVAL = 10       # seconds between probe shots while the game is still black
PROBE_COST_EST = 15       # a probe shot takes about this long (ssh + scp + polling); counted toward WARMUP_MAX


def _sibling(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MSG_LOCKED = _sibling("legion_preflight").MSG_LOCKED


def legion_probe(host):
    """Real probe for LegionBackend: LogonUI check plus one screenshot, judged by distinct colours."""
    pre, cap = _sibling("legion_preflight"), _sibling("legion_capture_screenshot")
    return pre.probe_message(host, lambda: cap.take_probe(host))


def log(msg):
    print(msg, file=sys.stderr)


# ---------- sequence ----------

def check_burst_placement(steps):
    """The end states are where mock 10 looped, so a sequence must sample them: a restart shot (label with
    'restart'), a burst after the last play input (the lose/win state, before the restart key) and a burst
    after the restart. Raises ValueError with what is missing."""
    decl = [s for s in steps if s["op"] == "declare"]
    if len(decl) != 1:
        raise ValueError('sequence must declare its end states once: {"op":"declare","end_states":["lose","win"]} '
                         "(\"lose\", \"win\" or both, whichever the game has)")
    states = decl[0].get("end_states")
    if (not isinstance(states, list) or not states or any(not isinstance(s, str) for s in states)
            or len(set(states)) != len(states) or any(s not in END_STATES for s in states)):
        raise ValueError(f"declare.end_states must be a non-empty list without repeats of {list(END_STATES)}")
    for i, s in enumerate(steps):
        if s["op"] == "burst" and s.get("end_state") not in (None, *END_STATES):
            raise ValueError(f"step {i}: burst end_state must be one of {list(END_STATES)}")
        # the end screen can change while you wait, so an end-state burst must be followed straight by an input
        if s["op"] == "burst" and s.get("end_state") and not (
                i + 1 < len(steps) and steps[i + 1]["op"] in ("key", "click", "move")):
            raise ValueError(f"step {i}: the '{s['end_state']}' end-state burst must be immediately followed by an "
                             "input step (no wait or shot in between), so it samples the end state itself")
    for st in states:
        if not any(s["op"] == "burst" and s.get("end_state") == st for s in steps):
            raise ValueError(f"declared end state '{st}' has no burst; add {{\"op\":\"burst\",\"label\":\"{st}\","
                             f"\"end_state\":\"{st}\"}} right before the input that leaves it")
    rest = [i for i, s in enumerate(steps) if s["op"] == "shot" and is_restart_label(s["label"])]
    if not rest:
        raise ValueError("sequence needs a shot labelled 'restarted' after the restart key; the end-state and "
                         "after-restart idle bursts are measured around it")
    r = rest[-1]
    keys = [i for i in range(r) if steps[i]["op"] in ("key", "click", "move")]
    if not keys:
        raise ValueError("sequence needs the restart key (an input step) before the 'restarted' shot")
    k = keys[-1]                                      # the restart input
    stray = [i for i in range(k + 1, r) if steps[i]["op"] in ("shot", "burst")]
    if stray:
        raise ValueError(f"step {stray[0]}: no shot or burst between the restart key and the 'restarted' shot "
                         "(only waits), so the capture right before the restart is the end-state burst")
    if k == 0 or steps[k - 1]["op"] != "burst" or not steps[k - 1].get("end_state"):
        raise ValueError("the last capture before the restart key must be an end-state burst (nothing but the "
                         "restart key after it; no wait, no shot), so the lose/win state itself is sampled")
    if not any(steps[i]["op"] == "burst" for i in range(r + 1, len(steps))):
        raise ValueError("sequence needs a burst after the 'restarted' shot, so the restarted game is sampled")


def validate_steps(steps):
    """Per-step checks only (ops, key names, labels, burst sizes). validate_sequence adds the gate's
    whole-sequence rules; legion_record --sequence uses just this part."""
    if not isinstance(steps, list) or not steps:
        raise ValueError("sequence must be a non-empty JSON array")
    for i, s in enumerate(steps):
        if not isinstance(s, dict) or s.get("op") not in VALID_OPS:
            raise ValueError(f"step {i}: op must be one of {sorted(VALID_OPS)}")
        if s["op"] == "shot" and not re.fullmatch(r"[A-Za-z0-9_-]+", str(s.get("label", ""))):
            raise ValueError(f"step {i}: shot needs a label made of letters, digits, _ or -")
        if s["op"] == "key" and ("keys" in s) == ("key" in s):
            raise ValueError(f'step {i}: a key step needs exactly one of "key": NAME or "keys": [NAME, ...] '
                             "(keys are held together, e.g. steer while holding space)")
        if s["op"] == "key" and "keys" in s and (not isinstance(s["keys"], list) or not s["keys"]
                                                 or len(set(map(str, s["keys"]))) != len(s["keys"])):
            raise ValueError(f'step {i}: "keys" must be a non-empty list of different key names')
        for name in (step_keys(s) if s["op"] == "key" else ()):
            if str(name).lower() in BARE_ALT_NAMES:
                raise ValueError(f"step {i}: a bare Alt tap is refused: on the Legion it opens the AMD overlay and "
                                 "covers the frames. Use another key (ctrl, shift, space...).")
            if name not in KEYS:
                raise ValueError(f"step {i}: unknown key {name!r}; use one of {' '.join(sorted(KEYS))}")
        if s["op"] == "burst":
            if not LABEL_RE.fullmatch(str(s.get("label", ""))):
                raise ValueError(f"step {i}: burst needs a label made of letters, digits or - (no _)")
            try:
                frames, seconds = burst_params(s)
            except (TypeError, ValueError):
                raise ValueError(f"step {i}: burst frames and seconds must be numbers") from None
            if not BURST_MIN_FRAMES <= frames <= 60:
                raise ValueError(f"step {i}: burst frames must be {BURST_MIN_FRAMES}..60, got {frames}")
            if not 1.0 <= seconds <= 30.0:
                raise ValueError(f"step {i}: burst seconds must be 1..30, got {seconds}")
            # Frames spaced about as far apart as a camera loop's period land on the same phase of the loop
            # and look identical (aliasing), so the spacing is capped.
            if seconds / frames > BURST_MAX_SPACING + 1e-9:
                raise ValueError(f"step {i}: burst frames are {seconds / frames:.2f} s apart; must be <= "
                                 f"{BURST_MAX_SPACING} s (e.g. 12 frames over 3 s) so a ~1 s loop cannot hide")
    return steps


def validate_sequence(steps):
    validate_steps(steps)
    labels = [s["label"] for s in steps if s["op"] == "burst"]
    if len(labels) != len(set(labels)):
        raise ValueError("burst labels must be unique")
    check_burst_placement(steps)
    if not any(s["op"] == "shot" for s in steps):
        raise ValueError("sequence has no shot step")
    if not any(s["op"] in ("key", "click", "move") for s in steps):
        raise ValueError("sequence sends no input; the gate needs real input")
    return steps


def sequence_seconds(steps):
    t = 0.0
    for s in steps:
        if s["op"] == "burst":
            frames, seconds = burst_params(s)
            t += seconds + 0.5 * frames  # the sleeps plus a generous per-frame capture cost
        elif s["op"] == "declare":
            pass
        else:
            t += float(s.get("seconds", 0)) if s["op"] == "wait" else float(s.get("hold", 0.1)) if s["op"] == "key" else 0.3
    return t


def normalize_manifest(data):
    """PowerShell's ConvertTo-Json turns a 0/1-item list into '' / a bare object."""
    if not data:
        return []
    if isinstance(data, dict):
        return [data]
    return list(data)


# ---------- PNG reading (no Pillow, no ffmpeg needed for analysis) ----------

def read_png(path):
    """Return (width, height, rgb_bytes). 8-bit, non-interlaced gray / RGB / RGBA only."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, w = 8, [], None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace != 0 or ctype not in (0, 2, 6):
                raise ValueError(f"{path}: unsupported PNG (depth {depth}, type {ctype}, interlace {interlace})")
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if w is None:
        raise ValueError(f"{path}: no IHDR")
    bpp = {0: 1, 2: 3, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    if len(raw) < h * (stride + 1):
        raise ValueError(f"{path}: truncated image data")
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif f != 0:
            raise ValueError(f"{path}: bad PNG filter {f}")
        prev = line
        if bpp == 3:
            out += line
        elif bpp == 4:
            out += b"".join(bytes(line[i:i + 3]) for i in range(0, stride, 4))
        else:
            out += b"".join(bytes((v, v, v)) for v in line)
    return w, h, bytes(out)


def write_png(path, w, h, rgb):
    """Tiny RGB writer (tests build synthetic frames with it)."""
    rows = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def thumb_gray(img, tw=64, th=36, sub=4):
    """Box-sampled gray thumbnail (list of tw*th floats)."""
    w, h, rgb = img
    out = []
    for ty in range(th):
        for tx in range(tw):
            tot = 0
            for sy in range(sub):
                y = min(h - 1, (ty * h + (sy * 2 + 1) * h // (sub * 2)) // th)
                for sx in range(sub):
                    x = min(w - 1, (tx * w + (sx * 2 + 1) * w // (sub * 2)) // tw)
                    i = (y * w + x) * 3
                    tot += (rgb[i] * 299 + rgb[i + 1] * 587 + rgb[i + 2] * 114) // 1000
            out.append(tot / (sub * sub))
    return out


def scale_rgb(img, tw, th):
    """Nearest-sample downscale to tw x th (contact-sheet tiles). Returns RGB bytes."""
    w, h, rgb = img
    out = bytearray()
    for ty in range(th):
        row = min(h - 1, (ty * h + h // 2) // th) * w
        for tx in range(tw):
            i = (row + min(w - 1, (tx * w + w // 2) // tw)) * 3
            out += rgb[i:i + 3]
    return bytes(out)


# 5x7 pixel font for the step labels (upper case, digits, a few marks). Rows are top to bottom.
_FONT_SRC = {
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "-": "00000 00000 00000 11111 00000 00000 00000", ".": "00000 00000 00000 00000 00000 00000 00100",
    ":": "00000 00100 00000 00000 00100 00000 00000", "=": "00000 00000 11111 00000 11111 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
}
FONT = {c: v.split() for c, v in _FONT_SRC.items()}


def draw_text(canvas, cw, x0, y0, text, xmax, scale=2, rgb=b"\xff\xff\xff"):
    """Stamp text onto an RGB bytearray canvas (row width cw). Unknown characters are blank; clipped at xmax."""
    x = x0
    for ch in text.upper():
        rows = FONT.get(ch)
        if rows and x + 5 * scale <= xmax:
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "1":
                        for dy in range(scale):
                            o = ((y0 + ry * scale + dy) * cw + x + rx * scale) * 3
                            for dx in range(scale):
                                canvas[o + dx * 3:o + dx * 3 + 3] = rgb
        x += 6 * scale


def write_contact_sheet(tiles, path, cols=SHEET_COLS, tile=SHEET_TILE, gap=4, labels=None):
    """Lay RGB tiles (each tile[0] x tile[1]) out row-major (left to right, then down) on a dark-magenta grid.
    labels: optional text per tile, drawn in a strip above it (step number and time on step sheets)."""
    tw, th = tile
    lh = LABEL_H if labels else 0
    rows = (len(tiles) + cols - 1) // cols
    sw, sh = cols * (tw + gap) + gap, rows * (th + lh + gap) + gap
    canvas = bytearray(b"\x30\x00\x30" * (sw * sh))  # the gap colour is unmistakably not game content
    for n, t in enumerate(tiles):
        x0, y0 = gap + (n % cols) * (tw + gap), gap + (n // cols) * (th + lh + gap)
        if lh:
            for y in range(lh):
                o = ((y0 + y) * sw + x0) * 3
                canvas[o:o + tw * 3] = b"\x10\x10\x10" * tw
            draw_text(canvas, sw, x0 + 4, y0 + 2, labels[n] if n < len(labels) else "", x0 + tw)
        for y in range(th):
            o = ((y0 + lh + y) * sw + x0) * 3
            canvas[o:o + tw * 3] = t[y * tw * 3:(y + 1) * tw * 3]
    write_png(path, sw, sh, bytes(canvas))


def sheet_name(label):
    return f"contact_{label}.png"


def mean_sd(vals):
    m = sum(vals) / len(vals)
    return m, (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5


def mean_abs_diff(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def grey_fraction(img, step=8):
    """Share of sampled pixels with low colour saturation (max-min channel spread < 20)."""
    w, h, rgb = img
    grey = tot = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            i = (y * w + x) * 3
            r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
            tot += 1
            if max(r, g, b) - min(r, g, b) < 20:
                grey += 1
    return grey / tot if tot else 0.0


def debug_colour_pixels(img):
    """Count pixels in the top-left area that match UE on-screen message colours: the PrintString
    default (cyan-blue) and pure red warnings. Packaged dev builds stack these top-left."""
    w, h, rgb = img
    n = 0
    for y in range(0, int(h * 0.45), 2):
        for x in range(0, int(w * 0.45), 2):
            i = (y * w + x) * 3
            r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
            if (r < 70 and g > 170 and b > 220) or (r > 225 and g < 40 and b < 40):
                n += 1
    return n


def ocr_text(path):
    """Text found in the frame, or None if tesseract is missing / failed."""
    if not shutil.which("tesseract"):
        return None
    try:
        p = subprocess.run(["tesseract", str(path), "-", "--psm", "11"], capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 else None


# ---------- analysis ----------

ITEMS = [
    ("capture", "Frames are real captures (not black, flat or undecodable)"),
    ("level", "Real level, not the default grid or an empty room"),
    ("objects", "Player and goal objects visible and readable"),
    ("input", "Input visibly moves the player (frames before and after input differ)"),
    ("hud", "Proper HUD, no debug PrintString / warning text on screen"),
    ("endscreen", "A win or lose screen is reachable"),
    ("restart", "Restart works (the restarted frame is a fresh start, not the end screen)"),
    ("motion", "Idle stability: with no input the view holds still (no looping camera, falling camera or flicker)"),
]


def is_restart_label(label):
    """The one place that decides which shot is the post-restart shot (case-insensitive)."""
    return "restart" in str(label or "").lower()


def analyze(out_dir, ocr=ocr_text, use_ocr=True, end_states=("lose",)):
    """Cheap automated checks over <out>/manifest.json + frames. Returns the results dict."""
    out_dir = Path(out_dir)
    manifest = normalize_manifest(json.loads((out_dir / "manifest.json").read_text(encoding="utf-8-sig")))
    shots = []
    for m in manifest:
        path = out_dir / m["file"]
        try:
            img = read_png(path)
            th = thumb_gray(img)
            m_, sd = mean_sd(th)
            # a burst is dozens of full-size frames: keep only the thumbnail, not the pixels
            shots.append({**m, "path": str(path), "ok": True, "thumb": th, "mean": m_, "sd": sd,
                          **({} if m.get("burst") else {"img": img})})
        except (OSError, ValueError, zlib.error) as e:
            shots.append({**m, "path": str(path), "ok": False, "error": str(e)})
    res = {k: {"id": k, "title": t, "auto": "AGENT", "detail": "", "frames": []} for k, t in ITEMS}
    all_shots = shots
    good_all = [s for s in all_shots if s["ok"]]
    shots = [s for s in all_shots if not s.get("burst")]  # the sequence checks below ignore idle-burst frames
    good = [s for s in shots if s["ok"]]

    # capture
    bad = [f"{s['file']}: {s['error']}" for s in all_shots if not s["ok"]]
    bad += [f"{s['file']}: {'black' if s['mean'] < 12 else 'flat'} frame" for s in good_all if s["sd"] < FLAT_SD_MAX]
    c = res["capture"]
    c["frames"] = [s["file"] for s in shots]
    bad += [f"{s['file']}: the game was not the foreground window (console/lock screen/other app in front)"
            for s in all_shots if s.get("foreground") is False]
    if not all_shots:
        c["auto"], c["detail"] = "FAIL", "no frames were captured"
    elif bad:
        c["auto"], c["detail"] = "FAIL", "; ".join(bad)
    else:
        c["auto"], c["detail"] = "PASS", f"{len(all_shots)} frames, all decodable with visible detail"

    # level: only a heuristic warning about grey
    lv = res["level"]
    lv["frames"] = [s["file"] for s in good[:3]]
    greys = [(s["file"], grey_fraction(s["img"])) for s in good]
    mostly = [f"{f} ({g:.0%})" for f, g in greys if g >= GREY_FRACTION_WARN]
    if mostly:
        lv["auto"], lv["detail"] = "WARN", "mostly grey (default grid / untextured?): " + ", ".join(mostly)
    else:
        lv["detail"] = "colour present; read the frames to judge"

    # objects
    res["objects"]["frames"] = [s["file"] for s in good[:3]]
    res["objects"]["detail"] = "judge by reading the frames"

    # input
    inp = res["input"]
    diffs, idle = [], None
    for prev, cur in zip(shots, shots[1:]):
        if not (prev["ok"] and cur["ok"]):
            continue
        d = mean_abs_diff(prev["thumb"], cur["thumb"])
        if is_restart_label(cur.get("label")):
            continue  # the restart key reloads the level; it is not the player's controls moving anything
        if cur.get("after_input"):
            diffs.append((cur["file"], d))
        elif idle is None:
            idle = d
    inp["frames"] = [f for f, _ in diffs]
    if not diffs:
        inp["auto"], inp["detail"] = "FAIL", "no frame was captured right after an input step"
    else:
        # A game that animates on its own (drift, gusts, water) changes between idle shots too, so an
        # input must change the picture clearly MORE than the idle baseline, not just by a fixed amount.
        need = max(MOVE_DIFF_MIN, IDLE_FACTOR * idle) if idle is not None else MOVE_DIFF_MIN
        moved = [(f, d) for f, d in diffs if d >= need]
        txt = ", ".join(f"{f}={d:.1f}" for f, d in diffs)
        idle_txt = f" (idle baseline {idle:.1f}, needed >= {need:.1f})" if idle is not None else " (no idle baseline shot)"
        if moved and idle is not None:
            inp["auto"], inp["detail"] = "PASS", f"{len(moved)}/{len(diffs)} input steps changed the picture: {txt}{idle_txt}"
        elif moved:
            inp["auto"], inp["detail"] = "WARN", f"picture changed but there is no idle shot to rule out self-animation: {txt}{idle_txt}"
        else:
            inp["auto"], inp["detail"] = "FAIL", f"no input step changed the picture more than idle does: {txt}{idle_txt}"

    # hud / debug text
    hud = res["hud"]
    hud["frames"] = [s["file"] for s in good]
    hits = [(s["file"], debug_colour_pixels(s["img"])) for s in good]
    hits = [(f, n) for f, n in hits if n >= DEBUG_PIXELS_WARN]
    notes = []
    if hits:
        notes.append("debug-colour pixels top-left: " + ", ".join(f"{f}={n}" for f, n in hits))
    ocr_found = []
    if use_ocr:
        for s in good:
            txt = ocr(s["path"])
            if txt is None:
                notes.append("OCR unavailable")
                break
            m = DEBUG_WORDS.search(txt)
            if m:
                ocr_found.append(f"{s['file']}: '{m.group(0)}'")
    if ocr_found:
        notes.append("OCR found debug-looking text: " + ", ".join(ocr_found))
    hud["auto"] = "WARN" if (hits or ocr_found) else "PASS"
    hud["detail"] = "; ".join(notes) if notes else "no debug-colour text, no debug words found"

    # end screen: hint only
    end = res["endscreen"]
    end["frames"] = [s["file"] for s in good[-3:]]
    end["detail"] = "judge by reading the last frames; the sequence must have reached a win or lose screen"

    # restart
    rs = res["restart"]
    first = good[0] if good else None
    rest = next((s for s in reversed(good) if is_restart_label(s.get("label"))), None)
    if first and rest and first is not rest:
        d = mean_abs_diff(first["thumb"], rest["thumb"])
        before = good[good.index(rest) - 1]  # the shot just before the restart = where the game ended up
        moved = mean_abs_diff(before["thumb"], rest["thumb"])
        rs["frames"] = [first["file"], before["file"], rest["file"]]
        # Same bar as input: clearly more than the idle (no input) change, or a self-animating game that
        # ignores the restart key would pass.
        need_r = max(MOVE_DIFF_MIN, IDLE_FACTOR * idle) if idle is not None else MOVE_DIFF_MIN
        rs["detail"] = (f"restarted frame vs first frame differ by {d:.1f} (limit {RESTART_DIFF_MAX}); "
                        f"vs the frame before restart {moved:.1f} (needs >= {need_r:.1f})")
        if before is not first and moved < need_r:
            rs["auto"] = "FAIL"
            rs["detail"] += ": nothing changed at the restart (frozen game or restart key ignored)"
        else:
            rs["auto"] = "PASS" if d <= RESTART_DIFF_MAX else "WARN"
    else:
        rs["detail"] = "no 'restart' shot in the sequence; judge by reading the frames"

    analyze_motion(res["motion"], all_shots, end_states)

    return {"out_dir": str(out_dir), "shots": [{k: v for k, v in s.items() if k not in ("thumb", "img")} for s in all_shots],
            "items": [res[k] for k, _ in ITEMS]}


def burst_groups(shots):
    """label -> frames of that idle burst, in capture order."""
    groups = {}
    for s in shots:
        if s.get("burst"):
            groups.setdefault(s["burst"], []).append(s)
    for g in groups.values():
        g.sort(key=lambda s: s.get("burst_index") or 0)
    return groups


def judge_burst(frames):
    """(status, detail) for one idle burst, from the frame-to-frame change with no input."""
    good = [s for s in frames if s["ok"]]
    if len(frames) < BURST_MIN_FRAMES or len(good) != len(frames):
        return "FAIL", f"only {len(good)} readable frames of {len(frames)} (need >= {BURST_MIN_FRAMES})"
    # The spacing the validator promises is only a request; judge the captured times. Frames that really came
    # more than ~1 s apart can land on the same phase of a ~1 s loop and look still.
    ts = [s.get("t") for s in good]
    if any(not isinstance(t, (int, float)) for t in ts):
        return "FAIL", "burst frames have no capture times (t), so their spacing cannot be checked"
    spacing = (ts[-1] - ts[0]) / (len(ts) - 1)
    if spacing > BURST_MAX_SPACING * BURST_SPACING_SLACK:
        return "FAIL", (f"frames too slow to judge motion: captured {spacing:.2f} s apart on average, limit "
                        f"{BURST_MAX_SPACING} s (+25% slack); a ~1 s camera loop would look still. Capture faster "
                        "(smaller screen, lighter machine) and rerun")
    steps = [mean_abs_diff(a["thumb"], b["thumb"]) for a, b in zip(good, good[1:])]
    mean_step, max_step = sum(steps) / len(steps), max(steps)
    drift = max(mean_abs_diff(good[0]["thumb"], g["thumb"]) for g in good[1:])
    txt = f"{len(good)} frames, mean step {mean_step:.1f}, biggest step {max_step:.1f}, drift from first {drift:.1f}"
    why = []
    if mean_step > IDLE_STEP_MAX:
        why.append(f"mean step above {IDLE_STEP_MAX}")
    if max_step > IDLE_JUMP_MAX:
        why.append(f"a single jump above {IDLE_JUMP_MAX}")
    if drift > IDLE_DRIFT_MAX:
        why.append(f"drift above {IDLE_DRIFT_MAX}")
    if why:
        return "FAIL", f"{txt} ({'; '.join(why)}): the view keeps changing with no input (loop, falling camera or flicker)"
    if mean_step > IDLE_STEP_WARN:
        return "WARN", f"{txt}: something animates on its own; read the contact sheet"
    return "PASS", txt


def missing_bursts(all_shots, end_states=("lose",)):
    """What the capture order says was never sampled: one burst per declared end state, the LAST capture
    before the restart shot being an end-state burst (nothing else between it and the restart), and a burst
    after the restart shot. Empty list = fine."""
    order = list(all_shots)
    out = []
    for st in end_states:
        if not any(s.get("burst") and s.get("end_state") == st for s in order):
            out.append(f"no idle burst for the declared '{st}' end state")
    rest = [i for i, s in enumerate(order) if not s.get("burst") and is_restart_label(s.get("label"))]
    if not rest:
        return out + ["no 'restarted' shot, so the restart cannot be placed"]
    r = rest[-1]
    if r == 0 or not (order[r - 1].get("burst") and order[r - 1].get("end_state")):
        out.append("the last capture before the restart is not an end-state burst (the end state was never "
                   "sampled right before restarting)")
    if not any(s.get("burst") for s in order[r + 1:]):
        out.append("no idle burst after the restart")
    return out


def analyze_motion(item, all_shots, end_states=("lose",)):
    """The 'motion' item: every idle burst must hold still. No burst at all FAILs, the item is required."""
    groups = burst_groups(all_shots)
    if not groups:
        item["auto"], item["detail"] = "FAIL", "no idle burst was captured; add burst steps (see stages/03_playtest/references/playtest-gate.md)"
        return
    rank = {"PASS": 0, "WARN": 1, "FAIL": 2}
    worst, parts = "PASS", []
    missing = missing_bursts(all_shots, end_states)
    if missing:
        worst = "FAIL"
        parts.append("MISSING: " + "; ".join(missing))
    for label, frames in groups.items():
        st, detail = judge_burst(frames)
        parts.append(f"{label}: {st} - {detail}")
        if rank[st] > rank[worst]:
            worst = st
    item["auto"], item["detail"] = worst, " | ".join(parts)
    item["frames"] = [sheet_name(label) for label in groups]


def write_burst_sheets(out_dir, results):
    """One contact sheet per burst (capture order, left to right then down) for the agent to Read.
    Returns the file names; run_gate lists them in results['sheets'] so the run stamp hashes them."""
    out_dir = Path(out_dir)
    names = []
    for label, frames in burst_groups(results["shots"]).items():
        tiles = []
        for s in frames:
            try:
                tiles.append(scale_rgb(read_png(out_dir / s["file"]), *SHEET_TILE))
            except (OSError, ValueError, zlib.error):
                pass  # already reported as unreadable by the capture check
        if tiles:
            write_contact_sheet(tiles, out_dir / sheet_name(label))
            names.append(sheet_name(label))
    return names


def build_steps(results):
    """One entry per still frame (bursts are judged by their own sheet): number, label, time, which
    step sheet and tile it is on, and the harness verdict for that frame (PASS/WARN/FAIL/AGENT).
    A frame's verdict is the worst Auto of every checklist item that lists it; a frame no item lists is
    PASS when it decoded and FAIL when it did not."""
    by_file = {}
    for it in results["items"]:
        # An item that lists many frames (capture, hud) but names the bad ones in its detail blames only those
        # frames; one bad burst frame must not turn every still FAIL. No named frame = it blames all it lists.
        named = set(re.findall(r"[\w.-]+\.png", it.get("detail", ""))) if it["auto"] != "PASS" else set()
        for f in it["frames"]:
            by_file.setdefault(f, []).append(it["auto"] if not named or f in named else "PASS")
    steps = []
    for n, s in enumerate([s for s in results["shots"] if not s.get("burst")], 1):
        autos = by_file.get(s["file"]) or ["FAIL" if s.get("ok") is False else "PASS"]  # a shot with no "ok" key was not marked unreadable
        k = (n - 1) // STEP_SHEET_FRAMES + 1
        steps.append({"n": n, "label": s.get("label", ""), "file": s["file"], "t": s.get("t"),
                      "sheet": step_sheet_name(k), "tile": (n - 1) % STEP_SHEET_FRAMES + 1,
                      "auto": max(autos, key=lambda a: SEVERITY.get(a, 1))})
    return steps


def step_sheet_name(k):
    return f"contact_steps_{k}.png"  # bursts cannot have "_" in their label, so this never collides with theirs


def write_step_sheets(out_dir, results):
    """Contact sheets of the still frames, STEP_SHEET_FRAMES per sheet, each tile labelled with step number,
    label and time. Fills results['steps'] and returns the sheet names (run_gate adds them to results['sheets'])."""
    out_dir = Path(out_dir)
    steps = results["steps"] = build_steps(results)
    names = []
    for i in range(0, len(steps), STEP_SHEET_FRAMES):
        chunk, tiles, labels = steps[i:i + STEP_SHEET_FRAMES], [], []
        for st in chunk:
            try:
                tiles.append(scale_rgb(read_png(out_dir / st["file"]), *SHEET_TILE))
            except (OSError, ValueError, zlib.error):
                tiles.append(b"\xc0\x00\x00" * (SHEET_TILE[0] * SHEET_TILE[1]))  # red tile keeps the numbering aligned
            labels.append(f"{st['n']:02d} {st['label']} t={st['t']:g}s" if isinstance(st["t"], (int, float))
                          else f"{st['n']:02d} {st['label']}")
        write_contact_sheet(tiles, out_dir / chunk[0]["sheet"], cols=STEP_SHEET_COLS, labels=labels)
        names.append(chunk[0]["sheet"])
    return names


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clear_previous(out_dir):
    """Remove every artifact of an earlier run so nothing stale (a judged checklist, old frames) survives."""
    out_dir = Path(out_dir)
    for pat in ("*.png", "manifest.json", "results.json", "checklist.md", "gate.ok", "ERROR", "DONE", "FOCUSED"):
        for f in out_dir.glob(pat):
            f.unlink()
    shutil.rmtree(out_dir / "video_frames", ignore_errors=True)


def stamp(out_dir, results, build=""):
    """Tie the results to this run's exact frames, so verify can tell the checklist belongs to them."""
    out_dir = Path(out_dir)
    results["run_id"] = uuid.uuid4().hex
    results["build"] = build
    results["manifest_sha256"] = _sha(out_dir / "manifest.json")
    files = [s["file"] for s in results["shots"]] + list(results.get("sheets", []))
    results["frames_sha256"] = {f: _sha(out_dir / f) for f in files if (out_dir / f).exists()}
    return results


STEPS_HEADING = "## Step review (prefilled from the harness; resolve every AGENT, WARN and FAIL)"


def write_checklist(out_dir, results, build=""):
    if "steps" not in results:
        results["steps"] = build_steps(results)  # run_gate already did this (with sheets); direct callers get no sheets
    stamp(out_dir, results, build)
    sheets = list(results.get("sheets", []))
    step_sheets = [x for x in sheets if x.startswith("contact_steps_")]
    lines = ["# Visual playtest checklist", "",
             f"Build: {build or '(not recorded)'}",
             f"Run: {results['run_id']}",
             "",
             "Look at the contact sheets (one Read each), not every PNG: " + (", ".join(step_sheets) or "(no sheets)"),
             "Open a single PNG only when a tile is unclear. `Auto:` is a cheap hint, never the verdict.",
             "Replace `Verdict: PENDING` with `Verdict: PASS` or `Verdict: FAIL - <why>` on every item.",
             "Every step below is prefilled with the harness verdict (PASS / WARN / FAIL / AGENT). AGENT, WARN and FAIL",
             "are unresolved: after looking, write `Verdict: PASS` or `Verdict: PASS (reviewed: <why>)`, or `Verdict: FAIL - <why>`.",
             "A blank verdict never passes. An Auto FAIL may only be passed with `(override: <why>)`.",
             "Then run `./scripts/visual_playtest.py gate <this folder>`; the build is not done until it exits 0.", ""]
    for n, it in enumerate(results["items"], 1):
        lines += [f"### {n}. {it['title']}", f"Auto: {it['auto']} - {it['detail']}",
                  "Look at: " + (", ".join(it["frames"]) if it["frames"] else "(none)"), "Verdict: PENDING", ""]
    lines += [STEPS_HEADING, ""]
    for st in results["steps"]:
        t = f", t={st['t']:g}s" if isinstance(st.get("t"), (int, float)) else ""
        lines += [f"#### Step {st['n']:02d}: {st['label']}{t} ({st['sheet']}, tile {st['tile']}; {st['file']})",
                  f"Auto: {st['auto']}", f"Verdict: {st['auto']}", ""]
    p = Path(out_dir) / "checklist.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    (Path(out_dir) / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return p


def verify(out_dir):
    """The gate. Returns (ok, problems)."""
    out_dir = Path(out_dir)
    p, rp = out_dir / "checklist.md", out_dir / "results.json"
    if not p.exists() or not rp.exists():
        return False, [f"{p} or {rp} not found; run `visual_playtest.py run` first"]
    text = p.read_text(encoding="utf-8")
    try:
        results = json.loads(rp.read_text(encoding="utf-8"))
        autos = [i["auto"] for i in results["items"]]
        run_id = results["run_id"]
    except (ValueError, KeyError, TypeError):
        return False, ["results.json is unreadable or incomplete; run `visual_playtest.py run` again"]
    # The checklist must belong to exactly these results and these frames (no stale or swapped files).
    m = re.search(r"^Run: (\w+)$", text, re.M)
    if not m or m.group(1) != run_id:
        return False, ["checklist.md belongs to a different run than results.json; run `visual_playtest.py run` again"]
    mp = out_dir / "manifest.json"
    if not mp.exists() or _sha(mp) != results.get("manifest_sha256"):
        return False, ["manifest.json changed since the run; run `visual_playtest.py run` again"]
    changed = [f for f, h in results.get("frames_sha256", {}).items() if not (out_dir / f).exists() or _sha(out_dir / f) != h]
    if changed or not results.get("frames_sha256"):
        return False, [f"frames changed or missing since the run: {', '.join(changed) or 'none recorded'}"]
    head, sep, step_text = text.partition(STEPS_HEADING)
    steps = results.get("steps")
    if not sep or not isinstance(steps, list):
        return False, ["checklist has no step review section; run `visual_playtest.py run` again"]
    blocks = re.split(r"^### ", head, flags=re.M)[1:]
    if len(blocks) != len(ITEMS) or len(autos) != len(ITEMS):
        return False, [f"checklist has {len(blocks)} items, expected {len(ITEMS)}; do not edit the headings"]
    step_blocks = re.split(r"^#### ", step_text, flags=re.M)[1:]
    if len(step_blocks) != len(steps):
        return False, [f"checklist has {len(step_blocks)} step blocks, expected {len(steps)}; do not edit the headings"]
    problems = []
    rows = [(b, a) for b, a in zip(blocks, autos)] + [(b, st.get("auto")) for b, st in zip(step_blocks, steps)]
    for b, auto in rows:  # Auto comes from results.json, never from the editable checklist
        title = b.splitlines()[0]
        v = re.search(r"^Verdict:[ \t]*(.*)$", b, re.M)
        verdict = v.group(1).strip() if v else ""
        up = verdict.upper()
        if not verdict:
            problems.append(f"{title}: Verdict is blank (look at the frame, then write PASS or FAIL - <why>)")
        elif up == "PENDING":
            problems.append(f"{title}: Verdict is still PENDING (look at the frames, then write PASS or FAIL - <why>)")
        elif up.startswith("AGENT"):
            problems.append(f"{title}: Verdict 'AGENT' is unresolved (the harness could not judge it; you must)")
        elif not up.startswith("PASS"):
            problems.append(f"{title}: Verdict is '{verdict}'")
        elif auto == "FAIL" and "override:" not in verdict.lower():
            problems.append(f"{title}: Auto FAIL needs 'Verdict: PASS (override: <why>)'")
    return not problems, problems


def receipt_valid(out_dir):
    """True only if gate.ok exists, belongs to this run, hashes the CURRENT checklist, and verify still passes.
    A ship step that wants the receipt without re-running `gate` calls this (CLI: `gate --check`)."""
    out_dir = Path(out_dir)
    try:
        rec = json.loads((out_dir / "gate.ok").read_text(encoding="utf-8"))
        run_id = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))["run_id"]
        return (rec["run_id"] == run_id and rec["checklist_sha256"] == _sha(out_dir / "checklist.md")
                and verify(out_dir)[0])
    except (OSError, ValueError, KeyError, TypeError):
        return False


def gate(out_dir):
    """The ship / findings step calls this. Same rules as verify, plus a receipt: on PASS it writes
    <out>/gate.ok (run id + checklist hash); on anything else it deletes any old receipt. Returns (ok, problems)."""
    out_dir = Path(out_dir)
    receipt = out_dir / "gate.ok"
    ok, problems = verify(out_dir)
    if receipt.exists():
        receipt.unlink()  # never leave a receipt a later edit could outlive
    if ok:
        results = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
        receipt.write_text(json.dumps({"run_id": results["run_id"], "checklist_sha256": _sha(out_dir / "checklist.md")}),
                           encoding="utf-8")
    return ok, problems


# ---------- video frames (e.g. a legion_record.py mp4) ----------

def extract_frames(video, out_dir, n, runner=subprocess.run):
    """Extract n evenly spaced PNGs from a recording into out_dir. Returns the file list."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = runner(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
               capture_output=True, text=True, timeout=30)
    try:
        dur = float(p.stdout.strip())
    except ValueError:
        raise RuntimeError(f"cannot read the duration of {video}")
    files = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        f = out_dir / f"video_{i + 1:02d}.png"
        runner(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(f)],
               capture_output=True, timeout=60)
        if f.exists():
            files.append(f)
    if not files:
        raise RuntimeError(f"no frames could be extracted from {video}")
    return files


# ---------- backends ----------

def game_process(game_name, env=None):
    """Windows process to watch. Normally the game name. MJ_GAME_PROC overrides it for a
    content-only package, where the stub exe can fail (0x800701C7) and the engine exe is launched directly."""
    proc = (os.environ if env is None else env).get("MJ_GAME_PROC")
    if not proc:
        return game_name
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", proc):
        raise ValueError(f"MJ_GAME_PROC {proc!r} must be letters, digits, _ . - only")
    return proc


def content_only(proc):
    """Only the engine exe (content-only package) gets the task repoint. Any other override, such as
    the game's own name or Game-Win64-Shipping for a C++ package, just changes which process is watched."""
    return proc.lower() == "unrealgame"


def engine_launch_cmd(task_name, game_name):
    """Point the game task at Engine\\Binaries\\Win64\\UnrealGame.exe next to the deployed stub exe."""
    return ('powershell -Command "$t=Get-ScheduledTask %s; $d=Split-Path $t.Actions[0].Execute; '
            '$a=New-ScheduledTaskAction -Execute (Join-Path $d Engine\\Binaries\\Win64\\UnrealGame.exe) '
            '-Argument ..\\..\\..\\%s\\%s.uproject -WorkingDirectory (Join-Path $d Engine\\Binaries\\Win64); '
            'Set-ScheduledTask -TaskName %s -Action $a | Out-Null"' % (task_name, game_name, game_name, task_name))


class LegionBackend:
    """Remote Windows run over ssh. Every external call goes through self.run so tests can fake it."""

    def __init__(self, host, remote_zip, game_name, task_name="MegaJamLaunchGame", warmup=WARMUP_DEFAULT,
                 run=None, deploy=None, sleep=time.sleep, probe=None, warmup_max=WARMUP_MAX):
        """probe: optional callable returning None (screen is real) or one plain failure line. When set,
        it runs before the launch (locked console) and again after the warmup, which is extended while
        the screen is still black, up to warmup_max seconds."""
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", game_name or ""):
            raise ValueError(f"game name {game_name!r} must be letters, digits, _ . - only")
        self.host, self.remote_zip, self.game_name, self.task_name, self.warmup = host, remote_zip, game_name, task_name, warmup
        self.probe, self.warmup_max = probe, max(warmup, warmup_max)
        self._lock_checked = False
        self.run = run or self._run
        self.deploy = deploy or self._deploy
        self.sleep = sleep

    @staticmethod
    def _run(cmd, timeout=120):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {timeout}s"
        return p.returncode, p.stdout, p.stderr

    @staticmethod
    def _deploy(host, remote_zip, game_name, task_name):
        sys.path.insert(0, str(HERE))
        import legion_playtest  # noqa: PLC0415 - the existing deploy+register helper
        return legion_playtest.deploy_and_register(host, remote_zip, game_name, task_name)

    def ssh(self, cmd, timeout=120):
        return self.run(["ssh", *SSH_OPTS, self.host, cmd], timeout)

    def alive(self):
        proc = game_process(self.game_name)
        rc, out, _ = self.ssh(f'powershell -Command "Get-Process {proc} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"')
        return rc == 0 and bool(out.strip())

    def _wait_for_picture(self):
        """After the warmup: probe the screen; while it is black, wait and probe again up to warmup_max.
        A locked console stops at once; a screen still black at the limit is reported, not played."""
        if not self.probe:
            return
        waited = self.warmup
        while True:
            t = time.monotonic()
            msg = self.probe()
            if msg is None:
                return
            # a probe shot takes real time (ssh + scp + polling): count it, so warmup_max is wall clock
            waited += max(time.monotonic() - t, PROBE_COST_EST)
            if msg == MSG_LOCKED or waited >= self.warmup_max:
                raise RuntimeError(msg)
            self.sleep(PROBE_INTERVAL)
            waited += PROBE_INTERVAL

    def check_lock(self):
        """Stop before deploying anything if the console is locked. Only a lock blocks here: a black
        frame before the launch can be the OLD hung game that this launch is meant to replace."""
        if self.probe and not self._lock_checked:
            self._lock_checked = True
            msg = self.probe()
            if msg == MSG_LOCKED:
                raise RuntimeError(msg)

    def launch(self):
        self.check_lock()
        self._lock_checked = False
        self.deploy(self.host, self.remote_zip, self.game_name, self.task_name)
        if content_only(game_process(self.game_name)):  # content-only package: launch the engine exe directly
            rc, _, err = self.ssh(engine_launch_cmd(self.task_name, self.game_name))
            if rc != 0:  # the task would still start the blocked stub exe
                raise RuntimeError(f"could not point the game task at UnrealGame.exe: {err.strip()[-120:]}")
        rc, _, err = self.ssh(f"schtasks /Run /TN {self.task_name}")
        if rc != 0:
            raise RuntimeError(f"could not run the game task: {err.strip()[-120:]}")
        self.sleep(self.warmup)
        if not self.alive():
            raise RuntimeError(f"{self.game_name} is not running after launch (crashed or never started)")
        self._wait_for_picture()

    def play(self, steps, out_dir):
        """Run the steps in the console session; fetch frames + manifest into out_dir."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        local_ps1 = HERE / INPUT_PS1
        with tempfile.TemporaryDirectory() as td:
            steps_file = Path(td) / "steps.json"
            steps_file.write_text(json.dumps(steps), encoding="utf-8")
            self.ssh(f'powershell -Command "New-Item -ItemType Directory -Force -Path {REMOTE_SCRATCH} | Out-Null"')
            self.ssh(f'powershell -Command "Remove-Item -Recurse -Force {REMOTE_OUT} -ErrorAction SilentlyContinue"')
            for src, dst in ((local_ps1, f"{REMOTE_SCRATCH}/{INPUT_PS1}"), (steps_file, REMOTE_STEPS)):
                rc, _, err = self.run(["scp", *SSH_OPTS, str(src), f"{self.host}:{dst}"], 120)
                if rc != 0:
                    raise RuntimeError(f"scp of {Path(src).name} failed: {err.strip()[-120:]}")
            # no inner quotes and no spaces in any path: they get mangled across bash -> ssh -> schtasks
            # -WindowStyle Hidden: a visible console would take the foreground and swallow the keys.
            tr = (f"powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File {REMOTE_SCRATCH}/{INPUT_PS1} "
                  f"-StepsFile {REMOTE_STEPS} -OutDir {REMOTE_OUT} -GameProcess {game_process(self.game_name)}")
            rc, _, err = self.ssh(f'schtasks /Create /TN {INPUT_TASK} /TR "{tr}" /SC ONCE /ST 00:00 /IT /F')
            if rc != 0:
                raise RuntimeError(f"could not create the input task: {err.strip()[-120:]}")
            try:
                rc, _, err = self.ssh(f"schtasks /Run /TN {INPUT_TASK}")
                if rc != 0:
                    raise RuntimeError(f"could not start the input task: {err.strip()[-120:]}")
                self._wait_done(sequence_seconds(steps) + 90)
            finally:
                self.ssh(f"schtasks /Delete /TN {INPUT_TASK} /F")
            fetch = Path(td) / "fetch"
            fetch.mkdir()
            rc, _, err = self.run(["scp", *SSH_OPTS, "-r", f"{self.host}:{REMOTE_OUT}", str(fetch)], 300)
            got = fetch / "vp"
            if rc != 0 or not got.exists():
                raise RuntimeError(f"scp of the frames failed: {err.strip()[-120:]}")
            err_file = got / "ERROR"
            if err_file.exists():
                msg = err_file.read_text(encoding="utf-8-sig", errors="replace").strip()
                raise RuntimeError(f"the input script stopped early: {msg[:200]}")
            for f in got.iterdir():
                if f.name != "DONE":
                    shutil.copy2(f, out_dir / f.name)

    def _wait_done(self, limit):
        waited = 0
        while waited < limit:
            self.sleep(3)
            waited += 3
            rc, out, _ = self.ssh(f'if exist {REMOTE_OUT.replace("/", chr(92))}\\DONE (echo YES) else (echo NO)')
            if rc == 0 and "YES" in out:
                return
        raise RuntimeError(f"the input script did not finish within {int(limit)}s")

    def close(self):
        """Ask the game to close from the console session first; force only if it stays alive."""
        name = game_process(self.game_name)  # the process that actually runs (MJ_GAME_PROC for content-only packages)
        close_task = f"MJToolClose{self.game_name}"
        tr = f"powershell -NoProfile -Command (Get-Process {name} -ErrorAction SilentlyContinue).CloseMainWindow()"
        rc, _, _ = self.ssh(f'schtasks /Create /TN {close_task} /TR "{tr}" /SC ONCE /ST 00:00 /IT /F')
        if rc == 0:
            self.ssh(f"schtasks /Run /TN {close_task}")
        try:
            for _ in range(6):
                self.sleep(2)
                if not self.alive():
                    return True
            self.ssh(f'powershell -Command "Stop-Process -Name {name} -Force -ErrorAction SilentlyContinue"')
            return False
        finally:
            self.ssh(f"schtasks /Delete /TN {close_task} /F")


class LocalBackend:
    """Packaged Linux build (or `UnrealEditor ... -game`) on this desktop: ffmpeg x11grab for frames, xdotool or
    /dev/uinput for keys. X11 / XWayland only: start the game with SDL_VIDEODRIVER=x11.

    On KDE Wayland (mock jam 15) a grab of the X root window is pure black (rootless Xwayland), so pass
    `window` (an `xdotool search --name` pattern): frames are then grabbed from that window id, and one click in
    the window gives it focus before the first input (mock 12's 5c recipe). `keyinput="uinput"` sends keys from a
    virtual keyboard (python evdev, /dev/uinput) instead of xdotool's XTEST."""

    def __init__(self, cmd, warmup=10, display=None, run=None, popen=subprocess.Popen, sleep=time.sleep,
                 window=None, keyinput="xdotool", uinput_factory=None, window_tries=10):
        self.cmd, self.warmup, self.sleep, self.popen = cmd, warmup, sleep, popen
        self.display = display or ":0"
        self.run = run or (lambda c, timeout=60: subprocess.run(c, capture_output=True, text=True, timeout=timeout))
        self.proc = None
        if keyinput not in ("xdotool", "uinput"):
            raise ValueError(f"keyinput must be xdotool or uinput, not {keyinput!r}")
        self.window, self.keyinput, self.window_tries = window, keyinput, window_tries
        self.win_id, self._ui, self._uinput_factory = None, None, uinput_factory

    def launch(self):
        self.proc = self.popen(self.cmd)
        self.sleep(self.warmup)
        if self.proc.poll() is not None:
            raise RuntimeError(f"{self.cmd[0]} exited right after launch (code {self.proc.returncode})")
        if self.window:
            self.win_id = self._find_window()

    def _window_size(self, wid):
        p = self.run(["xdotool", "getwindowgeometry", "--shell", wid])
        vals = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line) if p.returncode == 0 else {}
        try:
            return int(vals["WIDTH"]), int(vals["HEIGHT"])
        except (KeyError, ValueError):
            return 0, 0

    def _find_window(self):
        """The largest X window whose name matches `window`; retried while the game is still opening."""
        for _ in range(self.window_tries):
            p = self.run(["xdotool", "search", "--name", self.window])
            ids = p.stdout.split() if p.returncode == 0 else []
            sized = [(w * h, wid) for wid in ids for (w, h) in [self._window_size(wid)] if w * h > 0]
            if sized:
                return max(sized)[1]
            self.sleep(3)
        raise RuntimeError(f"no X window named like {self.window!r} (is the game on X11? SDL_VIDEODRIVER=x11)")

    def _geometry(self):
        if self.win_id:
            w, h = self._window_size(self.win_id)
            if w and h:
                return w, h
            raise RuntimeError(f"window {self.win_id} has no geometry (closed?)")
        p = self.run(["xdotool", "getdisplaygeometry"])
        if p.returncode != 0 or len(p.stdout.split()) != 2:
            raise RuntimeError(f"xdotool getdisplaygeometry failed (no X display?): {(p.stderr or '').strip()[-120:]}")
        w, h = p.stdout.split()
        return int(w), int(h)

    def _xdo(self, *args):
        """Run one xdotool command; a failure means no input reached the game, so stop the run."""
        p = self.run(["xdotool", *args])
        if p.returncode != 0:
            raise RuntimeError(f"xdotool {' '.join(args)} failed: {(p.stderr or '').strip()[-120:]}")

    def _grab(self, size, path):
        src = ["-window_id", self.win_id] if self.win_id else ["-video_size", size]
        p = self.run(["ffmpeg", "-v", "error", "-y", "-f", "x11grab", *src, "-i", self.display,
                      "-frames:v", "1", str(path)])
        if p.returncode != 0:
            raise RuntimeError(f"screen grab failed: {(p.stderr or '').strip()[-120:]}")

    def play(self, steps, out_dir):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        w, h = self._geometry()
        size = "%dx%d" % (w, h)
        if self.win_id:  # Xwayland gives keys to the game only after a click in its window (mock 12, 5c)
            self._xdo("mousemove", "--window", self.win_id, str(w // 2), str(h // 2))
            self._xdo("click", "1")
        manifest, n, t0, after = [], 0, time.monotonic(), False
        for s in steps:
            op = s["op"]
            if op == "wait":
                self.sleep(float(s["seconds"]))
            elif op == "shot":
                n += 1
                name = f"{n:02d}_{s['label']}.png"
                self._grab(size, out_dir / name)
                manifest.append({"label": s["label"], "file": name, "t": round(time.monotonic() - t0, 2), "after_input": after})
                after = False
            elif op == "burst":
                # N frames over `seconds` with NO input; the frames are never "after_input"
                frames, seconds = burst_params(s)
                for i in range(1, frames + 1):
                    n += 1
                    label = f"burst_{s['label']}_{i:02d}"
                    name = f"{n:02d}_{label}.png"
                    t_frame = time.monotonic()
                    self._grab(size, out_dir / name)
                    manifest.append({"label": label, "file": name, "t": round(time.monotonic() - t0, 2), "after_input": False,
                                     "burst": s["label"], "burst_index": i,
                                     **({"end_state": s["end_state"]} if s.get("end_state") else {})})
                    self.sleep(max(0.0, seconds / frames - (time.monotonic() - t_frame)))
                after = False
            elif op == "key":
                names = step_keys(s)  # all pressed in order, held together, released in reverse order
                if self.keyinput == "uinput":
                    ui, codes = self._uinput(), [evdev_code(k) for k in names]
                    for code in codes:
                        ui.write(EV_KEY, code, 1)
                    ui.syn()
                    self.sleep(float(s.get("hold", 0.1)))
                    for code in reversed(codes):
                        ui.write(EV_KEY, code, 0)
                    ui.syn()
                else:
                    syms = [KEYS[k][2] for k in names]  # X keysyms (Escape, Return, Shift_L...), not our short names
                    for sym in syms:
                        self._xdo("keydown", sym)
                    self.sleep(float(s.get("hold", 0.1)))
                    for sym in reversed(syms):
                        self._xdo("keyup", sym)
                after = True
            elif op == "click":
                if "x" in s:
                    self._xdo("mousemove", str(s["x"]), str(s["y"]))
                self._xdo("click", "3" if s.get("button") == "right" else "1")
                after = True
            elif op == "move":
                self._xdo("mousemove_relative", "--", str(s["dx"]), str(s["dy"]))
                after = True
        (out_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def _uinput(self):
        if self._ui is None:
            self._ui = (self._uinput_factory or _evdev_uinput)(sorted({evdev_code(k) for k in KEYS}))
        return self._ui

    def close(self):
        if self._ui is not None:
            try:
                self._ui.close()
            except Exception:
                pass
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        return True


EV_KEY = 1  # linux/input-event-codes.h
_EXTENDED_EVDEV = {0x48: 103, 0x4B: 105, 0x4D: 106, 0x50: 108}  # up, left, right, down


def evdev_code(name):
    """Linux key code for a KEYS name: set-1 scan codes equal evdev codes, except the extended arrows."""
    scan, extended, _ = KEYS[name]
    return _EXTENDED_EVDEV[scan] if extended else scan


def _evdev_uinput(codes):
    from evdev import UInput  # optional dependency, only for --local-input uinput
    ui = UInput({EV_KEY: codes}, name="megajam-playtest-kbd")
    time.sleep(1.0)  # let the compositor see the new device before the first key
    return ui


# ---------- orchestration ----------

def run_gate(backend, steps, out_dir, build="", video=None, frames=0, ocr=ocr_text, use_ocr=True):
    """Launch, play, always close, then analyse and write the checklist. Returns (results, checklist_path)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    clear_previous(out_dir)  # a failed run must leave nothing a previous PASS could hide behind
    try:
        backend.launch()
        backend.play(steps, out_dir)
    finally:
        backend.close()
    if video and frames:
        extract_frames(video, out_dir / "video_frames", frames)
    decl = next((s for s in steps if s["op"] == "declare"), None)
    end_states = tuple(decl["end_states"]) if decl else ("lose",)
    results = analyze(out_dir, ocr=ocr, use_ocr=use_ocr, end_states=end_states)
    results["end_states"] = list(end_states)
    results["sheets"] = write_step_sheets(out_dir, results) + write_burst_sheets(out_dir, results)
    return results, write_checklist(out_dir, results, build)


def attach_vlm_judge(out_dir, results, judge_fn=None):
    """Optional (--vlm-judge): ask the local VLM about the last frame and append the verdict to results.json
    and checklist.md. Advisory only: any judge error is recorded as "unavailable" and never fails the gate.
    Written after stamp(), in a '## ' section, so verify() ignores it."""
    out_dir = Path(out_dir)
    frame = (results.get("shots") or [{}])[-1].get("file")
    try:
        if judge_fn is None:
            sys.path.insert(0, str(HERE))
            import vlm_judge
            judge_fn = vlm_judge.judge
        if not frame or not (out_dir / frame).exists():
            raise RuntimeError("no frame to judge")
        entry = dict(judge_fn(out_dir / frame))
        entry["status"] = "pass" if entry.get("pass") else "fail"
    except Exception as e:  # noqa: BLE001 - the judge must never break the gate
        entry = {"status": "unavailable", "frame": frame, "reason": str(e)[:300]}
    results["vlm_judge"] = entry
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    lines = ["", "## VLM judge (advisory; not a verdict, not part of the gate)", f"Status: {entry['status']}"]
    if entry["status"] == "unavailable":
        lines.append(f"Reason: {entry['reason']}")
    else:
        lines += [f"Frame: {entry['frame']}  Model: {entry.get('model', '?')}  Confidence: {entry['confidence']}",
                  f"hud_readable={entry['hud_readable']} title_line_present={entry['title_line_present']} "
                  f"camera_steady={entry['camera_steady']}",
                  "Issues: " + ("; ".join(entry["issues"]) or "(none)")]
    # Model text is untrusted: one line per field, so it can never add a '### ' heading or a 'Verdict:' line.
    lines = [" ".join(str(x).split()) for x in lines]
    cp = out_dir / "checklist.md"
    cp.write_text(cp.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return entry


def load_sequence(path):
    steps = DEFAULT_SEQUENCE if not path else json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_sequence(steps)


def report(results, checklist):
    for it in results["items"]:
        print(f"[{it['auto']:5}] {it['title']} - {it['detail']}")
    print(f"\nchecklist: {checklist}")
    sheets = [x for x in results.get("sheets", []) if x.startswith("contact_steps_")]
    print(f"NEXT: Read {', '.join(sheets) or 'the PNGs'} (one image each), set every 'Verdict:' line in the checklist, then run:")
    print(f"  {HERE / 'visual_playtest.py'} gate {Path(checklist).parent}")
    return 1 if any(i["auto"] == "FAIL" for i in results["items"]) else 0


def local_argv(cmd):
    """--local-cmd as an argv. argparse stops a nargs="+" list at the first word starting with '-', so a
    launch like `systemd-run --user --scope ... UnrealEditor x.uproject -game` cannot be passed word by word
    (mock 15). One quoted string is split like a shell would split it, unless the whole string is an existing
    file (an executable path with a space in it stays one argv item)."""
    cmd = list(cmd or [])
    if len(cmd) == 1 and any(c.isspace() for c in cmd[0]) and not os.path.isfile(cmd[0]):
        return shlex.split(cmd[0])
    return cmd


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="play the packaged build and write the checklist")
    r.add_argument("--target", choices=["device-host", "local"], default="device-host")
    r.add_argument("--out", required=True, help="output folder (frames, manifest.json, checklist.md)")
    r.add_argument("--sequence", help="JSON step file; default is the generic WASD/space/mouse/R sequence")
    r.add_argument("--host", default=DEFAULT_HOST)
    r.add_argument("--remote-zip")
    r.add_argument("--game-name")
    r.add_argument("--task-name", default="MegaJamLaunchGame")
    r.add_argument("--local-cmd", nargs="+",
                   help="command that starts the local packaged build; a command whose words start with '-' "
                        "(systemd-run --user ..., -game) must be ONE quoted string, which is split like a shell")
    r.add_argument("--local-window", help="local: xdotool --name pattern of the game window; frames come from that window "
                   "(a root grab is black on KDE Wayland) and one click focuses it")
    r.add_argument("--local-input", choices=("xdotool", "uinput"), default="xdotool",
                   help="local: key source; uinput = virtual keyboard via python evdev (needs rw on /dev/uinput)")
    r.add_argument("--warmup", type=int, default=WARMUP_DEFAULT,
                   help=f"seconds to wait after launch (default {WARMUP_DEFAULT}: a cold first start is slow); on the "
                        f"Legion it is extended while the screen is still black, up to {WARMUP_MAX} s")
    r.add_argument("--skip-probe", action="store_true",
                   help="Legion: skip the lock / black-screen probe shots (not recommended)")
    r.add_argument("--video", help="optional mp4 (e.g. from legion_record.py) to pull extra frames from")
    r.add_argument("--frames", type=int, default=0, help="number of frames to extract from --video")
    r.add_argument("--no-ocr", action="store_true")
    r.add_argument("--vlm-judge", action="store_true",
                   help="also ask the local VLM (scripts/vlm_judge.py) about the last frame; advisory, off by default")
    r.add_argument("--build", default="", help="free text recorded in the checklist (zip name, commit)")
    a = sub.add_parser("analyze", help="redo the automated checks on an existing folder")
    a.add_argument("out")
    a.add_argument("--no-ocr", action="store_true")
    v = sub.add_parser("verify", help="the gate: exit 0 only if every verdict is PASS")
    v.add_argument("out")
    g = sub.add_parser("gate", help="for the ship/findings step: exit non-zero until verify passes; writes gate.ok on PASS")
    g.add_argument("out")
    g.add_argument("--check", action="store_true", help="only check that gate.ok is still valid for the current checklist")
    args = ap.parse_args(argv)

    if args.cmd == "gate" and args.check:
        ok = receipt_valid(args.out)
        print("gate receipt: " + ("VALID" if ok else "MISSING OR STALE - run `gate` again"))
        return 0 if ok else 1

    if args.cmd in ("verify", "gate"):
        ok, problems = (gate if args.cmd == "gate" else verify)(args.out)
        for p in problems:
            print(f"FAIL: {p}")
        print("visual playtest gate: " + ("PASS" if ok else "NOT PASSED - do not report the playtest done or ship"))
        return 0 if ok else 1
    if args.cmd == "analyze":
        # Print only. A verifiable stamp (results.json + checklist.md) may come from `run` alone, otherwise
        # frames copied from an old build could be re-stamped and pass.
        results = analyze(args.out, use_ocr=not args.no_ocr)
        for it in results["items"]:
            print(f"[{it['auto']:5}] {it['title']} - {it['detail']}")
        print("\n(analyze writes nothing; only `run` produces a checklist that `verify` accepts)")
        return 1 if any(i["auto"] == "FAIL" for i in results["items"]) else 0

    steps = load_sequence(args.sequence)
    if args.target == "device-host":
        if not (args.remote_zip and args.game_name):
            ap.error("--target legion needs --remote-zip and --game-name")
        backend = LegionBackend(args.host, args.remote_zip, args.game_name, args.task_name, args.warmup,
                                probe=None if args.skip_probe else (lambda: legion_probe(args.host)))
    else:
        if not args.local_cmd:
            ap.error("--target local needs --local-cmd")
        backend = LocalBackend(local_argv(args.local_cmd), args.warmup, window=args.local_window, keyinput=args.local_input)
    try:
        results, checklist = run_gate(backend, steps, args.out, args.build or (args.remote_zip or " ".join(args.local_cmd or [])),
                                      args.video, args.frames, use_ocr=not args.no_ocr)
    except Exception as e:  # noqa: BLE001 - one clear line, exit 2 = the capture itself failed
        print(f"CAPTURE FAILED: {e}")
        return 2
    if args.vlm_judge:
        entry = attach_vlm_judge(args.out, results)
        print(f"vlm judge: {entry['status']}" + (f" ({entry['reason']})" if entry["status"] == "unavailable" else ""))
    return report(results, checklist)


if __name__ == "__main__":
    sys.exit(main())

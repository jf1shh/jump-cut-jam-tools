---
tier: tested
source: stages/04_ship/references/jam-clock.md
updated: 2026-11-10
---

# Jam hard-stop clock

`scripts/jam_clock.py` counts down to the deadline and writes marker files. Full detail: `stages/04_ship/references/jam-clock.md`.

## Why it exists

Mock 10 ran past its 07:00 PT hard stop because nothing enforced the time. An agent that is busy and
doing well has no reason to stop on its own. The clock gives it an order it can poll, so the stop does
not depend on the agent noticing the time.

## Poll `check` every loop turn

Run `python3 scripts/jam_clock.py check` each turn. The exit code is the order:

| Exit | Meaning | What to do |
|---|---|---|
| 0 | WORK | Keep working. This is the only "go". |
| 10 | FORCE_PACKAGE (T-60 min) | Stop feature work. Package and upload now. |
| 11 | FINAL (T-15 min) | Only itch page and text edits. No new builds. |
| 12 | EXPIRED, or the clock is unreadable | Stop. The deadline passed, or the agent cannot read the clock. |

`check` reads the clock itself, not just the marker files, so it is right even if the daemon died. It
fails closed: a wrong state dir (daemon and agent disagree on `JAM_CLOCK_DIR`) gives 12, not 0. `status`
prints time left.

## Starting it

Real kickoff: plain `python3 scripts/jam_clock.py start` (default deadline 2026-11-15 20:59 ET). For a
mock, pass `--deadline <ISO with offset>`. A plain `start` after a deadline that passed under 12 hours ago
is refused (exit 2) and writes the EXPIRED marker; it needs an explicit `--deadline` to begin a new run.
A deadline dead for more than 12 hours (a finished mock) is replaced by the contest close, with a warning.

## Rule: read the time from the clock, not from a handoff
- **Why:** mock 10's handoff files carried wrong clock times (21:50 against a real 22:08; `mock-jam-findings-10.md:43`).
- **How to check:** `python3 scripts/jam_clock.py status` or `date`.

## Rule: an early "done" is a failure
- **Why:** mock 12 declared itself finished twice with hours left: no sound, and a montage instead of a real clip (`mock-jam-findings-12.md:39,101`).
- **How to check:** until the hard stop, work the idle list. `jam_clock.py finish` is meant to refuse without sound, a real 30 to 60 s clip and a gate PASS.

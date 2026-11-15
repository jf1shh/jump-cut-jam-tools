# Jam clock

`scripts/jam_clock.py` enforces the contest hard stop. Mock 10 ran past its 07:00 PT stop; this is the fix.
It never touches the editor. It only counts and writes marker files.

## Run it

At kickoff (default deadline is the rules close, 2026-11-15 20:59 ET = 17:59 PT):

```bash
python3 ~/Projects/megajam/scripts/jam_clock.py start
```

For a mock, pass the mock's own stop: `start --deadline 2026-11-09T07:00:00-08:00`.
A new, different deadline clears old markers. `start` with no `--deadline`:
- stored deadline in the future: kept (a daemon restart).
- passed less than 12 hours ago: refused (exit 2, "pass --deadline"), so `check` keeps saying stop.
  Only an explicit `--deadline` starts a new run.
- passed more than 12 hours ago (a finished mock): replaced by the contest close, with a warning.
So the real kickoff is plain `jam_clock.py start`. The daemon also survives a half-written or
unreadable `deadline.json`: it keeps the last good deadline and retries next tick. Restarting with no `--deadline` (or the same one) keeps
the existing deadline and markers, so nothing is re-sent. `check` fails closed: if it cannot read the
deadline (for example the daemon and the agent use different state dirs) it prints EXPIRED and exits 12.
Set `JAM_CLOCK_DIR` the same way for both, or pass `--state-dir`. Time left on demand: `jam_clock.py status`.

State lives in `~/.local/state/megajam-jam-clock` (override: `--state-dir` or `$JAM_CLOCK_DIR`).

## What happens

| Time left | Phase | Marker | Order |
|---|---|---|---|
| > 60 min | WORK | none | normal |
| <= 60 min | PACKAGE | `FORCE_PACKAGE` | stop feature work; package + upload now |
| <= 15 min | FINAL | `FINAL` | only itch page / text edits |
| <= 0 | EXPIRED | `EXPIRED` | nothing more ships; the FINAL allowance is void too |

A late start in FINAL or after the deadline writes no FORCE_PACKAGE (its order is stale by then). Markers are JSON with the order in plain words.

## Nudging the running session

`SendMessage` is a tool inside a session, not a shell command, so the clock cannot call it directly.
Two paths:

1. **Poll (always works).** The agent runs `jam_clock.py check` on every loop turn. Exit 0 = ok,
   10 = force package, 11 = final, 12 = expired. It reads the clock, so it is right even if the
   daemon died.
2. **Push (optional).** Give a command that delivers a message; it gets the text on stdin and in
   `$JAM_CLOCK_MESSAGE`, runs once per marker, and its failure never blocks the marker:
   `start --nudge-cmd '<command>'` or `JAM_CLOCK_NUDGE_CMD`. Example: a small wrapper that touches
   the lead session's RESTART/inbox flag. The wrapper is not built yet.

## Line for the briefs (hub adds it)

> **Clock.** Every loop turn run `python3 scripts/jam_clock.py check`. On exit 10 (FORCE_PACKAGE):
> stop feature work and run package + upload now. On exit 11 (FINAL): only itch page and text edits.
> On exit 12 the deadline has passed, or the clock is unreadable: stop. Only exit 0 means keep working;
> any other code means stop feature work. Never argue with the clock. `jam_clock.py status` shows time left.

Tests: `python3 -m pytest tests/test_jam_clock.py`.

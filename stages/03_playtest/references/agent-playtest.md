# Agent playtest: play it like a human before the owner sees it

Owner, 2026-11-08: "i want an agent to play test it also like a human would before it comes to me."

`scripts/visual_playtest.py` (see `playtest-gate.md`) sends a blind key script. In mock 10 it never watered
a plant, so the win was never seen, and the lose-state camera loop was found by the owner. This tool closes
the loop: the agent looks at a real frame, decides, acts, looks again. Real OS input and real screen capture on
the Legion (the DPI-aware SendInput/capture scripts, PR #102).

## Gate rule

**No build goes to the owner until an agent playtester has, on the packaged Legion build:**
1. reached the **win** state by actually playing (look -> decide -> act),
2. **lost on purpose**, and
3. **restarted** after the loss,

with frames or clips as evidence for each, a filled report, and `agent_playtest_cli.py gate --report ...`
printing `GATE PASS`.

What the gate proves: real input was sent (at least 5 commands), the game was in front for every input, and
win / lose / restart were each marked with their own files, captured in this session after the first real
input (a title frame is not evidence), with the restart evidence captured after the lose evidence. Frames must
have been taken with the game in front; clips must have passed their video check (not black or flat) and been recorded with the game running and in front at both ends (`clip` takes a look frame before and after; if OBS or a dialog is in front, `press` a harmless key and clip again). The
latest usable mark per milestone counts, so a wrong mark can be fixed by marking again. If the game crashes,
run `start` again with the same zip: the history is kept and numbering continues (a `relaunch` is journaled).
Inputs that left the game out of front only block the gate in the run they happened in; a relaunch clears them.
A relaunch between the lose and restart evidence fails the gate: restart has to happen in the game.
`start --fresh` archives the old history into `archive-<time>/` instead; a different build needs a new session
folder. What it cannot prove: that a
frame truly shows a win. The tester states what it saw in the report, and the hub or owner spot-checks the
evidence frames. A PASS without a report that matches the frames is not a pass.

## The tester must play blind to the source

Act as a QA tester who just got the zip. Read **only** what the game shows on screen (title, instructions,
HUD). Do not open the game's source, the GDD, the brief or the autopilot/debug settings while playing. If the
on-screen instructions do not say how to win, that is a finding (Clarity), not something to look up. Never use
the game's own autopilot or a debug key.

## Commands

All from the repo root; one session folder holds everything (`--session DIR` or `$AGENT_PLAYTEST_DIR`).
Each look/press/mouse is one trip to the Legion and takes about 10 to 20 seconds. Not run from a ticket worker.

```bash
export AGENT_PLAYTEST_DIR=~/Projects/megajam/playtest-sessions/mockNN-$(date +%H%M)
S=~/Projects/megajam/scripts/agent_playtest_cli.py
python3 $S start --remote-zip 'C:\Dev\Game\Packaged\SilentBlade_Game.zip' --game-name Game
python3 $S look --label title            # prints a PNG path: Read that file, then decide
python3 $S press space                   # tap
python3 $S press w --hold 1.5            # hold 1.5 s
python3 $S press "a,w,d" --hold 0.4      # several keys, one after another (no chords: alternate to go diagonal)
python3 $S mouse --move 300 0            # mouse look
python3 $S mouse --click left --x 960 --y 540
python3 $S clip 20                       # 20 s OBS video of the live game (3-120 s); prints the mp4 path
python3 $S state --lines 40              # is it running + the end of the game log
python3 $S mark win --evidence frames/01_014_win.png --note "all 5 plants watered, banner shown"
# evidence paths are relative to the session folder (absolute paths work too); the PNG path
# printed by look/press is exactly what to pass. Re-marking replaces an earlier bad mark.
python3 $S gate --report $AGENT_PLAYTEST_DIR/report.md
python3 $S stop
```

`press` and `mouse` always finish with a screenshot and print its path, so the loop is: **Read the PNG ->
say what you see and what you will try -> one command -> Read the next PNG.** Use short holds (0.2 to 1 s) so
you see the effect of each move. A warning on stderr that the game was not the front window means the game
crashed, quit or lost focus after the input (keys are only sent while it is in front): run `state`, report it
as a finding, then relaunch or redo that step. `clip` is for motion (camera loops, flicker, animation); it uses the
same OBS path as `legion_record.py`.

## Protocol (do these in order)

1. **Start and read.** `start`, then `look`. Read the title and instructions on screen only. Write down what
   you believe the goal and controls are before touching anything.
2. **Win by playing.** Look -> decide -> act until the game says you won. Do not skip steps by guessing; if you
   are stuck for 10 commands in a row, note it under Stuck and try something different. Take a `clip` of the
   winning moments if the win is an animation, and `mark win --evidence <frame> [clip]`.
3. **Lose on purpose.** Restart, then fail deliberately (run out the timer, walk into the hazard, do nothing).
   `mark lose --evidence ...`. Watch the lose screen with a `clip`: is the camera still, does it loop, can
   you tell why you lost?
4. **Restart.** Use whatever the game tells you to. Confirm the new run really starts clean (score, timer,
   positions). `mark restart --evidence ...`. If there is no on-screen way to restart, that is a finding.
5. **Poke the edges.** Run into walls and corners, jump or move off the map if possible, spam each key for a
   few seconds (`press "space,space,space,space,space" --hold 0.05`), mouse-spin, press `esc`, and idle 30 s
   (`clip 30` with no input) to check for timers, drift or crashes. `state` after each to see if the game is
   still alive and what the log says.
6. **Note** confusing controls, unclear goals, stuck spots, visual glitches (each with the frame or clip name),
   then score Fun and Clarity 1 to 5 and write the report from the template below.
7. **Gate.** `gate --report report.md`. Fix the gaps it names. Then `stop`.

Mock briefs should carry a one-line pointer to this file (the hub adds it after T-20261108-10 merges).

## Report template

Copy to `$AGENT_PLAYTEST_DIR/report.md` and fill every `<fill>`. Section names and the two scores are checked
by the gate. Name evidence by file name.

<!-- report-template -->
```markdown
# Verdict
<fill: one line. Would you hand this to the owner? yes / no and why>

# Build and run
Build: <fill: zip name, date>. Session folder: <fill>. Commands used: <fill: roughly how many>.

# Win
<fill: what the screen told me the goal was; what I did; how I knew I won. Evidence: frame/clip names>

# Lose
<fill: how I lost on purpose; what the lose screen showed; was it clear why. Evidence>

# Restart
<fill: how I restarted; did the new run start clean. Evidence>

# Edges
<fill: walls, spamming keys, esc, off-map, idle 30 s. What happened each time>

# Confusing
<fill: controls or goals I misread, with what the screen said at that moment>

# Stuck
<fill: any spot where I could not progress, and how I got out. "none" if none>

# Glitches
<fill: visual or audio problems, each with a frame or clip name. "none" if none>

# Fun score
Fun score: N/5 - <fill: one sentence>

# Clarity score
Clarity score: N/5 - <fill: one sentence>
```
<!-- /report-template -->

## Real Legion run (for the hub; no Legion runs from the ticket)

1. `scripts/legion_preflight.py` passes (it is also called by `legion_record.py`). The packaged zip is on the
   Legion (`package-and-push.ps1`).
2. Run the command block above in a fresh Claude session at the repo root (one agent, so the "one GPU / one
   Legion driver" rules hold; do not run `visual_playtest.py` or `legion_record.py` at the same time).
3. Expected first-run risks, in order of likelihood: OBS slow to start for the first `clip` (up to 90 s, it
   waits); the Legion screen locked or asleep (frames show the lock screen: wake it, rerun `look`); a visible
   console taking focus (the warning above); the game log path not found by `state` (it prints "game log not
   found", the rest still works).
4. After a PASS, the hub reads the report and opens at least the three evidence frames before saying the build
   goes to the owner.

## Files

- `scripts/agent_playtest_cli.py` - the commands and the gate. Reuses `visual_playtest.py` (`LegionBackend`,
  key table, input and capture scripts) and `legion_record.py` (OBS start, record, fetch, frame check).
- `tests/test_agent_playtest_cli.py` - fake-backed tests (no Legion).
- `scripts/agent_playtest.py` is a different thing (headless in-editor PIE steering); do not confuse them.

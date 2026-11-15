# 05 Agent playtest and visual check

**Purpose:** an agent plays the packaged build the way a player does (real OS input, real screen capture), looks at the
frames, and reports what it saw. Not a log grep and never the game's autopilot.
**When:** on every package that reaches the Legion (`07-package-and-ship-check.md` step 6), and when the lead needs a fresh
look at the state of the build. Editor-side looks after each step use `mx.py shot` or `step_shot.py` (lead only).
**Lead sends to:** a playtest agent (not the writer of the code being tested). The agent uses the Legion over ssh, not
Unreal MCP. One Legion job at a time.
**Model:** Sonnet. A second pass as a judge (`judge_pass.py`) uses a different Sonnet or an Opus agent.
**Not agent-testable:** the Legion's built-in gamepad. The agent sends keyboard and mouse only; the owner plays the pad
and the report must say "pad: owner only".

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{build}` | the build id or commit tag (from `legion_ship.py`'s summary) |
| `{remote_zip}`, `{game_name}` | the packaged zip on the Legion and the game's exe name |
| `{session_dir}` | `AGENT_PLAYTEST_DIR`, e.g. `{game_dir}/work/playtest/{build}` |
| `{focus}` | what to test first (the new slice's done-test) |

## Prompt

```text
{HOUSE_RULES}

You are the PLAYTEST agent for build {build}. You never call Unreal MCP and you never use the game's autopilot.
Read stages/03_playtest/references/agent-playtest.md and _config/reference/templates/playtest-checklist.md first.

Use python3 ~/Projects/megajam/scripts/agent_playtest_cli.py with AGENT_PLAYTEST_DIR={session_dir}:
  start --remote-zip {remote_zip} --game-name {game_name}
  look --label NAME           -> prints a PNG path: Read it, say what you see, then decide the next input
  press KEYS [--hold S]       real key presses; mouse --click/--move for the mouse
  clip SECONDS                OBS video of live play
  state                       tail of the game log
  mark win|lose|restart --evidence FILES...   only after you saw it happen in the frames
  gate                        exit 0 only if win, lose and restart are all evidenced
  stop

Play: first {focus}; then one full run start to end screen. Cover: title, a full scene, a crash and retry, pause,
restart, quit, and the theme being visible in the first minute. Use keyboard and mouse only; write "pad: owner only".
After EVERY look, write one line of what is on screen. Flag: grey grid floor, placeholder shapes, debug text or
print-to-screen text, unreadable HUD, a black or frozen frame, a camera that jitters, a soft lock.
If the game closes by itself, copy the Legion logs and stop; hand to 06-bug-crash-triage.md.

Finish with `gate`. If a checklist needs a verdict file, use
python3 ~/Projects/megajam/scripts/visual_playtest.py (run, then verify and gate) and set each verdict only after
Reading the contact sheets. Do not pass anything you did not look at.
```

## Done when

`agent_playtest_cli.py gate` exits 0 with real frames behind win, lose and restart, or the report says exactly which
step failed and shows the frame.

## Reply format

House format, plus `Build:`, `Gate: PASS | FAIL`, `Seen:` (up to 8 lines, frame path then what it shows), `Bugs:` (each
`severity - what - frame or log path - repro steps`), `Not tested:` (pad, anything skipped).

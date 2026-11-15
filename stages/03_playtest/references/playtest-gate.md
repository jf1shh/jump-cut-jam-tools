# Visual playtest gate

**Required before any mock jam (and the real entry) is called "done".** Owner, 2026-11-08 (T-20261108-05).

Why: mock 10 passed a "plays to win" gate that was a PIE log grep driven by the game's own autopilot. The
packaged build was a grey grid floor with placeholder primitives, PrintString text and water going negative.
The agent must look at the game, played with real input.

Three visual tools, three moments (plan: `stages/00_prep/references/mock-jams-10-14-plan.md`):

| When | Tool |
|---|---|
| Before importing each asset | `scripts/asset_preview.py` (T-20261108-07) |
| After every build step and import | `scripts/step_shot.py` (T-20261108-06) |
| Final gate on the packaged build | `scripts/visual_playtest.py` (this page) |

## What it does

1. Launches the PACKAGED build (Legion: existing `legion_playtest.deploy_and_register` + the game task).
2. Plays a scripted sequence of REAL OS input. Legion: `scripts/visual_playtest_input.ps1` runs in an
   Interactive-logon scheduled task (the console session that owns the display) and calls user32
   `SendInput` with scan codes. Local Linux build: `xdotool`. Never the game's own autopilot.
3. Saves a PNG at every `shot` step (frames right after an input are tagged `after_input`), plus
   `manifest.json`. Optionally pulls N more frames from a `legion_record.py` mp4 (`--video F --frames N`).
4. Runs cheap automated checks and writes `checklist.md` + `results.json` next to the frames.
5. You READ the contact sheets (Read tool, one image each), write a verdict per item and per step, then `gate`
   is the gate (see "Reading the run: 2 images, no blank verdicts" below).

## How to run

```bash
# Legion (default): zip must already be on the Legion, same as legion_playtest.py
~/Projects/megajam/scripts/visual_playtest.py run --remote-zip 'C:\Dev\Game\Packaged\Game.zip' --game-name Game --out /tmp/vp-mock11
# Local packaged Linux build (X11/XWayland only)
~/Projects/megajam/scripts/visual_playtest.py run --target local --local-cmd ./Packaged/Linux/Game.sh --out /tmp/vp-mock11-local
# after reading contact_steps_1.png + contact_steps_2.png and setting every "Verdict:" line in /tmp/vp-mock11/checklist.md
~/Projects/megajam/scripts/visual_playtest.py gate /tmp/vp-mock11   # the ship/findings step; `verify` = same check, no receipt
```

Run it from the project, with the editor closed if the GPU gate says so. Keep `--out` outside the repo, or
copy the folder into the findings if the owner wants the evidence kept.

The default sequence presses W, D, Space, left-click, moves the mouse, waits ~25 s, then presses R
(restart). Games with other controls: pass `--sequence steps.json` (array of
`{"op":"wait","seconds":2}`, `{"op":"shot","label":"x"}`, `{"op":"key","key":"w","hold":1.5}`, `{"op":"key","keys":["space","d"],"hold":4}` (held together),
`{"op":"click","button":"left","x":960,"y":540}`, `{"op":"move","dx":300,"dy":0}`). Key names are in
`KEYS` in `visual_playtest.py`: a-z, 0-9, arrows (`up` `down` `left` `right`), `space`, `enter`, `esc`, `tab`,
`shift`, `ctrl`. Any other name is refused before the game is deployed. `alt` is refused with its own message:
a bare Alt tap opens the AMD overlay on the Legion and covers the frames, so the input script never sends one
(it also no longer taps Alt to win focus; it shares the foreground window's input queue instead). The PowerShell table must equal
that list (a test checks it). The sequence MUST reach a win or lose screen and then restart, or items 6 and 7 cannot pass; add a
`shot` labelled `restarted` after the restart so the restart check can compare it with the first frame.

## Reading the run: 2 images, no blank verdicts (T-20261108-21)

Why: in mock 11 the agent Read 15 playtest PNGs one by one (~2.6K tokens each, ~40K context), wrote no
Verdict lines, never ran `verify`, and still reported the playtest done (harness verdicts were input PASS,
HUD WARN, restart WARN, win/lose AGENT). Three changes close that:

1. **Step contact sheets.** `run` writes `contact_steps_1.png`, `contact_steps_2.png`, ... : the still frames
   (bursts excluded; they keep their own `contact_<label>.png`), 8 per sheet in 4 columns x 2 rows, each tile
   labelled with the step number, label and time (`03 AFTER_W t=12.4s`). 15 frames = 2 image reads. Read a
   single PNG only when a tile is unclear. Sheets are hashed into the run stamp like the burst sheets.
   The burst sheets need a look only when the motion item is not PASS.
2. **A verdict stub per step.** `checklist.md` has a "Step review" section after the 8 items, one block per
   still frame, prefilled with the harness verdict for that frame: the worst Auto of the items that list it
   (`FAIL` > `WARN` > `AGENT` > `PASS`); a frame no item lists is `PASS` if it decoded. After looking, replace
   `AGENT`, `WARN` or `FAIL` with `Verdict: PASS` or `Verdict: PASS (reviewed: <why>)`, or `Verdict: FAIL - <why>`.
   A step whose Auto is FAIL (from `results.json`) can only pass with `(override: <why>)`.
3. **`verify` is stricter and `gate` exists.** `verify` fails when any item or step verdict is blank, still
   `PENDING`, an unresolved `AGENT`, or anything not starting with `PASS`; it also fails if a step block or the
   Step review heading was deleted.

`visual_playtest.py gate <out>` is what the ship / findings step calls. It runs `verify`, exits 1 until it
passes, and says "NOT PASSED - do not report the playtest done or ship". On PASS it writes `<out>/gate.ok`
(run id + checklist hash); on any failure it deletes an old `gate.ok`, and a new `run` clears it. A ship step can
check the receipt with `gate <out> --check` (exit 0 only if `gate.ok` matches this run and the current
checklist hash and `verify` still passes), or just call `gate` again. This stops a session claiming "done" without verdicts, but it
cannot prove the sheets were looked at: the verdict text is the agent's word, so write what you saw.

Not yet checked on real captures: the label font and the tile size on 1920x1080 frames (tested with 160x90
synthetic frames only).

## Trap: `montage` of more than 12 frames splits into `-0` / `-1` files (mock 11, seen once)

A `montage` of more than 12 frames split into `-0` and `-1` files in mock 11 (seen once, not re-tested): look for
both files. Details: `_config/reference/canon/jam-mcp-mock11-unconfirmed-traps.md`.

## Idle bursts: catching motion that stills miss (T-20261108-10)

Why: the mock 10 packaged build, left in OUT OF WATER, looped (camera falls toward the floor in ~1 s, snaps
back wide, repeats). The gate judged 4 still frames and passed it. Evidence:
`~/Projects/megajam/work/legion-video/` (`legion_screen.mp4`, `contact_sheet.png`, `mid_5frames.png`).

A `burst` step takes N frames over S seconds with NO input (`{"op":"burst","label":"lose","seconds":3,"frames":12}`;
frames 10..60, seconds 1..30, labels letters/digits/`-`, unique). Frames must be at most 0.3 s apart
(`seconds/frames <= 0.3`); a wider spacing can land on the same phase of a ~1 s camera loop and show it as
still, so the sequence is refused. The same limit is applied to the CAPTURED times: `analyze` averages the real
`t` gaps of each burst and FAILs the motion item ("frames too slow to judge motion") above 0.3 s + 25%, because
the Legion's per-frame capture (CopyFromScreen + PNG save) can be much slower than requested. If that happens,
the gate cannot judge motion on that machine: capture faster, do not override.

End states are declared: the sequence must contain one `{"op":"declare","end_states":["lose"]}` (`"lose"`,
`"win"` or both, whichever screens the game has). Each declared state needs a burst tagged
`"end_state":"lose"` (or `"win"`) that is immediately followed by an input step (no wait or shot between, so the
burst samples the end screen itself), and the last capture before the restart key must be such a burst. A
sequence is also refused without a shot labelled `restarted` after the restart key and a burst after it.
`analyze` applies the same rules to the captured order: a declared end state with no burst, a last capture
before the restart that is not an end-state burst, or no after-restart burst makes the `motion` item FAIL
(never skipped). `run` takes the declaration from the sequence; a standalone `analyze` assumes `lose`.

The default sequence declares `lose` and has three bursts: `midplay` (before any input), `lose` (after the long
wait, last capture before the restart key) and `afterrestart`. A game with a win screen too: pass your own
`--sequence` that declares both, e.g. play to lose, `burst` (label `lose`, `end_state` `lose`), press restart,
play to win, `burst` (label `win`, `end_state` `win`), press restart, shot `restarted`, `burst` `afterrestart`.
Burst frames are saved as `NN_burst_<label>_NN.png` and are kept out of the input, restart and HUD checks.

Checks (grey-level change, 0-255, between 64x36 thumbnails of consecutive frames):
- FAIL if the mean step is above 4.0, any single step is above 12.0 (a snap-back or respawn cut), or the last
  frame differs from the first by more than 15.0 (the view slid away). The mock 10 loop measured 15-20 per step.
- WARN above a mean step of 1.5 (something animates on its own, such as water): read the sheet.
- FAIL if a burst has fewer than 10 readable frames, or if the run has no burst at all.
- `run` writes `contact_<label>.png` per burst (5 columns, capture order, left to right then down, dark-magenta
  gaps). READ it: the same view should repeat in every tile. Sheets are hashed into the run stamp.
Tune the limits at the top of `visual_playtest.py` (`IDLE_*`). An ambient-animation game that trips the FAIL
can pass only with `Verdict: PASS (override: <why>)` after you read the sheet.

Capturing with OBS instead: record the idle seconds with `legion_obs_record_test.ps1` (stages/04_ship/references/capture-setup.md),
pull frames with `--video F --frames N`; those go to `video_frames/` and are for reading only, the motion check
uses the burst.

Reusable: `visual_playtest.py` is importable. `analyze(dir)` on any folder with a `manifest.json` whose entries
carry `burst` and `burst_index` returns the `motion` item; `scale_rgb(read_png(f), w, h)` and
`write_contact_sheet(tiles, path)` build a sheet from any frame files, so `step_shot.py` or the agent
playtester can call them.

Real run (hub, on the Legion; this ticket ran nothing there): the normal `run` command above. The default
sequence now takes ~15 s longer. Then Read `contact_midplay.png`, `contact_endstate.png`,
`contact_afterrestart.png` and judge item 8. Not yet confirmed on real hardware: `burst` in the PowerShell
script (capture rate of `CopyFromScreen` at the Legion's resolution; if a frame takes over 0.25 s the burst
simply runs longer, the frame count stays the same).

## The checklist (8 items)

1. Frames are real captures (not black, flat, undecodable). **Auto: yes.**
2. Real level, not the default grid or an empty room. Auto: warns if frames are mostly grey.
3. Player and goal objects visible and readable. Agent only.
4. Input visibly moves the player. **Auto:** a frame after an input must differ from the frame before it
   by at least 2.0 AND by at least 1.5x the idle change (start vs idle shot, no input), so a game that
   animates on its own but ignores input fails. FAIL if no input beat that; WARN if there is no idle shot.
5. Proper HUD, no debug text. **Auto:** warns on PrintString-blue / warning-red pixels in the top-left, and on
   debug words (`PrintString`, `LogBlueprint`, `Hello`, `Accessed None`, ...) found by OCR when `tesseract`
   is installed (`--no-ocr` to skip).
6. A win or lose screen is reachable. Agent only.
7. Restart works. Auto: the `restarted` frame should look like the first frame (difference <= 12) AND
   differ from the frame just before the restart (>= 2.0), so a frozen game or an ignored restart key FAILs.
8. Idle stability: with no input the view holds still. **Auto: yes**, from the idle bursts (section above). FAIL
   on a looping or falling camera, flicker or respawn spam; read each `contact_*.png`.

Shots whose label contains `restart` are left out of the item 4 movement check (the restart key reloads the
level; only the play keys, mouse and clicks may prove input works). The item 7 restart check uses the same
idle-baseline bar as item 4. `analyze DIR` only prints; it writes nothing, so it cannot re-stamp old frames.
Only `run` produces the `results.json` + `checklist.md` that `verify` accepts.

Scaled displays: the input script calls `SetProcessDPIAware` before it reads the screen bounds. Without that,
a 125%/150% display makes `CopyFromScreen` crop the picture to a corner (seen on the Legion in the real mock 10
playtest). A test pins the call before `CopyFromScreen` in both this script and `scripts/legion_screenshot.ps1`.

Focus: on the Legion the input task runs hidden (`-WindowStyle Hidden`), brings the game window to the
front before every key, click and move, and stops with an error if it cannot (input goes to the foreground
window). Each shot records whether the game was in front; a shot with the game behind something else
FAILs item 1. Local runs check every `xdotool` exit code and use X key names (`Escape`, `Return`, ...).
A stray console window holding focus (mock 11, gap 19): the focus step tries 6 times and, from the second try,
minimises every other window first. If it still fails, the error names the window title that kept focus.

Lock and black-screen probe (mock 11, gaps 14, 21, 34): on the Legion, `run` takes one probe shot before it
deploys anything. A `LogonUI.exe` process, or a probe with fewer than 50 distinct colours, stops the run at once
with one line: `CAPTURE FAILED: Legion is locked: unlock it by hand ...` (exit 2), never 47 black frames.
`legion_capture_screenshot.py` and `legion_record.py` do the same (`legion_record.py` adds that OBS cannot start
on a locked console). Cold start (gap 15): the default `--warmup` is 30 s, and after it the probe repeats every
10 s while the screen is still black, up to 90 s. Still black then: `capture is black: re-run once before
suspecting the build`. One black run happened once (gap 34) and the straight re-run gave real frames, so re-run
once before blaming the build. `--skip-probe` (`--skip-lock-check` for the screenshot script) turns it off.

Stale results cannot pass: `run` first deletes the old frames, manifest, results and checklist; `results.json`
stores a run id and SHA-256 of the manifest and every frame, and `verify` refuses a checklist whose run id or
files differ. `verify` reads each `Auto:` value from `results.json`, never from the editable checklist.

The auto result is a hint, never the verdict. In `checklist.md` replace every `Verdict: PENDING` with
`Verdict: PASS` or `Verdict: FAIL - <why>`. An item whose Auto is FAIL can only pass with
`Verdict: PASS (override: <why>)`.

## What passes

`visual_playtest.py gate <out>` (same rules as `verify`, plus the `gate.ok` receipt) exits 0 only when all 8
items AND every step say `Verdict: PASS`. Anything else (blank, pending, AGENT, WARN, FAIL, edited headings,
no checklist) exits 1. Capture failures (game would not start, input script
error, ssh down) exit 2 from `run` with one line saying why, and count as a failed gate.

Exit codes of `run`: 0 = captured, no auto FAIL (judging still pending); 1 = captured, an auto check FAILED;
2 = capture failed.

## Not verified yet (read before trusting it)

Built and unit-tested with fakes only (`tests/test_visual_playtest.py`: synthetic PNGs, fake ssh/scp, fake
xdotool/ffmpeg). **Not run against the real Legion or a real game.** Untested on real hardware:
- `visual_playtest_input.ps1` (SendInput scan codes, `CopyFromScreen` in the console session, task quoting).
  First real run on the Legion is the test; if a game ignores scan-code input, note it in the findings.
- The Legion backend uses its own ssh options and a polite-close step modelled on `legion_record.py`
  (T-20261108-04, PR #99, not merged when this was written). After #99 merges, `--video` takes its mp4 and
  the close step can be swapped for `legion_record.close_process`.
- The local backend (`xdotool` + `ffmpeg x11grab`) works on X11/XWayland only and was never run on a game.
  Mock 15 found that a full-root `x11grab` on KDE Wayland is pure black, so the local backend now grabs one
  window: `--local-window NAME` (largest window `xdotool search --name NAME` finds; grabbed by `-window_id`,
  one focus click before the first input) and `--local-input {xdotool,uinput}` (`uinput` sends evdev key
  codes through `/dev/uinput`, which Wayland apps also see). See `stages/00_prep/output/mock-jam-findings-15.md` for the
  first live result.
- Screenshots come from the screen, so the game must be on top and not minimised, and the Legion locked
  screen or a notification can ruin a frame; the capture check usually catches that.

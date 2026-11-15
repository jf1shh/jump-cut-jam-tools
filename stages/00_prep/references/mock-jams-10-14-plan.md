# Mock jams 10-14: balloon week plan (T-20261107-03)

> **Rescheduled overnight (T-20261107-04, 2026-11-07).** Owner, 2026-11-07 16:49Z: "lets pause the mock jam
> to run overnight because i actually want to work on multiple things during the days". The mocks now run
> 21:00 PT to 07:00 PT, so days stay free. Only four nights exist before the window, so mock 12 also carries
> gap 5c and mock 13 (liquid metal) is a **reserve, dropped unless the owner asks**. Layout picked by hub 26;
> the owner can override. Rule 7(h) text is unchanged.

Owner 2026-11-07: the next five days are jam prep, run as five mock jams, each with a different balloon
(inspired by the MegaJam 2026 page art: translucent four-lobed balloon "flowers"). Hub 25 picked #5.
Docs only: this ticket does no Unreal work. Window opens Wed 2026-11-11 21:00 PT (Rule 4).

| Mock | Balloon | Brief | Readiness gap it must prove |
| --- | --- | --- | --- |
| 10 | Water | `mock-jam-10-brief.md` | 1c + 6d: editor launches from the real jam loop |
| 11 | Helium | `mock-jam-11-brief.md` | 2b + 6c: MCP read-only call, Editor Toolsets listed |
| 12 | Slime | `mock-jam-12-brief.md` | 2c: editor-restart recovery, cook with MCP plugin on; plus 5c: desktop video capture (folded in from mock 13) |
| 13 | Liquid metal | `mock-jam-13-brief.md` | **RESERVE, no slot.** Was 5c; runs only if an earlier night fails a gate and the owner asks. Dropped otherwise. |
| 14 | Twisted balloon art | `mock-jam-14-brief.md` | 5a: real butler target; then 6a: `pre-jam-tooling` tag |

Gap IDs are the rows of `stages/00_prep/references/jam-readiness-2026-11-06.md`. Rows already PASS need nothing. 3d (butler
login) is re-checked by the owner on Nov 11 morning. 6b (EULA 22) is owner-only, see below.

## Rules for every mock

- **Rule 7(h):** every mock runs in the throwaway `~/Projects/megajam-mock` area, and that area is
  deleted after the findings are merged. Nothing made in a mock (gameplay, levels, art, audio, code
  that is game logic) may be reused in the real entry. Only tooling fixes and findings docs come back
  to this repo. Every brief says this again.
- **Overnight rules:** the owner starts each loop before bed (`HANDOFF_MAX_RESTARTS=300 proj start
  megajam-mock`, owner-only, unchanged). The night's lead agent must not block on an owner ask: log it in
  the findings doc and keep going. The hub sends a phone alert only for a blocker that stops the whole mock.
- Time box: target 8-10 h wall clock, hard stop at 10 h (07:00 PT). That includes the Legion package, the butler
  push to `jf1shh/megajam-pretest` (channel `win64`), a 30-60 s video, and the findings doc. If the box
  runs out, package what exists and write the findings anyway. A gate that is not reached is a FAIL.
- **Visual playtest gate, REQUIRED before "done" (owner 2026-11-08, T-20261108-05).** Mock 10 shipped a build
  that was "not a playable game at all" (grey grid floor, placeholder primitives, PrintString text, water going
  negative) because its "plays to win" gate was a PIE log grep with a demo autopilot. Now every mock runs
  `scripts/visual_playtest.py` on the packaged build (real OS input, never the game's autopilot), reads the
  extracted frames, and marks every `checklist.md` item PASS or FAIL. No pass, no "done", no push of the
  build. How to run and what passes: `stages/03_playtest/references/playtest-gate.md`. Each brief's gate list carries this line.
- **Short-clip motion check, part of that gate (owner 2026-11-08, T-20261108-10).** Four still frames passed
  mock 10 although its lose state looped the camera (it fell toward the floor in ~1 s, snapped back wide,
  repeated; evidence `~/Projects/megajam/work/legion-video/legion_screen.mp4`). The playtest now records a ~3 s,
  12-frame no-input burst mid-play, in each end state (lose, win) and after restart, builds a contact sheet per
  burst, and the `Idle stability` checklist item FAILs on a looping or falling camera, flicker or respawn spam.
  Read every `contact_*.png`. Each brief's gate list carries this line.
- **Agent playtester plays like a human before the owner sees a build** (T-20261108-11,
  `stages/03_playtest/references/agent-playtest.md`): it must reach the WIN state by real play, lose on purpose, and restart, with
  frames and clips as evidence. Each brief's gate list carries this line.
- **Screenshot and look after every asset and every build step (owner 2026-11-08).** Checking only at the
  end is how mock 10 went wrong. Three tools, three moments:
  - `scripts/asset_preview.py` for every asset, a close look at it BEFORE import (T-20261108-07).
  - `scripts/step_shot.py` after every build step (level, lighting, HUD, gameplay change) and right after each
    import: an editor viewport or PIE frame through Unreal MCP, framed on what changed (T-20261108-06).
  - `scripts/visual_playtest.py` as the final gate on the packaged build (above).
  Read every picture (Read tool on the PNG) and log a one-line verdict (`looks right` / `wrong: <why>`) in the
  findings. Fix a "wrong" before the next step. The final playtest gate stays required on top of this.
  Until those two scripts are merged, take the shot by hand through Unreal MCP and still log the verdict.
- Licensed models only (see `AGENTS.md`): `krea-2-turbo`, `realesrgan-x4plus`, TripoSplat. One lead
  agent is the only Unreal MCP caller.
- The theme line in each brief is the "theme reveal". The lead agent reads it at T+0, not before.
- Findings go in `stages/00_prep/output/mock-jam-findings-1N.md` (N = 0..4 for mocks 10..14) on a normal ticket branch.

## One GPU job at a time

Between any two mocks, and between any two GPU jobs inside a mock, in this order:

```bash
lemonade unload
gpu-preflight   # must print "CLEAR — safe to start a large job."
```

Launch the editor and every generation job in its own scope (`AGENTS.md`, "One GPU workload at a time").
Never start a mock while the previous one still holds the GPU. When the mock's GPU work is finished
(editor closed, no generation running), restore Lemonade and check the gate again:

```bash
lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768
gpu-preflight   # should print BLOCKED again; that proves Lemonade is back
```

Never use 8192. Packaging happens on the Legion, so it does not hold the desktop GPU.

## Schedule (Pacific time)

| Slot | Start - hard stop | What |
| --- | --- | --- |
| Sat Nov 7 | 21:00 - 07:00 (Sun) | Mock 10 (water). Owner starts the loop before bed. |
| Sun Nov 8 | 21:00 - 07:00 (Mon) | Mock 11 (helium). Owner starts the loop before bed. |
| Mon Nov 9 | 21:00 - 07:00 (Tue) | Mock 12 (slime) + gap 5c: its 30-60 s video is made with the desktop capture path. Owner starts the loop before bed. |
| Tue Nov 10 | day | Free. Rules re-check against the Box PDF (Nov 10). Real itch.io page due by 17:00 (owner ask 1). |
| Tue Nov 10 | 21:00 - 07:00 (Wed) | Mock 14 (twisted balloon). Needs the real itch.io page by 17:00 (owner ask 1). |
| Reserve | none | Mock 13 (liquid metal). No slot: all four nights are used and the days are free. **Dropped unless the owner asks.** If 5c fails in mock 12, it is fixed by hand on Wed Nov 11, 07:00-10:30, like any other open gap. |
| Wed Nov 11 | 07:00 - 10:30 | Merge findings 10-14, fix doc/tooling gaps, check butler login, then `pre-jam-tooling` tag (owner). |
| Wed Nov 11 | 11:00 | Kickoff livestream. No GPU work. Concept on paper only. |
| Wed Nov 11 | 21:00 | Window opens. `HANDOFF_MAX_RESTARTS=300 proj start megajam`. |

Days stay free: no mock holds the GPU 07:00-21:00 PT. By 07:30 each morning Lemonade is restored with
`--ctx-size 32768` and `gpu-preflight` shows BLOCKED (see "One GPU job at a time").

Slack: each mock ends with 1-3 h unused on purpose. 07:00 PT is a hard stop. An overrun does not slide
into the day or into the next night: package what exists, write the findings, and drop the tail of the
schedule. Never overlap two GPU jobs. If a gap is still open after mock 14, fix it Wed morning by hand,
not by a 6th mock.

## Owner-only steps

An agent must not do these (sign-in, terms, unattended-run start, package installs).

| When | Owner step |
| --- | --- |
| Now | Check `proj path megajam-mock` resolves. If not, tell the hub; the loop cannot start for the mock until it does (or the hub gives you the `claude-loop` line to run in that folder). |
| Prep for each mock (before the loop starts) | Make the project with `python3 scripts/new-mock-project.py NAME ~/Projects/megajam-mock` (add `--dry-run` first if unsure). Write into the loop root itself, not a subfolder: the loop session is rooted at `~/Projects/megajam-mock`, and Claude Code loads `.mcp.json` only from the session root, so a subfolder copy would leave the lead agent with no Unreal MCP tools. It writes the `.uproject` with the jam plugins, `.mcp.json` for port 8010, the `GameFeatureData` cook rule in `DefaultGame.ini`, and the MCP port pin plus a named first level in `DefaultEngine.ini`. Safe to re-run; `--force` merges only its own keys. Then swap `megajam-mock/CLAUDE.md` to that night's brief and retire old `.handoff/*/HANDOFF.md` notes, so the loop does not resume the last mock. |
| Start of mocks 10, 11, 12, 14 (before bed, ~21:00 PT) | **Start the loop** for the mock: `HANDOFF_MAX_RESTARTS=300 proj start megajam-mock` (same shape as the real one, not a ticket worker). Then `proj list` shows it `busy`. |
| Before mock 11 | Nothing extra. Hub checks `gpu-preflight` first. |
| Mon Nov 9, during the day | Optional: `sudo pacman -S wf-recorder` for the desktop capture test (5c). It cannot be installed mid-night. Without it, mock 12 tests `spectacle` or `ffmpeg kmsgrab` only, and says so. |
| Mon Nov 9, before bed | Nothing extra for the screen. Owner 2026-11-07: the screen stays unlocked at night. Mock 12's early capture probe (5c) still proves the capture is not black. |
| By Tue Nov 10 17:00 | **Ask 1 (5a):** create the real itch.io entry project as a draft and tell the hub its `user/slug:channel`. **You decide the team name and game name** (`TeamName_GameName.zip`). The hub writes both into `stages/00_prep/references/jam-day-runbook.md` section 3. |
| Before Nov 11 | Accept **UE EULA update 22** in a browser (readiness 6b). |
| Wed Nov 11 morning | `ssh <device-host>`, then `butler status jf1shh/megajam-pretest:win64` still works (readiness 3d). Log in by hand only if it fails. |
| Wed Nov 11, after the last doc merge | Tag: `git tag pre-jam-tooling origin/master` then `git push origin pre-jam-tooling` (readiness 6a). Agents do not push tags. |
| Wed Nov 11, 21:00 PT | `HANDOFF_MAX_RESTARTS=300 proj start megajam`. Then `proj list` shows `megajam` busy. |
| After each mock | Review and merge the findings PR; confirm `~/Projects/megajam-mock` was deleted (or tell the hub to). |

## Coverage check (all open readiness items close by mock 14)

- 1c, 6d: mock 10. 2b, 6c: mock 11. 2c and 5c: mock 12. 5a: mock 14. 6a: final step after mock 14.
  Mock 13 is a reserve and not needed for coverage.
- Also still on the owner list, not mock work: 6b (EULA), team and game name (5b), runbook note on the
  restart cap (4c, already fixed in code), Rules re-check on Nov 10 and Nov 15.
- If 1c/6d FAILS in mock 10 (the guard blocks the loop's editor launch), stop that mock. The hub and owner
  fix the guard in the DAY after, so mock 11 still starts that night (Sun Nov 8 21:00), because 2b, 2c
  and 6c all need the editor to launch from the loop.

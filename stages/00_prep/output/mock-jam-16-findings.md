# Mock jam 16 findings (Polarity Flip, UE 5.9, Windows path on the Legion)

Brief: `stages/00_prep/references/mock-jam-16-brief.md`. Throwaway game in `~/Projects/megajam-mock/mock16` (PolarityFlip); nothing from it
comes back here (rule 7(h)), only tooling fixes and this doc. Times are PT, 2026-11-10/11. Unattended night run (owner
asleep), started by a side session of hub 81. Jam clock: `jam_clock.py start --deadline 2026-11-11T03:07:26-08:00`
(started 21:07:26).

## Result in one line
Grey-box loop (pull up to a steel plate, steer, push off, win at the goal plate, lose on spikes, lose off screen,
restart) proven in the 5.9 editor (PIE, test bots) at **21:21, 12 min after the editor came up**, no 5.8 fallback.
**Windows path proven up to itch:** packaged on the Legion with `C:\Dev\UE_5.9` (after a hub-approved engine file fix),
zip **370.2 MiB** without debug symbols, pushed to `jf1shh/megajam-pretest:win64` (build #2354706, processed). With real
Windows key input the packaged game works: **SPACE works** (mock 15's SPACE bug not seen), lose, win (SPACE+D held
together) and restart. The **visual playtest gate did NOT pass** (5 honest FAILs): a Windows Defender Firewall prompt
for the new `PolarityFlip.exe` covers the screen; it was not touched (Windows setting). Video and agent playtest
**OPEN** for the same reason.

## What was built (one Blueprint, primitives only)
- `BP_Game` (Actor, Tick) moves a magnet cube under a row of steel ceiling plates. Hold SPACE = pull (red) toward the
  nearest point of the nearest plate; release = push (blue) away from it. Force `2400 / (1 + (d/250)^2)`, gravity 900,
  A/D steer 450. Win = pulled onto the gold goal plate. Lose = spikes below, or off screen. R reloads `L_Magnet`.
- Fixed side camera, 2-line TextRender HUD (size 42, dark on a cream "fridge door"), readable in every shot.
- One master material `M_Steel` with 7 instances (Steel, Red, Blue, Goal, Spike, Pad, Door). Force No Precomputed
  Lighting on.
- Keys read with `PlayerController.IsInputKeyDown` every Tick (same as mocks 14-15) on purpose, to retest mock 15's
  SPACE bug on Windows.
- Physics was tuned first in a 60-line Python model (same equations); PIE matched it to 0.1 s (win 4.4 s, spikes 2.5 s,
  off-left 0.9 s).

## Proven in PIE (5.9 editor, bots; shots read by the builder; win sheet re-checked by the lead)
- auto1: rise, steer, WIN at t=4.4 s (gold magnet, "STUCK TO THE GOAL! YOU WIN"), restart.
- auto2: rise, push-off drop, LOSE on spikes ~2.5 s ("ZAPPED!"), restart. auto3: LOSE off-left ~0.9 s, restart.
- No bot: magnet idle on the pad for 5 s. Bots deleted, level saved, 36 actors, no dirty packages.
- `greybox_gate`: "grey-box loop proven at 21:22".

## 5.9 gate table
| Gate | Result |
|---|---|
| Editor launch (`launch-editor.sh`, 16G scope) | PASS, :8010 up 14.2 s after start |
| MCP toolsets / describe / `py` | PASS (`py` returns `5.9.0-0+UE5`) |
| `step_shot` viewport shots | PASS: shots 01-21 all first try, each read with a verdict (no realtime fix needed; `--pie` not used) |
| Blueprint DSL Write | PASS: accepted first try 3 times (incl. `while`, `/`, a newline in a string) |
| `force_save_level.py` live | FAIL on first run (2 new 5.9 bugs), **fixed and PASS live** after the fix (save + `--verify-only`, exit 0, VERIFIED, 36 actors) |
| Fallback to UE 5.8.4 needed | NO |

## Tooling findings
Fixed on branch `mock16-findings` (tests added, full suite passing):
1. **Sequences could not hold two keys at once** (the win needs SPACE held while steering with D). A key step may now
   give `"keys": ["space", "d"]`: pressed in order, held, released in reverse, in `visual_playtest.py` (xdotool and
   uinput) and in the Legion input script `visual_playtest_input.ps1` (parse-checked on the Legion: 0 errors).
2. `agent_playtest_cli.py press KEYS --together` holds the keys at once (same new step).
3. `force_save_level.py` save on 5.9: `AttributeError: 'Package' object has no attribute 'mark_package_dirty'`. Now
   uses it when present (5.8) and `Object.modify(True)` otherwise (checked live: the level shows in
   `get_dirty_map_packages`).
4. `force_save_level.py --verify-only` on 5.9: `ValueError: line 57: imports must be at the top level of the script.`
   (`import uuid` inside `run()`); now imported at the top. Both fixes re-run live: PASS.

5. **Debug symbols shipped** (see Windows packaging): `package-and-push.ps1` now moves `*.pdb`/`*.debug`/`*.sym`
   to `Packaged\Symbols` before the zip and push; `legion_ship.py` fetch skips them too (commit 64cd0c1).
6. **`legion_ship.py` exe check refused a good 5.9 build**: a content-only project packaged with `-build` on the 5.9
   source engine stages `PolarityFlip\Binaries\Win64\PolarityFlip.exe` and no `Engine\Binaries\Win64\UnrealGame.exe`.
   Either target now passes for content-only projects; the decoy rule stays (bafe125).
7. **Zip gate was 1 GiB, not 1 GB**: the first zip was 1023.8 MiB, under the old `1GB` (1024 MiB) gate but over
   1,000,000,000 bytes. `MaxBytes` is now 1,000,000,000 (6d23b6b).
8. `mx.py py` on 5.9 returns the value of the last expression; `print()` output goes only to the editor log.

Open (not fixed here):
9. PIE ran at ~30 fps in the editor and the magnet tunnelled through a plate (flew off the right side). Fixed in the
   game with fixed 1/60 s physics substeps and a 0.05 s frame cap. **Template note:** any Tick physics in a jam
   grey-box should substep; the model at dt 0.033 reproduced the bug.
10. The DefaultPawn sphere showed in the play area; the game hides the pawn in BeginPlay and puts a PlayerStart behind
   the backdrop. Worth adding to the grey-box template.
11. mock 15's `proof.py` read `mx.py py` output as JSON; since the mock 15 fix `py` prints the plain value, so the old
   proof script tagged every line "ERR" (fixed in the mock copy only).

## Time
- 21:07 clock start, 21:09:54 editor up, 21:14 materials, 21:15 level, 21:17 Blueprint, 21:21 loop proven,
  21:22 gate recorded, 21:25 force_save_level fixed and verified live.
- 21:47-21:49 package run 1 FAILED (missing IOS AutomationTool files); 21:58 hub OK for the file fix; 21:51 ship2 start.
- ~22:57 game compile done, 23:16 stage done (BuildCookRun 5076 s = 1 h 25 min, BUILD SUCCESSFUL), 23:20 zip 1023.8 MiB,
  23:21 ship2 stopped at the exe check (finding 6). 23:22 editor closed (idle-stable for ~1.5 h before that).
- 23:25 zip again without symbols: 370.2 MiB. 23:25-23:28 `legion_ship.py --from-step 3`: SHIPPED, build processed.
- 23:28-23:31 Windows visual playtest; gate NOT PASSED (firewall prompt). ~23:45 Lemonade restored, close-out.
- **Kickoff to first packaged build: 2 h 13 min** (21:07 to 23:20, zip made). Kickoff to first build on itch: 2 h 21 min.

## Legion engine fix (hub 81 OK, 21:58 PT)
**Package run 1 FAILED in 1.4 min** (21:47-21:49): UAT compiles the IOS.Automation script module and stops with
`error MSB3554: Cannot write to the output file "...\AutomationTool\IOS\uatobj\...\IOS.Automation.Properties.Resources.resources".
Could not find a part of the path 'C:\Dev\UE_5.9\Engine\Source\Programs\AutomationTool\IOS\Resources\GreenCheck.png'`.
**Root cause (jam-day risk):** `C:\Dev\UE_5.9\_build-logs\ue59_build.ps1` line 20 runs GitDependencies with
`--exclude=Mac --exclude=IOS --exclude=TVOS --exclude=Android --exclude=VisionOS --exclude=osx64`. That drops
dependency files UAT still needs to build its script modules, so **no BuildCookRun can run on that engine** until they
are back. The same exclude may break Android packaging (rule 1 allows Android) the same way. A fresh engine install for
the jam must not use these excludes, or must be checked with one BuildCookRun first.
Fix (hub 81 option A): both trees are 5.9.0 (`Build.version` identical: 5.9.0, Changelist 0, BranchName UE5; CL 0 on both,
so this does not prove the exact same commit). The 9 files missing under `Engine\Source\Programs\AutomationTool\` were
copied from `~/Projects/UnrealEngine-5.9` into the same paths, only where missing (none existed, none overwritten); the
sha256 read back on the Legion equals the desktop copy:

| Added on the Legion (under `C:\Dev\UE_5.9\Engine\Source\Programs\AutomationTool\`) | sha256 |
|---|---|
| `IOS\ExportOptions.plist.template` | f5baf42cbd8b14bb665dcd666c6fdf3e2c3115353e65e7798d56491c04ea7637 |
| `IOS\Resources\GreenCheck.png` | 9316c8705f14ea7733e2947aa58e65658f1aa5866b6fec43c5328d25f126abd8 |
| `IOS\Resources\GreyCheck.png` | 0324f4d83b39e5ec3cd3cac6ca9c21d929a514e2336b4afc52760cb88c94f68f |
| `IOS\Resources\SourceArt\GreenCheck.psd` | ba7243dea344f793ddbbeea06e6e33c121cb4160dd310f8d0c82cc436a7299a3 |
| `IOS\Resources\SourceArt\GreyCheck.psd` | a6429eafb5347092591967f364f4ec01aa9724adf333e3babeeaf7abc28d9fd7 |
| `IOS\Resources\SourceArt\IPhonePackagerIcon.pdn` | 2e72bf4daa4c3ab3cef8af3023077de2e582c293fd3d50c9c8f22f1db0cc447d |
| `IOS\Resources\SourceArt\IPhonePackagerIcon.png` | f00180e7d6c61e903bf20a65ca2e0222de43b8bc82134e1efb44da7776c67efb |
| `IOS\Resources\SourceArt\LowResIcon.pdn` | 0b8b7ef74c382c0148499e60946a619159f783d2a7191a1ac0960e96f54f1eb0 |
| `IOS\Resources\SourceArt\LowResIcon.png` | 272da911eeaa0c4ad6b1ad2b45a6131f2715227b74c6d4f56a57bbae8954f332 |

Revert (needs the owner's word): delete exactly these 9 files (and the then-empty `IOS\Resources` folder). Scratch
copies left in `C:\Dev\_ship\ios_fix.tar` and `C:\Dev\_ship\ios_fix\`.

## Windows packaging (UE 5.9 on the Legion)
- Run 2: `legion_ship.py ~/Projects/megajam-mock/mock16 --engine 'C:\Dev\UE_5.9'`. The game was compiled with `-build`
  (source engine), cooked and staged. **BUILD SUCCESSFUL**, BuildCookRun 5076 s (1 h 25 min): a jam-day cost that only
  the first package of a fresh engine pays (the Development game target is compiled from scratch).
- Staged size 3.3 GB: **`PolarityFlip.pdb` 2542 MB** and `PolarityFlip.exe` 329 MB. `package-and-push.ps1` zipped
  everything: 1023.8 MiB, passed the old 1 GiB gate by 0.2 MiB.
- Hub-approved repair, nothing deleted: the stage left as is, zipped again to
  `C:\Dev\mock16\Packaged\nopdb\SilentBlade_PolarityFlip.zip` with `--exclude=*.pdb *.debug *.sym`:
  **388,136,169 bytes (370.2 MiB)**, 0 pdb entries, sha256 `e562ad559a608e2a684bdf71388afd09e9236d6699d9a9a4d68e18ed01f66e04`.
- `legion_ship.py --from-step 3` (with fixes 5 and 6): exe check PASS, fetch skipped the pdb, butler pushed 747.24 MiB
  (29083 files, 152.94 MiB patch) to `jf1shh/megajam-pretest:win64`: **build #2354706 processed** (version 19).
  Log: `~/.local/state/megajam/legion_ship/mock16-20261110-232508.log`.

## Windows visual playtest (`work/vp16`, real Windows key input)
**Gate: NOT PASSED** (`visual_playtest.py gate`, exit 1, 5 FAILs; every verdict filled honestly after reading all 5
contact sheets). Blocker: a **Windows Defender Firewall "allow public and private networks to access this app?"
prompt for `PolarityFlip.exe`** sits over the centre of every frame. It was not answered (that changes a Windows
setting). Before the first key step the Legion's Claude app was in front; the game came to the front at the first key
step (`Assert-GameForeground`).
What the frames do show around the dialog (same sequence as `work/vp/seq.json`):
- SPACE held 1.5 s lifts the magnet from the pad up to the first steel plate (`15_after_space.png`): **the SPACE key
  works in the packaged Windows build.** Mock 15's SPACE bug (seen only via xdotool in the uncooked stand-in) did not appear.
- D then drops it onto the spikes: "ZAPPED! R = try again" (`16_lost.png`, lose burst steady).
- R: fresh start, magnet on the pad, "POLE: PUSH (blue)" (`29_restarted.png`).
- SPACE+D held together 6 s (the new `"keys"` step): "STUCK TO THE GOAL! YOU WIN" (`30_after_climb.png`, win burst steady).
- R again: fresh start (`43_restarted2.png`).
FAILs: item 1 (frames: dialog, wrong window first), item 7 (restart not provable by diff with the dialog over it),
item 8 (idle burst shows the Claude app; frames 0.54 s apart, limit 0.3 s), steps 01 and 02 (game not in front).

## Readiness table
| Row | Item | Status |
|---|---|---|
| 1a | `gpu-preflight` gate | PASS (CLEAR before the editor and before the Lemonade restore) |
| 1b | UE 5.9 binary on desktop | PASS |
| 1c | Editor start works | PASS (16G scope, :8010 in 14.2 s) |
| 1d | Lemonade restored | PASS: `Qwen3-Coder-30B-A3B-Instruct-GGUF` loaded ~23:45 PT, ctx 32768 read back from health |
| 2a | Unreal MCP config | PASS |
| 2b | MCP server answers (toolsets, describe, py) | PASS |
| 2c | `step_shot` | PASS (shots 01-21 first try) |
| 2d | `force_save_level.py` live on 5.9 | PASS after 2 fixes (FAIL on first run) |
| 2e | Editor idle stability | PASS (up 21:09-23:22, idle ~1.5 h, MCP still answered; peak 7.9 GB in a 16G scope) |
| 2f | Grey-box loop (`greybox_gate`) | PASS, 12 min after the editor came up |
| 3a | Legion reachable | PASS (ssh) |
| 3b | Same UE version on Legion | PASS (5.9.0 on both, `Build.version` identical; CL 0 so not commit-exact) |
| 3c | Legion engine can run BuildCookRun | FAIL then PASS: 9 IOS AutomationTool files missing (GitDependencies excludes); added with hub OK, revert listed above |
| 3d | butler found and logged in | PASS (PC butler) |
| 4a-4e | claude-loop / revive | not used this mock |
| 5a | itch page + butler push | **PASS**: `jf1shh/megajam-pretest:win64` build #2354706 processed |
| 5b | Under-1 GB zip | **PASS** after the symbol repair: `SilentBlade_PolarityFlip.zip` 388,136,169 bytes (first zip 1023.8 MiB, fails a strict 1 GB) |
| 5c | 30-60 s video | **OPEN**: not recorded; blocked by the firewall prompt (would be in every frame) |
| 6a | `pre-jam-tooling` tag | NOT TONIGHT (owner) |
| 6c | MCP plugin list | PASS |
| 6e | Legion visual playtest gate | **OPEN** (gate NOT PASSED, 5 FAILs, all from the firewall prompt / window focus) |
| 6f | Agent playtest (`stages/03_playtest/references/agent-playtest.md`) | **OPEN**: not run; same blocker |
| 6g | Mock 15 SPACE bug in the packaged Windows build | **NOT REPRODUCED**: SPACE lifts the magnet with real Windows input (frame 15) |
| 6h | No 5.8 fallback needed | PASS |

## Jam-day risks (new)
1. **Firewall prompt per new exe.** Windows asks once for every new exe name/path (`PolarityFlip.exe` here). The real
   entry's exe needs the **owner to answer it once on the Legion before the first playtest**, or every playtest frame,
   video and agent run is covered. Agents must never answer it. (A Shipping build may open no listening socket and so
   not ask; untested.)
2. **The 5.9 engine on the Legion was installed with GitDependencies `--exclude=IOS/Android/...`**, which broke UAT
   (see "Legion engine fix"). A fresh engine install must be checked with one BuildCookRun before the jam.
3. **The first package on a fresh source engine takes ~1 h 25 min** (game target compiled with `-build`). Package once
   early on day 1 so later packages are incremental.
4. **Development `-build` packages stage a 2.5 GB `.pdb`.** Fixed in the tools (finding 5); still check the zip size
   before every push (now a strict 1,000,000,000-byte gate).
5. Before a Legion playtest, make sure the game will be the front window from the first shot (the Legion's Claude
   app was in front for frames 01-14 here).

## Morning follow-up (needs the owner first)
1. Owner, at the Legion console: answer the Windows Defender Firewall prompt for
   `C:\Dev\mock16\...\PolarityFlip.exe` (the owner's choice; agents do not touch it).
2. Visual playtest (one Legion driver at a time):
   `python3 scripts/visual_playtest.py run --target legion --remote-zip 'C:\Dev\mock16\Packaged\nopdb\SilentBlade_PolarityFlip.zip' --game-name PolarityFlip --sequence ~/Projects/megajam-mock/mock16/work/vp/seq.json --out ~/Projects/megajam-mock/mock16/work/vp16b`,
   read every contact sheet, fill each `Verdict:`, then `python3 scripts/visual_playtest.py gate ~/Projects/megajam-mock/mock16/work/vp16b` (exit 0 needed).
   If frames 01-02 still show another window, add a key-free focus step or a longer first wait to the sequence.
3. Agent playtest: follow `stages/03_playtest/references/agent-playtest.md` with
   `python3 scripts/agent_playtest_cli.py start --remote-zip 'C:\Dev\mock16\Packaged\nopdb\SilentBlade_PolarityFlip.zip' --game-name PolarityFlip`,
   then lose (`press d`), restart (`press r`), win (`press space,d --together --hold 6`), mark each with evidence, run its gate.
4. Video: `python3 scripts/legion_record.py --remote-zip 'C:\Dev\mock16\Packaged\nopdb\SilentBlade_PolarityFlip.zip' --game-name PolarityFlip --seconds 45`;
   watch it and check 1920x1080 and 30-60 s.
5. Update rows 5c, 6e and 6f here and the scorecard row.

## Morning rerun on the Legion (2026-11-11, hub 82, owner said go at ~01:40 PT)
Branch `mock16-legion-rerun` off master fb32331. The Legion had rebooted at 00:15; **the firewall prompt did not come
back** (not seen in any frame; nobody answered it from this side). The owner's Claude app was in front at first; one
R key press brought the game to the front.
| Gate | Result | Evidence (`~/Projects/megajam-mock/mock16/work/`) |
|---|---|---|
| Agent playtest (`stages/03_playtest/references/agent-playtest.md`) | **PASS** (gate exit 0) | `agentpt/`: lose `frames/01_005_after-d.png` ("ZAPPED!"), restart `01_006_after-r.png`, win `01_007_after-space-d.png` (`press space,d --together --hold 6`), `report.md`, `gate.out` |
| Legion visual playtest (`visual_playtest.py gate`) | **PASS** (exit 0) with 5 overrides, each read from the frames | `vp16b/` (sequence `vp/seq2.json` = `seq.json` + an R press and 4 s wait before the first shot), `checklist.md`, `gate.out` |
| 30-60 s video (`legion_record.py`) | **OPEN**: preflight stopped on stale scheduled tasks `MJExplorer, MJKill, MJKill2, MJWin` (not `MJTool*`, so treated as the owner's); not removed, preflight not skipped | `video.log` |

Overrides in `vp16b` (said plainly, for the owner to judge): item 7 restart (auto diff 2.0 vs the end frame because the
magnet is a small cube; the frames show a fresh start), item 8 idle (auto FAIL is the Legion capture rate, 0.67 s between
frames vs a 0.3 s limit; all 12 frames identical, but flicker faster than 0.67 s cannot be ruled out), steps 01, 06, 07
(auto FAILs from those same diffs).
**SPACE on Windows, packaged, real keys: works.** `vp16b/15_after_space.png` was taken while SPACE was held: HUD
"POLE: PULL (red)", red magnet pulled up to the first plate. Mock 15's SPACE bug is not in the packaged Windows build.
New gaps: (1) `legion_record.py` sends no input, so even a clean run films the idle start screen, not gameplay; a rule-10
gameplay video needs input during the recording (e.g. a sequence-driven record). (2) Any look frame taken after a key is
released hides hold-to-act mechanics (agent report, "Confusing").

### Live gameplay-video run (2026-11-11 ~02:00 PT, hub 82 GO): FAIL, not caused by the new code
`legion_record.py --sequence vp/seq2.json --seconds 58` (commit 2817e34): preflight OK, then both takes failed with
`OBS websocket did not answer within 90s`; no mp4, no input task started (OBS fails before the recording, so the
`--sequence` path was never reached). Log: `~/Projects/megajam-mock/mock16/work/video2.log`.
**Root cause, read-only check on the Legion:** `%APPDATA%\obs-studio\plugin_config\obs-websocket\config.json` has
`"server_enabled": false` (port 4455, auth on). OBS started and closed again (logs 01:59 and 02:02); nothing left
running, no `MJTool*` task left. Not changed: it is a Legion/OBS setting.
**Owner action before the jam:** in OBS on the Legion, Tools > WebSocket Server Settings > Enable WebSocket server
(port 4455, same password as before), then rerun the command above. Until then the gameplay video gate stays **OPEN**
and `--sequence` is proven by unit tests only. **Jam-day risk:** the Legion reboot at 00:15 (or an OBS update) may have
reset this; check `server_enabled` in the preflight (`legion_preflight.py` could read that file; not done here).
- Rerun ~02:3x PT after the owner enabled the OBS websocket: OBS answered in ~3 s (fixed). Both takes then stopped at
  `legion_record`'s own guard: **no inbound firewall allow rule for PolarityFlip.exe** (the guard exists so the firewall
  prompt cannot spoil a video). No input was sent, no mp4. Log `work/video3.log`. Owner action, admin PowerShell on the
  Legion, once per exe (the stub the tool checks, and the real game exe the stub starts, which is the one that opens
  the network socket):
  `New-NetFirewallRule -DisplayName "MegaJam game" -Direction Inbound -Action Allow -Profile Any -Program "C:\Dev\mock16\Packaged\nopdb\agent_test\PolarityFlip.exe"`
  `New-NetFirewallRule -DisplayName "MegaJam game (inner)" -Direction Inbound -Action Allow -Profile Any -Program "C:\Dev\mock16\Packaged\nopdb\agent_test\PolarityFlip\Binaries\Win64\PolarityFlip.exe"`
  **Jam-day risk:** the real entry's exe path needs the same rule before its first video; plan it with the firewall
  prompt (risk 1).
- **Rerun ~02:21 PT after the owner added both firewall rules (Profile Private): the guard passed, video RECORDED.**
  `~/Projects/megajam-mock/mock16/work/video/2026-11-11 02-21-31.mp4`: 57.6 s, 1920x1080, 60 fps, 2.3 MB. Frames read
  (`video/frames/contact.png`): t=26-32 s level with HUD "POLE: PUSH (blue)", t=40 s "ZAPPED!" (lose), t=46 s fresh
  restart, t=54 s "STUCK TO THE GOAL! YOU WIN" (SPACE+D held together). **`legion_record --sequence` is proven live:**
  keys played during the recording and took effect.
  **Not submittable as is:** t=0-~22 s shows the OBS window (Display Capture of the desktop, OBS in front); the game
  came to the front only at the first key step (the input script's focus call). Fix before the jam (not done here):
  bring the game window to the front right after `StartRecord` (or start the sequence with a harmless key and no long
  first wait), and/or trim the head. Gameplay video gate: **PASS for "shows real play"; FAIL for "clean 30-60 s from
  the first frame"**; the owner should watch it.
- **Live take after the focus + trim fix (74c56c5), ~02:39 PT: PASS.** `legion_record --sequence vp/seq2.json --seconds 68`:
  cut 10.52 s of head; submission candidate
  `~/Projects/megajam-mock/mock16/work/video/2026-11-11 02-38-57_trimmed.mp4` (57.2 s, 1920x1080, 60 fps, audio),
  original kept beside it. Frames read (`video/frames2/contact.png`): t=0, 1, 2 s already the game (no OBS, no
  desktop); t=28 "ZAPPED!", t=36 "POLE: PULL (red)" magnet pulled up, t=43 "STUCK TO THE GOAL! YOU WIN", t=50 and
  56.5 fresh restarts. Notes: (1) t=0-~22 s is the game idle on the pad: the *sequence* (seq2) opens with 8 s + 5 s
  lead-in + waits; a jam video sequence should act within ~3 s. (2) Cut 10.52 s is just over `HEAD`=10; the tail still
  fit, but raise `HEAD` to 12 if a later take clips the end. (3) The small "Minimize"/"Close" boxes top right are stuck
  hover tooltips of the Legion's Claude desktop app (already in `agentpt/frames/01_001_title.png`, before any tool
  input), not drawn by the game or our tools; the owner can clear them by moving the mouse over the desktop (or closing
  that app) before the jam video. Not touched from here.

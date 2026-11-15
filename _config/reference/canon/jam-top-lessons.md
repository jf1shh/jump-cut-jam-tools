---
tier: tested
source: stages/00_prep/output/mock-jam-findings-10.md ... stages/00_prep/output/mock-jam-findings-15.md; stages/00_prep/output/mock-jam-16-findings.md; stages/00_prep/references/mock-scorecard.md; stages/00_prep/references/jam-execution-plan.md
updated: 2026-11-10
---

# Jam-day top lessons: the 15 rules that most change our odds

One screen, read before every work block. Each line is something a mock (10-16) actually hit. Ranked by how
much it cost us. F10 = `stages/00_prep/output/mock-jam-findings-10.md`, and so on. F16 = `stages/00_prep/output/mock-jam-16-findings.md` (folded in 2026-11-10).

## Tip: the rules, in order
1. **Packaged and playable by a person, early and every day.** Mock 10 took 11 h 38 min to a playable package; mock 11 did it in 2 h 57 min; mock 15 never packaged; mock 16 zipped in 2 h 13 min. The first package on the fresh 5.9 source engine takes ~1 h 25 min (later ones are incremental), so package once early on day 1. The plan's build #1 is Thu 16:00 (~19 h in): push a grey-box package to the private pretest page the first night too (overnight pretest pushes are allowed, plan ruling C6). (scorecard; F10; F15; F16)
2. **Real keys on the packaged build are the gate, not PIE bots.** Bot loops hid the SPACE/R bug; xdotool on XWayland drops or delays keys. Only real OS input on the packaged Windows build counts: mock 15's SPACE bug was not reproduced on Windows in mock 16 (a different game), so most likely the Linux input path. (F13; F15:12-15; F16)
3. **Keep the Legion unlocked all window.** `LockApp.exe` blacked out playtest, capture and video in mocks 11, 14 and 15. Owner disables the idle lock Wed 10:00. (F14:17; F15)
4. **Save to disk and prove it before every package.** Mock 10 lost 55 min to a SIGTERM and packaged a stale `.umap`. Run `scripts/force_save_level.py` (VERIFIED) first; on 5.9 it needs mock 16's two fixes (merged to master 2026-11-11). `save_assets` after every step. (F10:42; F16; `jam-force-save-level`)
5. **The package is not PIE.** Autopilot off, the real level, the real HUD; look at a packaged frame (mock 10 shipped a grey checker floor and stray Landscape). (F10)
6. **HUD readable on the packaged 1080p frame.** Win text clipped and low contrast in mock 11; use the backdrop box (`scripts/hud_text_box.py`), scale about 2.2, no PrintString. (F11:79; `jam-hud-readable-text`)
7. **The 5.9 Windows path works; keep it working.** Mock 16 shipped a 5.9 Win64 build to itch (pretest #2354706) with `--engine C:\Dev\UE_5.9`, after restoring 9 AutomationTool files that GitDependencies `--exclude=IOS...` had dropped. Keep `*.pdb` out of the zip (2.5 GB; cap is 1,000,000,000 bytes). Drop `TargetAllowList` on MCP before a 5.9 cook. Fork to 5.8.4 is still decided by Wed 15:00. (F16; `jam-packaging-windows`; `jam-legion-ship-preflight`)
8. **"Done" means sound, a real 30-60 s clip and a gate PASS.** Mock 12 stopped early twice without them. (F12)
9. **Editor survival.** Mock 12 lost 3 h to a stuck port 8010 and a modal from `BlueprintTools.create`. Timeouts on every wait; `ss -ltn | grep 8010` empty before relaunch; 5 s between editors. (F12:54)
10. **Gate integrity.** A rubber-stamped gate and identical contact-sheet tiles passed broken builds; read every frame and judge each item. (F12; F15)
11. **One human click for Windows prompts.** Every new exe name raises a Firewall prompt that covered every mock 16 playtest frame: the owner answers it once per exe before the first Legion playtest; make the game the front window before frame 01. Also the OBS update or crash dialog and the AMD overlay spoil captures; agents may not change firewall rules. Ask the owner, or use the X11 grab / `agent_playtest_cli clip` fallback. (F10:66-70; F11; F12; F16)
12. **Score lives in Fun and Level Design.** Judge pass went 19 to 20 of 35, and only Visuals moved; spend Saturday on mechanic, structure and sound. (F12:17,66)
13. **GPU gate is not sticky.** Lemonade reloaded itself next to the 5.9 editor; re-run `gpu-preflight` before each heavy job; restore with `--ctx-size 32768`. (F15; F14)
14. **Freeze and pin tools; wake on long waits.** A hub fast-forward changed scripts under a running mock (F12). A side session waiting on a long Legion job sat idle 1.5 h (hub, mock 16): wait with `waitfor`/Monitor and check sessions at each hub check-in.
15. **Know the 5.9 tool breaks.** Mock 15 hit `CaptureEditorImage` URN, `mx.py save`, `step_shot --pie`, `; quit`; fixed in tooling after (live-smoked 11-10). Prefer `HighResShot`, `save_dirty_packages`, `quit_editor()`. (F15; `jam-ue59-upgrade`)

- **Why:** each of these cost hours or a failed gate in a mock; most were caught late by the owner, not by a gate.
- **How to check:** at each gate build, read this list top to bottom and say yes or no to each line in the dev log.

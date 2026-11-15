# Mock-jam rehearsal findings — 2026-10-28/29

A fast rehearsal of the real MegaJam pipeline's *mechanics* (CLAUDE.md in this folder), made-up
theme "Overgrown", verb "Throw". "Compressed" and "overnight" describe the scope, not the clock:
the whole run spanned about 2 hours (7:06 PM–9:13 PM Pacific, 2026-10-28), across two
sessions/handoffs, and was built to prove each pipeline stage works end to end — not to rehearse
jam-week content pace or produce a realistic amount of game content. All 7 of CLAUDE.md's steps
were exercised in some form; the honest scorecard is below. Verified 2026-10-29: the packaging
claims below were cross-checked against the actual files left on the Legion Go S (zip byte count,
file timestamps matching the commit timeline) — this was a real pipeline run, not a shortcut.

## Stage timings and verdicts

| Stage | Verdict | Notes |
|---|---|---|
| UE project scaffold + GDD one-pager | Done | Content-only (Blueprint) project, no C++ target. |
| Headless UE cold boot + probe | Done, ~1-2 min once fixed | Was a 20+ min hang before the `-nullrhi -nosound` fix (see below). |
| Greybox build (`build_level.py`) | Done, seconds | Floor, player start, 3 vine targets, seed-pod prop, saved map. |
| Playable loop | Done, but simulated not human | Python state-machine playthrough only — see caveat below. |
| Asset pipeline (image → 3D → import) | Done, with retries | Image 151s. 3D stage flaked cold: attempts at 12.48s (exit 1), 58.04s (exit 1), then succeeded at 95.56s (exit 0) — one success after two failures, not two successes. UE import succeeded on first real attempt once the script existed. |
| Win64 packaging on Legion | Done, 28s cook, 374.6 MB zip | Broke twice on `.uproject` quirks before succeeding — see below. This was the pipeline's single biggest unknown going in (open question #14 in the real repo's knowledge base) and is now resolved. |
| OBS capture | Not done, correctly deferred | No display in this headless session; OBS isn't installed on this desktop by design. OBS 33.0.0 is on the Legion Go S but its setup wizard is stuck on a step that needs a GUI click — a real gap, not mock-specific. |
| Devlog | Done | `docs/dev-log-2026-10-28.md`, hand-written following the real repo's template (didn't run `gen_devlog.py` against the real repo, per instructions). |

## What worked

- The headless UE pattern (`xvfb-run` + `UnrealEditor-Cmd` + `-ExecCmds="py <absolute-path>"` +
  `-nullrhi -nosound -unattended -nosplash`) is solid once its two gotchas (below) are known.
  Boot, probe, greybox build and the simulated playthrough all ran reliably and fast on repeat
  launches.
- The local asset pipeline (Qwen-Image → Modly → UE Python import) works end to end and produced
  a real textured static mesh in the level's content, with no cloud calls anywhere.
- `package-and-push.ps1` from the real repo needed zero code changes — it's cleanly
  parameterized (`-EnginePath`, `-ProjectPath`, `-TeamName`, `-GameName`, optional `-ItchTarget`)
  and worked as-is once the project file itself was fixed.
- SSH + `scp` to the Legion Go S (Windows OpenSSH) works cleanly for project transfer and running
  PowerShell scripts remotely, once you know `C:\Users\<user>` is a usable path (not Windows'
  `/tmp`-equivalent, which doesn't exist) and that nested PowerShell `Start-Process` through two
  layers of shell quoting is fragile — running the script directly over `ssh` (not wrapped in a
  backgrounded `Start-Process`) is simpler and gave real error output immediately instead of
  silent empty logs.

## What broke / had to be worked around

1. **Zenity/Vulkan modal hang.** `UnrealEditor-Cmd -unattended` still pops a `zenity` dialog
   ("Vulkan device not available") under `xvfb-run`, because xvfb provides no GPU/Vulkan surface
   and `-unattended` doesn't suppress this specific dialog. Nothing can click it headless, so the
   process hangs forever. Fix: add `-nullrhi -nosound` to every headless `UnrealEditor-Cmd`
   invocation on this box.
2. **Relative `-ExecCmds` script paths silently fail.** `-ExecCmds="py Scripts/foo.py"` resolves
   against the *engine's* `Binaries/Linux` directory, not the project directory or cwd. Always
   pass an absolute path to the script.
3. **A fresh editor launch does not reopen the last-saved map.** `simulate_round.py` needed an
   explicit `LevelEditorSubsystem.load_level(...)` call at the top, or it ran the whole scripted
   loop against an empty default map.
4. **No human playtest or screen capture was possible in this session, by construction.** This
   headless box has no display and no input device attached to the Unreal process. The scripted
   Python state-machine playthrough (title → hits → score → end) is real evidence the game logic
   works, but it is **not** a substitute for a human mouse-and-keyboard playtest. The real jam
   needs one on a machine with a display — the Legion Go S, per the existing capture plan.
5. **Asset pipeline's 3D stage flakes cold.** The first one or two attempts at the Modly
   image-to-3D step failed fast (not a real error, just a cold-start issue — Modly's health check
   failing, VRAM not freed in time from a prior unload). It then succeeded reliably once warmed.
   Budget for 2-3 attempts in real jam timing, not 1.
6. **Win64 packaging broke twice on the `.uproject` file itself, not on anything UE-specific
   about this project's content:**
   - The `EngineAssociation` field still held this desktop's Linux source-build engine path.
     Harmless for the desktop's own `UnrealEditor-Cmd` launches (which open the project by
     explicit path, bypassing association lookup) but broke `RunUAT` on Windows outright.
     Blanking it to `""` is correct for a project packaged via an explicit `-EnginePath`.
   - That alone wasn't enough. An explicit, empty `"Modules": []` key in the `.uproject` makes
     `RunUAT BuildCookRun`'s `AutodetectSettings` treat the project as code-based, search for
     target files, find none, and fail with "does not look like uproject file but no targets
     have been found" — before cooking a single asset. **The key must be omitted entirely for a
     content-only (Blueprint, no C++) project, not just left empty.** Once both fixes were in,
     `BuildCookRun` completed in 28 seconds and produced a 374.6 MB zip. **Scope caveat: this
     `.uproject` shape was only tested against a content-only, no-C++ project. CLAUDE.md allows
     dropping to C++ for some systems in the real entry — if the real project ever adds a C++
     module, this exact fix (omitting `Modules` entirely) won't carry over as-is and needs
     re-validating against a code-based `.uproject`.**
7. **Butler is still not on the Legion Go S's PATH.** Confirmed both last session and this one.
   Not mock-specific — this blocks the real itch.io push too. (Update, real repo, 2026-10-28:
   butler is now installed and on PATH on the Legion Go S; only `butler login` remains, an
   owner-only interactive step.)

## Recommendations for the real Phase 0/Phase 1 plan

- **Resolve open question #14 now, not during jam week:** the exact `RunUAT BuildCookRun` flags
  and the `.uproject` shape needed for a content-only project are now proven working — reuse this
  mock's fixed `.uproject` shape (no `Modules` key, blank `EngineAssociation`) and
  `package-and-push.ps1` run pattern (direct `ssh ... -File script.ps1`, not a nested
  `Start-Process`) as the template for the real project's packaging gate, rather than
  re-discovering this during the actual jam. **This only applies as-is if the real entry stays
  content-only (no C++ module) — re-validate the `.uproject` shape if it ever drops to C++.**
- **Butler is now installed and on PATH on the Legion Go S (done 2026-10-28).** Only
  `butler login` remains — that's an owner-only interactive OAuth step, not automatable.
- **Finish the OBS auto-configuration wizard on the Legion Go S before jam week** — it needs one
  GUI click that SSH alone can't give it. Do this in person once, ahead of time.
- **Budget 2-3 attempts, not 1, for the asset pipeline's image-to-3D step** when it's the first
  call after Modly has been idle — this is a real, repeatable cold-start cost, not noise.
- **Plan an explicit human-playtest-with-capture checkpoint as its own task**, separate from
  "build the playable loop." Tonight's headless rehearsal could prove the game logic but never
  could have caught input-feel, control-mapping or camera issues — those only show up in a real
  playtest, and the real jam's schedule should not assume the scripted/simulated loop covers that
  ground.
- **If using Unreal MCP instead of raw headless Python scripting for the real jam** (this mock
  used Python throughout, not MCP, for lower setup risk — see HANDOFF.md section 5), budget
  separate time to validate MCP's own headless/connection behavior; it was not exercised at all
  in this rehearsal.

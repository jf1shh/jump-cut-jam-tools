---
tier: tested
source: stages/00_prep/output/mock-jam-findings.md
updated: 2026-11-10
---

# Running the Unreal editor headless on our Linux box

Tested on 5.8.4; re-test on 5.9 before relying on it.

Proven in the 2026-10-28 mock jam (UE 5.8.4, CachyOS, no display).

## Tip: always add `-nullrhi -nosound` to headless runs
- **Why:** under `xvfb-run` there is no real Vulkan device. `UnrealEditor-Cmd -unattended` still opens a
  zenity "Vulkan device not available" dialog that nobody can click, so the process hangs forever.
  Before the fix a cold boot hung 20+ minutes; after it, 1-2 minutes.
- **How to check:** the editor reaches your script within a couple of minutes. If it sits silent, look for a
  `zenity` process (`pgrep zenity`).

## Tip: pass an absolute path to `-ExecCmds="py ..."`
- **Why:** a relative script path resolves against the engine's `Binaries/Linux` folder, not the project or
  your shell folder. It fails silently.
- **How to check:** the first line of your script should `print` something. No print in the log = script not found.

## Tip: load the map yourself at the top of the script
- **Why:** a fresh editor launch does not reopen the last saved map. A scripted run then works on the empty
  default map.
- **How to check:** call `LevelEditorSubsystem.load_level(...)` first, then assert the expected actors exist.

## Tip: a scripted playthrough is not a playtest
- **Why:** a Python state-machine run proves game logic only. It cannot catch input feel, controls, camera or looks.
- **How to check:** put a real human playtest on a machine with a display (the Legion) as its own task.

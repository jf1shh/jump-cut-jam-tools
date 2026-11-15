# Mock jam 8: "Signal Run" — win juice, a real lose state, packaged build launches clean

Date: 2026-10-31. Builds on mock jam 7 (`stages/00_prep/output/mock-jam-findings-7.md`), which left the level with
no lose state (walking to the beacon won, nothing else happened) and a bare `PrintString` as the
only win feedback. This jam extends `L_MockJam7` in place via the live Unreal MCP editor (no
script re-run needed — `scripts/ue_build_level.py` still isn't idempotent, per mock jam 7's open
items).

## Scope

1. Win juice: a sound, a camera shake, and a short delay before the existing "SIGNAL DELIVERED"
   message on beacon overlap.
2. A real lose state: a hazard trigger with its own feedback (sound, shake, red "SIGNAL LOST"),
   placed off the direct spawn-to-beacon line so the win and lose paths are independently
   reachable depending on the route taken.
3. Package to the Legion Go S via `scripts/package-and-push.ps1` and playtest both paths there.

## Result

The packaged build (`SilentBlade_MockJam7.zip`, 507.6 MB) built clean and launched on the Legion
with zero errors in the log — engine init in 2.11s, level load confirmed
(`LogLoad: LoadMap: /Game/MockJam7/L_MockJam7`), process stayed alive and responding. **Visual/input
verification of the win and lose triggers themselves was not completed this session** — see Open
items. Everything up to "the build runs" is confirmed; "the new triggers actually fire and feel
right" is not yet confirmed by direct observation.

All new Blueprint/level work was done live through Unreal MCP (port 8010) and confirmed compile-clean
with a 0-error/0-warning Map Check before packaging:

- **`BP_Beacon`** (existing, from mock jam 7) — `EventGraph`'s `OnComponentBeginOverlap(Mesh)` now
  runs `Audio|PlaySound2D` (`/Engine/EngineSounds/1kSineTonePing`) → `Camera|PlayWorldCameraShake`
  (new `BP_WinShake` asset) → `Utilities|FlowControl|Delay` 0.5s → the original
  `PrintString "SIGNAL DELIVERED"`.
- **`BP_Hazard`** (new) — an `Actor` Blueprint with a flat 150×150×10cm cube `StaticMeshComponent`
  (`OverlapAllDynamic` collision, same profile convention as `BP_Beacon`/`PlayerOrb`). On
  `OnComponentBeginOverlap` it runs `Audio|PlaySound2D` (`/Engine/EngineSounds/WhiteNoise`) →
  `Camera|PlayWorldCameraShake` (new `BP_LoseShake` asset) → `Delay` 0.5s →
  `PrintString "SIGNAL LOST"` in red for 3s. Placed in `L_MockJam7` at world location
  `(0, -150, 5)` — opposite the decorative orb `(-150, 150, 0)`, off the straight line from
  `PlayerStart` `(-300, 0, 50)` to the beacon `(300, 0, 0)`. Walking straight to the beacon wins;
  detouring into the hazard patch loses.
- **`BP_WinShake` / `BP_LoseShake`** (new) — both `LegacyCameraShake`-derived Blueprints (full
  class path `/Script/EngineCameras.LegacyCameraShake` — see bug 1 below). `BP_WinShake` is a
  quick, gentle punch (0.4s, FOV amplitude 3.0 @ 20Hz, Z amplitude 2.0 @ 25Hz). `BP_LoseShake` is
  stronger and near-instant (0.6s, blend-in 0.02s, roll + X/Z amplitude 4–6.0 @ 30–35Hz, randomized
  offset).

## Bugs found and fixed, in the order they surfaced

1. **`/Script/Engine.LegacyCameraShake` is not a valid class path.** `BlueprintTools.create`'s
   `asset_type` rejected it outright (`Parameter error: ... is not valid Class`). Confirmed via
   `ObjectTools.search_subclasses(base_class=CameraShakeBase, class_name="Legacy")` that the real
   path is namespaced under the `EngineCameras` module: `/Script/EngineCameras.LegacyCameraShake`.
   Fixed by using the correct path for both `BP_WinShake` and `BP_LoseShake`.
2. **Collision profile is still nested, not top-level — reconfirmed for a hand-added primitive
   component.** Same gotcha mock jam 7 found for `BP_Beacon`'s mesh component: adding a cube via
   `PrimitiveTools.add_cube` and then trying to set `collisionProfileName` directly on the
   component is silently ignored. `{"bodyInstance":{"collisionProfileName":"OverlapAllDynamic"}}`
   in `set_properties` works. Worth folding into a reusable helper if a mock jam 9 adds a third
   trigger-style actor.
3. **`package-and-push.ps1`'s documented `-NoticeFile ([string]::Empty)` workaround only works for
   `-Command` invocations, not `-File`.** The default `-NoticeFile` resolves to a Linux-side
   relative path (`..\docs\NOTICE.txt`) that was never copied to the Legion, so the first packaging
   attempt failed with a "notice file not found" error. The tooling-plan's documented empty-string
   workaround is for inline `-Command` invocations; passed to a `-File` invocation, PowerShell
   treats `([string]::Empty)` as a literal string argument, not an expression, so it fails with that
   literal text as the missing path instead of an empty one. Fixed by copying the real
   `_config/reference/NOTICE.txt` from this repo to the Legion (`C:\Dev\MockJam7Game\NOTICE.txt`) and pointing
   `-NoticeFile` at it directly. **The tooling-plan's gotcha entry for this needs a correction** —
   it doesn't cover `-File` invocations.
4. **Content sync to the Legion before packaging has no scripted step — it's a manual `scp`.**
   Confirmed (not previously documented as a gap) that the five changed/new assets
   (`L_MockJam7.umap`, `BP_Beacon`, `BP_Hazard`, `BP_WinShake`, `BP_LoseShake`) had to be copied by
   hand to `C:\Dev\MockJam7Game\Content\MockJam7\` before `package-and-push.ps1` would pick up the
   changes. Worked fine as a one-off `scp`, but see Open items — this will get tedious as the
   project grows.

## Open going into the real jam

- **Could not visually verify either trigger fires correctly.** The approach mock jam 7 used for
  its agent-administered playtest — synthetic input (`keybd_event`) and `SetForegroundWindow`
  driven over SSH — failed here: an SSH session lands in Windows Session 0 (`services`,
  non-interactive), while the running game and the Legion's own desktop are in Session 1
  (`console`). Windows isolates window handles and input injection across sessions, so nothing
  injected from Session 0 reaches the game (`Get-Process` showed `MainWindowHandle: 0` for the
  running `MockJam7Game` process). `stages/00_prep/references/mock-jam-6-tooling-plan.md` (line 299) already flagged
  this exact limit for mock jam 7's own playtest — "the agent can verify the packaged build
  visually when it runs on the Legion, not over SSH" — and it held again here. **The owner needs
  to playtest this build directly on the Legion** (or a future session needs to run an agent
  session interactively on the Legion's own desktop, not over SSH) to confirm the ping/shake/delay
  on the win path and the white-noise/shake/red-text on the lose path actually look and feel right.
  The build itself launches clean with zero log errors, so the risk is tuning (is the shake visible
  enough, is the delay the right length), not a crash or a silent build.
- **No content-sync script for pushing Linux-editor changes to the Legion.** This jam's `scp` was
  a one-off. If future mock jams keep editing on Linux and packaging on the Legion, this is worth
  scripting (`package-and-push.ps1` could take a source-content-root to sync from, or a small
  rsync/scp wrapper could run before it).
- **`-NoticeFile` gotcha in `stages/00_prep/references/mock-jam-6-tooling-plan.md` needs a correction note** pointing out
  the `-File`-vs-`-Command` difference (bug 3 above), so the next session doesn't rediscover it the
  hard way.
- **Neither `BP_Beacon` nor `BP_Hazard` guards against re-triggering.** Walking back and forth
  through either repeats its feedback every time. Carried forward unchanged from mock jam 7 (which
  had the same characteristic on the win side); not fixed here since it wasn't flagged as a problem
  and a "real jam" scoring level will likely have its own win/lose state machine regardless.
- **`/Engine/EngineSounds/1kSineTonePing` and `/Engine/EngineSounds/WhiteNoise` were chosen over
  `/Engine/EditorSounds/*` and `/Engine/VREditor/Sounds/*` on the assumption that `EngineSounds` is
  normal runtime content and the others are editor-only.** The packaged build launched with no
  errors, which is consistent with this being correct, but audio playback itself wasn't confirmed
  by ear this session (see the playtest-verification gap above) — worth a specific listen on the
  next on-device pass.

# Mock jam 7: "Signal Run" — first real level, packaged build renders and plays

Date: 2026-10-30. GDD: `stages/00_prep/references/mock-jam-7-gdd.md`. Builds on the mock jam 6 tooling plan
(`stages/00_prep/references/mock-jam-6-tooling-plan.md`), whose Gotchas log has the full detail for every entry
below. This doc is the summary.

## Scope

A real playable level instead of mock jam 6's floating scratch content: a walled 10 m × 10 m room
(floor + 4 walls, 3 m high), a PlayerStart at one end, the generated `SM_Beacon` (as `BP_Beacon`,
the win trigger) at the other, and the generated `SM_Orb` as a decorative placeholder. The
level is built headless by `scripts/ue_build_level.py`. Win = overlapping the beacon prints
`SIGNAL DELIVERED`.

## Result

The packaged Windows build renders on the Legion Go S (sky, walls, beacon, and orb art visible),
and holding W from PlayerStart reaches the beacon and logs `SIGNAL DELIVERED`. The agent verified
this on the Legion's own display (DPI-aware screenshots plus synthetic input) before the owner
played it. The owner's first look caught one more bug (the oversized orb, below).

## Bugs found and fixed, in the order they surfaced

1. **Black screen:** the level had no lights. `_place_default_lighting()` now adds a sun, a sky
   light, and (see 4) a SkyAtmosphere.
2. **Hang after level load, part 1:** `SkyLightComponent.recapture_sky()` run under `-nullrhi`
   bakes an unusable capture. Switched to `real_time_capture=True`.
3. **Missing ICU data:** RunUAT didn't stage `Engine/Content/Internationalization`, so the game
   crashed instantly. `package-and-push.ps1` now copies it from the engine install. Zipping
   switched to `tar` because `Expand-Archive`/`Compress-Archive` silently drop long paths.
4. **Hang after level load, part 2 (the actual 17:21 hang):** the `GameFeatureData` runtime
   ensure stalled while writing its minidump. Fixed by marking the `DefaultGame.ini` rule
   `bIsEditorOnly=True`.
5. **Still black at ~145 fps:** `unreal.Rotator` takes positional args as (roll, pitch, yaw), so
   the sun sat below the horizon. Switched to keyword args. A real-time sky light also needs a
   SkyAtmosphere.
6. **Giant brown circle (owner playtest):** generated meshes import at ~200 cm across. The 2 m orb,
   1.5 m in front of the spawn point, filled the view. `_spawn_mesh_actor()` now takes a scale; the
   orb is 0.3. The already-built level was patched in place (backup at
   `C:\Dev\MockJam7Game\Content\MockJam7\L_MockJam7.umap.pre-orbfix.bak` on the Legion).
7. **Beacon invisible at spawn (agent retest):** generated meshes also have a centred pivot. The
   beacon spawned at z=0 was half-buried, a ~1 m stub hidden behind the orb, which sat on the same
   spawn-to-beacon line. `_rest_on_floor()` now lifts every spawned mesh by its bounds, and the
   orb moved to y=150. Patched in place (backup `L_MockJam7.umap.pre-placefix.bak`).

**Final retest (2026-10-30, packaged, windowed 1280×720 on the Legion):** at spawn the 2 m beacon
tower is visible straight ahead and the orb sits off to the right. Holding W reaches the beacon
and logs `SIGNAL DELIVERED`. No fatal errors or ensures.

## Open going into the real jam

- **`package-and-push.ps1` needs a permission rule for unattended runs.** The auto-mode
  classifier blocked it once (no `-ItchTarget`, so local only) until the owner OK'd it directly.
- **Size every generated mesh on placement.** The ~200 cm import size will hit every asset.
- **Re-test `recapture_sky()` on its own?** Fix 2 was never isolated from fix 4. It's
  `real_time_capture` either way, so low priority.
- The level build script still isn't idempotent; in-place patches need one-off scripts.

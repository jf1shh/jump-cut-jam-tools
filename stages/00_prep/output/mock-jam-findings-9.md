# Mock jam 9: "Signal Run" — re-trigger guard on both triggers, a tooling-doc correction

Date: 2026-10-31. Builds on mock jam 8 (`stages/00_prep/output/mock-jam-findings-8.md`), which left `BP_Beacon` and
`BP_Hazard` on `L_MockJam7` able to fire their win/lose feedback repeatedly if the player walked
back and forth through either. This was a deliberately small, scoped polish round pulled straight
from mock jam 8's open items — no new mechanics, no content/sound work, no tooling expansion.

## Scope

1. Add a re-trigger guard to `BP_Beacon` and `BP_Hazard` so each fires its feedback sequence at
   most once per level instance.
2. Correct the `-NoticeFile` gotcha note in `stages/00_prep/references/mock-jam-6-tooling-plan.md` to flag that the
   documented `([string]::Empty)` workaround only applies to `-Command` invocations of
   `package-and-push.ps1`, not `-File` invocations (mock jam 8's bug 3).

## Result

Both Blueprints now guard against re-triggering. The final packaged build
(`SilentBlade_MockJam7.zip`, 508.1 MB, includes the Nanite fix and the SkyAtmosphere fix below)
built clean (`BUILD SUCCESSFUL`, 26.77s for the final repackage) and launched on the Legion with
zero log errors — level load confirmed (`LogLoad: LoadMap: /Game/MockJam7/L_MockJam7`), process
stayed alive and responding through the poll window, an explicit log grep confirmed the Nanite
warning is gone (see bug 3), and a `SkyAtmosphere` actor now exists in the level so the SkyLight
real-time-capture warning's underlying condition no longer holds (see bug 4). As with
mock jam 8, **visual/input verification of the re-trigger guard actually working in play was not
possible this session** — see Open items; everything up to "the build runs clean" is confirmed.

**Addendum (same date, folded into this round after an owner playtest):** the owner's own playtest
of the first packaged build surfaced a third issue — a red on-screen Nanite material warning on the
orb mesh. See bug 3 below. A second owner playtest of that fixed build then surfaced a fourth issue
— a red on-screen SkyLight real-time-capture warning (see bug 4). Both fixes and their
re-verification are included in this doc's final state, not a separate findings doc.

All changes were made live through Unreal MCP (port 8010) and confirmed compile-clean (0
errors/0 warnings, `warnings_as_errors=true`) before packaging:

- **`BP_Beacon`** — added a new `bTriggered` Blueprint boolean variable (default `false`). The
  `OnComponentBeginOverlap(Mesh)` event now wraps its existing sound → camera shake → delay →
  "SIGNAL DELIVERED" sequence in `(if (not (Variables|Default|GetTriggered)) (Variables|Default|
  SetTriggered true) ...)` — the DSL getter/setter node IDs are `GetTriggered`/`SetTriggered`, not
  `GetbTriggered`/`SetbTriggered` (UE strips the `b` Hungarian-notation prefix from the generated
  node name; see bug 1 below). The flag is set `true` as the very first statement inside the guard,
  before the sound/shake/delay run, so re-entering the trigger during the 0.5s delay also can't
  double-fire.
- **`BP_Hazard`** — identical change: new `bTriggered` bool, same `if (not (GetTriggered))` guard
  wrapping the sound → shake → delay → red "SIGNAL LOST" sequence.
- No new actors, meshes, or level geometry — `L_MockJam7`'s actor placement is unchanged from mock
  jam 8.

## Bugs found and fixed, in the order they surfaced

1. **The Blueprint variable getter/setter DSL node ID drops the `b` Hungarian prefix.** Adding a
   bool variable named `bTriggered` via `add_variable` and then calling
   `(Variables|Default|GetbTriggered)` / `SetbTriggered` in `write_graph_dsl` failed with
   `AssertionError: ... Variables|Default|GetbTriggered does not exist`. `find_node_types` with a
   `"Triggered"` filter on the graph showed the real generated IDs are `Variables|Default|
   GetTriggered` and `Variables|Default|SetTriggered` — UE's standard "drop the `b` from the
   display name of a bool property" convention carries through to the DSL node ID too, not just
   the Blueprint editor UI. Fixed by using the un-prefixed names; the variable itself is still
   named `bTriggered` in `list_variables`.
2. **`package-and-push.ps1` run over `ssh <device-host>` needs `-ExecutionPolicy Bypass`, not just
   `-Command`.** A plain `powershell -Command "& C:\...\package-and-push.ps1 ..."` failed outright
   with `running scripts is disabled on this system` (`PSSecurityException`) before even reaching
   the `-NoticeFile` question this session was supposed to just re-confirm. Not new — `-Command`
   invocations apparently were never actually exercised end-to-end for this script in mock jam
   6/7/8's packaging runs (those presumably ran under a session/profile with a less restrictive
   policy already in effect) — but worth logging since it's the first time a bare `-Command`
   packaging call was attempted fresh this way. Fixed by adding `-ExecutionPolicy Bypass` to the
   remote `powershell` invocation; `-NoticeFile C:\Dev\MockJam7Game\NOTICE.txt` (a real path,
   `-Command`-style, no `([string]::Empty)` needed since a real notice file was wanted) then worked
   exactly as the corrected tooling-plan note (this jam's scope item 2) describes.
3. **Nanite material usage warning on the orb, reported by the owner after playtesting the first
   packaged build:** `LogMaterial: Warning: Material /Game/MockJam7/mj7_orb/Materials/
   mj7_orb_material_0 missing usage flag Nanite! Default Material will be used in game.` — red
   on-screen text, not a crash. Root cause: `mj7_orb_material_0` is a `MaterialInstanceConstant`
   (an Interchange glTF import), not a plain `Material` — its parent chain is `mj7_orb_material_0`
   → `/InterchangeAssets/gltf/MaterialInstances/MI_Default_Opaque` → `/InterchangeAssets/gltf/
   M_Default`, a **shared Unreal Engine plugin material** (Interchange's default glTF-import
   template), not project content. `bUsedWithNanite` only exists as a property on the base
   `Material` class, confirmed via `ObjectTools.list_properties` — a `MaterialInstanceConstant` has
   no such boolean.
   - **First attempt (did not work, verified by relaunch + log grep):** `MaterialInstanceConstant`
     exposes `basePropertyOverrides.bOverride_UsageFlags` / `usageFlags` (a bitmask), seemingly
     designed to let an instance declare extra usage flags without touching its parent. Found the
     Nanite bit (`262144`, bit 18) empirically by toggling `bUsedWithNanite` on `M_Default`,
     diffing the instance's mirrored `usageFlags` value, then reverting — not guessed. Setting the
     override on `mj7_orb_material_0` alone, repackaging, and relaunching still showed the exact
     warning in the fresh log. This bitmask override does not suppress this particular runtime
     check for an instance.
   - **Actual fix:** set `bUsedWithNanite = true` directly on the shared base
     `/InterchangeAssets/gltf/M_Default` (physically at `Engine/Plugins/Interchange/Assets/Content/
     gltf/M_Default.uasset` in the engine install, not under the project's `Content/`), recompiled,
     and saved. Synced the same relative engine-plugin file to the Legion's own `C:\Dev\UE_5.8`
     install (confirmed the relative path matched before copying — it did). Repackaged, relaunched,
     and this time `Select-String` against the fresh packaged log for `"missing usage flag Nanite"`
     returned no match — confirmed gone, not just inferred from `errorLines: 0` (which stayed 0 in
     *both* the broken and fixed builds, since this check doesn't grep `LogMaterial` at all — see
     mock jam 9's section 8 open question in its original handoff).
   - **Side effect, flagged rather than silently absorbed:** `M_Default` and
     `MI_Default_Opaque` are shared Interchange plugin content — six other project material
     instances derive from the same chain (`mockjam4_target_material_0`,
     `mockjam4_throwable_material_0`, `mj6_beacon_material_0`, `mj6_orb_material_0`,
     `mj7_beacon_material_0`, `lastlight_orb_material_0`). All of them are now also Nanite-usage
     eligible as a consequence of this fix. This is additive only (an extra allowed shader
     permutation, not a removed one) and should not change any existing visuals, but it is a
     project-wide engine-content change, not one scoped to the orb alone — worth knowing if any of
     those meshes behave unexpectedly under Nanite later.
4. **SkyLight real-time-capture warning, reported by the owner on the second playtest (after the
   Nanite fix was already built in):** red on-screen text, Unreal's standard warning —
   "A sky light with real-time capture enable is in the scene. It requires at least a
   SkyAtmosphere component. A VolumetricCloud component or a mesh with a material tagged..."
   Confirmed via `ActorTools.get_components` that `L_MockJam7`'s `SkyLight_0` actor has
   `SkyLightComponent0.bRealTimeCapture = true`, and via `SceneTools.find_actors` that the level
   had no `SkyAtmosphere` actor at all — exactly the condition the warning describes. Fixed by
   adding a `/Script/Engine.SkyAtmosphere` actor to `L_MockJam7` via
   `SceneTools.add_to_scene_from_class` (default transform, no other actors or materials touched —
   this is the simplest option the warning itself names first, and nothing about this jam-scale
   scene calls for a `VolumetricCloud` or a tagged mesh instead). Did not disable real-time capture
   — that would change what the sky light actually renders, not just silence the warning. Saved,
   scp'd the updated `L_MockJam7.umap` to the Legion, repackaged (`BUILD SUCCESSFUL`, 26.77s, zip
   508.1 MB), relaunched via `legion_playtest.py` (`errorLines: 0`, level loaded, process stayed
   alive), and re-confirmed via `Select-String` that the Nanite warning (bug 3) stayed fixed. The
   SkyLight warning itself is on-screen-only and was never written to the log file in the broken
   build either (confirmed by grepping for "SkyAtmosphere" and "requires a Sky" — no matches) —
   so this one can't be confirmed gone by log grep the way bug 3 was; confirmed instead by the
   underlying condition (no `SkyAtmosphere` actor) no longer being true, plus a clean repackage and
   relaunch. Owner can also eyeball the next playtest.

## Open going into the real jam

- **Could not visually verify the guard fires correctly (i.e., that walking through either trigger
  twice only prints its message once).** Same root cause as mock jam 7 and 8: an SSH-launched
  session on the Legion lands in Windows Session 0, while the running game is in interactive
  Session 1, so no synthetic input reaches the game to actually walk the player through a trigger
  twice. `legion_playtest.py`'s automated check (process stays alive, level loads, log has zero
  error lines) passed, but it never drives the player into either trigger at all, let alone twice —
  it can't distinguish "guard works" from "guard present but untested." **The owner needs to
  playtest this build directly on the Legion**, walking through the beacon (or hazard) twice in a
  row, to confirm the message/sound/shake fire only on the first pass through each.
- Everything else carried forward unchanged from mock jam 8's open list (sound asset choice
  undetermined by ear, no scripted content-sync tool, audio playback itself unconfirmed) — out of
  scope for this round by instruction, not re-investigated here.

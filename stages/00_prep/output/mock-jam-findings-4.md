# Mock jam 4: real art + real audio attempt + a real interactive mechanic, combined

Date: 2026-10-29. Builds on mock jam 3 (PR #39, interactive Blueprint mechanic packaged and pushed
to the Legion Go S, primitive-shape meshes). This rehearsal was the first attempt to combine all
three production tracks at once — real generated art, real generated audio, and a real interactive
mechanic — through the full pipeline to a packaged, pushed build. A prior agent run on this same
rehearsal was interrupted by a machine reboot; this session picked it up. **Correction up front:**
the resume briefing for this session understated how far that prior run had actually gotten — see
"What was already done before this session" below.

## Scope

Minimal proof mechanic, reusing mock jam 3's `BP_Target`/`BP_Projectile`/`BP_InputSpawner` Blueprints
and `L_MinimalProof` level in `~/Projects/ue-mcp-verify`, but this time with real generated meshes
(`SM_ThrowableBall`, `SM_DunkTarget`) wired into the projectile and target instead of primitive
shapes, plus an attempt at a real score-hit sound effect. Package and push to the Legion Go S.

## What was generated

Two props, generated through the local Nexus pipeline (image → 3D → textures), logged in
`stages/02_build/output/asset-pipeline-log.csv`:

- **`mockjam4_throwable`** (the ball/projectile prop): `concept.png`, `mockjam4_throwable.glb`
  (final, repaired), `mockjam4_throwable.high.glb` (pre-repair), albedo/normal/AO textures.
- **`mockjam4_target`** (the dunk-target prop): same file set under `mockjam4_target/`.

**QA notes (honest, not blocking):** both props' QA report
(`*.cpu_tail_report.json`) flags non-manifold edges on the **high-poly** pre-repair mesh — 6 for
the throwable, 9 for the target (3 bodies merged down to 2 in the target's case). The pipeline's own
repair stage fixes both to 0 non-manifold edges in the final mesh actually imported into Unreal
(`nonmanifold_after: 0` for both in the QA JSON's `repair` block) — so the imported `SM_ThrowableBall`
and `SM_DunkTarget` assets are clean, but the flaw on the high-poly source is worth tracking if this
pipeline is ever reused for a bake/retopo step that reads the `.high.glb` directly instead of the
repaired one.

## Audio: blocked, root-caused, not retried

Two attempts to generate a score-hit SFX via nexus-music/ACE-Step both failed with exit code 1,
logged in `stages/02_build/output/audio-pipeline-log.csv` (`mockjam4_score_hit.flac`, 2026-10-29 13:34:34 and
13:34:55 UTC — the second retry was after an `lemonade unload`, per the prior run's notes, and
still failed). **Root cause (already diagnosed by the prior run, not rediscovered here):** Nexus's
music generator's GPU-preflight allowlist check
(`~/Projects/nexus/backend/services/music/generator.py`) doesn't recognize
`/opt/onlyoffice/desktopeditors/DesktopEditors` + its `editors_helper` process, which was holding a
GPU render-node handle — the same unfixed gap already on record in `stages/00_prep/output/mock-jam-findings-2.md`
§4. Per task instructions this was **not retried** and ONLYOffice was **not closed** — this is
carried forward as "no audio in this rehearsal," same honesty standard as findings-2. No audio
asset exists to wire into either Blueprint; this is a documented gap, not an attempted-and-failed
wiring step.

## What was already done before this session (correction to the resume briefing)

This session's briefing said the meshes were imported but not yet wired into the Blueprints, and
that no packaging/push had happened yet. On inspecting the live project and the Legion Go S,
**both of those were already done and saved before the reboot**:

- `BP_Target`'s `TargetMesh` component's `staticMesh` property was already set to
  `/Game/MinimalProof/mockjam4_target/StaticMeshes/SM_DunkTarget`, and `BP_Projectile`'s `ProjMesh`
  component's `staticMesh` was already set to `SM_ThrowableBall` — both confirmed via
  `AssetTools.is_dirty` returning `false` for both Blueprints (i.e. this is the on-disk saved
  state, not a stale in-memory default).
- A packaged Win64 build, `C:\jam\MockJam4Game\Packaged\Windows\SilentBlade_MockJam4.zip`
  (454.5 MB — under the 1 GB gate), was already on the Legion Go S with a last-write time of
  2026-10-29 06:51–06:52 AM, about an hour before this session started, and the project copy at
  `C:\jam\MockJam4Game` (`.uproject` basename hyphen-free, per the mock-jam-3 packaging fix) had a
  matching last-write time (06:50 AM) on the `BP_Target.uasset`/`BP_Projectile.uasset` files that
  matched the ones on the Linux box — so the pushed build reflects the already-wired meshes, not a
  stale pre-wiring state.

This session's actual contribution was **independent verification** of that state (not redoing the
work), plus the audio-blocked documentation, this findings doc, and the usual cleanup.

## How this session verified it (fresh editor + MCP, raw curl/JSON-RPC)

Brought up a fresh headless editor + MCP server exactly per the mock-jam-3 pattern:

```
Xvfb :112 -screen 0 1280x720x24 &
DISPLAY=:112 UnrealEditor-Cmd ~/Projects/ue-mcp-verify/ue-mcp-verify.uproject \
  -log -nullrhi -nosound -ModelContextProtocolPort=8011
```

No `claude mcp add` registration was used this time — went straight to raw HTTP JSON-RPC (`curl`
POST to `http://127.0.0.1:8011/mcp`, `initialize` to get an `Mcp-Session-Id` header, then
`tools/call` → `call_tool` with `toolset_name`/`tool_name`/`arguments`), since `ToolSearch` is
already known not to surface this server's tools in this environment (see Tooling gotchas below).
`list_toolsets` confirmed 50+ registered toolsets, same as mock jam 3.

Verification steps, each a real read-back and not a trusted "success" response:

1. `SceneTools.load_level` on `/Game/MinimalProof/L_MinimalProof` — confirmed loaded (`null` return,
   no error).
2. `AssetTools.find_assets` on `/Game/MinimalProof` recursively — confirmed both `SM_DunkTarget` and
   `SM_ThrowableBall` exist as real assets on disk under the expected `StaticMeshes/` subfolders.
3. `ActorTools.get_components` on each Blueprint's CDO (default object, obtained via
   `BlueprintTools.get_default_object`) — returned the real component ref paths
   (`BP_Target.BP_Target_C:TargetMesh_GEN_VARIABLE`, `BP_Projectile.BP_Projectile_C:ProjMesh_GEN_VARIABLE`).
   **Gotcha found this session:** querying `ObjectTools.get_properties` for the mesh-component
   property directly on the Blueprint's `Default__*_C` object (e.g. `targetMesh`) returned the
   literal string `"None"` even though the component clearly exists — the generic-CDO-property path
   doesn't resolve a component subobject reference correctly. The actual component must be fetched
   first via `ActorTools.get_components` (which returns real `refPath`s to the component
   subobjects), then `ObjectTools.get_properties`/`list_properties` called on *that* ref path.
4. `ObjectTools.get_properties` on each real component ref path for the `staticMesh` property —
   confirmed `SM_DunkTarget` on `TargetMesh_GEN_VARIABLE` and `SM_ThrowableBall` on
   `ProjMesh_GEN_VARIABLE`, both as full soft-object-path refs (not just a name match).
5. `BlueprintTools.compile_blueprint` on both Blueprints, then `LogsToolset.GetLogEntries` filtered
   to `LogBlueprint` — only the two expected `"Compiling Blueprint '...'"` entries, zero error
   entries, confirming both still compile clean with the real meshes attached.
6. `AssetTools.save_assets` with an empty path list (save-all-dirty) — returned `true`; nothing was
   actually dirty at that point, consistent with the on-disk state already matching.

No audio wiring was attempted (there is no audio asset to wire, per the Audio section above).

## Packaging and push verification

Rather than re-run `RunUAT BuildCookRun` from scratch (the existing package already reflects the
verified, saved, wired state — re-packaging would have produced a byte-different but logically
identical zip), this session independently exercised the **already-pushed** build on the Legion Go
S to confirm it's real and loads real content, the same way mock jam 3 did:

- Launched `C:\jam\MockJam4Game\Packaged\Windows\MockJam4Game.exe -log` over SSH via PowerShell
  (`Start-Process`), waited, then read `Saved\Logs\MockJam4Game.log`.
- **Confirmed:** both pak/IoStore containers mount (`global.utoc` and
  `MockJam4Game-Windows.utoc`/`.pak`), the AMD iGPU is detected and a D3D12 device is created
  (Feature Level 12_2, ray tracing tier 1.1), and the process gets through engine/RHI init.
- **Same known failure as mock jam 3, same root cause:** fails at swapchain creation —
  `LogD3D12RHI: Error: hr failed ... DXGI_ERROR_NOT_CURRENTLY_AVAILABLE` at
  `WindowsD3D12Viewport.cpp:162` — because the process runs over an SSH session with no attached
  interactive desktop (Session 0 equivalent), not because of a build or content defect.
- **Net result, stated plainly: real interactive playability could not be verified over SSH.**
  Content and GPU detection are independently confirmed; an actual play-through needed the owner
  physically at the Legion Go S's own screen, exactly as mock jam 3 required for its build.
- **UPDATE 2026-10-29 (owner, physically on the Legion Go S):** confirmed. The owner ran this build
  directly on the device's own screen — Space spawns the (now reskinned) projectile, it hits the
  target, and the score increments. Controller/joypad input also navigates correctly. Same
  confirmation as mock jam 3's build; this is the first time a mock jam has closed this loop twice
  in a row, i.e. for two separately packaged builds.
- Cleaned up the scratch PowerShell check scripts (`check.ps1`–`check5.ps1`, `cleanup.ps1`) left
  under `C:\jam\` by this session's verification steps. `SilentBlade_MockJam4.zip` and the
  `MockJam4Game` project copy were left in place on the Legion Go S for the owner's playtest, same
  as mock jam 3's packaged build.

## Tooling gotchas for the next session

Four carried forward from the resume briefing, confirmed/elaborated where this session touched them,
plus one new one (the CDO-property gotcha in step 3 above):

1. **`ToolSearch` never surfaces live Unreal MCP server tools in this environment.** Don't spend
   time on it — go straight to raw HTTP JSON-RPC `curl` against the MCP port. This held again this
   session with a server that was never even registered via `claude mcp add`.
2. **Chaining multiple `py <script>; py <script2>; quit` in one `-ExecCmds="..."` does not work** —
   the whole string after `py ` gets whitespace-tokenized as that one script's argv. Run each `py`
   import as its own single-command invocation, watch its own log line, then kill the process. (Not
   re-exercised this session since no new Python import was needed, but still accurate and worth
   keeping on record.)
3. **The stale `UnrealEngine-5.8.OFFLOADED-TO-NAS.txt` note is misleading.** The engine binary is
   actually still local at
   `~/Projects/UnrealEngine-5.8/Engine/Binaries/Linux/UnrealEditor-Cmd` and was used
   directly this session — a future session should not be misdirected by that stale offload note
   into looking for it on the NAS.
4. **PR #39 (mock-jam-findings-3.md) is still open/unmerged.** That doc had to be read from the
   `mock-jam-3-findings` worktree rather than master. Until #39 merges, that reference isn't
   reachable from a plain master checkout, which is itself worth flagging for a future session that
   might `grep`/search master and not find it.
5. **Nexus's GPU-preflight allowlist has a smaller, separate staleness gap** beyond the ONLYOffice
   one that blocked audio here: its `claude-code` allowlist entry is hardcoded to version path
   `2.1.284`, but the installed version is `2.1.304`. Out of scope to fix here (Nexus-side), noted
   for whoever next touches that allowlist.
6. **New this session:** `ObjectTools.get_properties`/`list_properties` on a Blueprint's CDO
   (`Default__*_C`) returns `"None"` for an actor-component-typed property even when the component
   genuinely exists and is populated — the generic property path doesn't resolve component
   subobjects. Get the component's real `refPath` first via `ActorTools.get_components`, then query
   properties on that ref path directly.

## Process cleanup

Killed at the end of this session: the `-nullrhi` `UnrealEditor-Cmd` process and the `Xvfb :112`
display this session started. No `claude mcp add` registration existed to remove (raw curl was used
throughout, never registered as a named MCP server) — `claude mcp list` after cleanup shows only
`context7` and `deepwiki`, no engine server. `gpu-preflight` confirmed CLEAR after cleanup (0.55 GB
VRAM used, well under the 4 GB limit). The Legion Go S's `MockJam4Game` process was also stopped
after the verification launch, and this session's own scratch PowerShell scripts there were
deleted; the packaged zip and project copy were left in place for the owner's playtest.

## Status summary

| Item | Status |
|---|---|
| Art (throwable + target) | Generated, QA'd (manifold flaw on high-poly source only, repaired mesh clean), imported |
| Audio (score-hit SFX) | **Blocked**, root cause known (Nexus GPU-allowlist gap, ONLYOffice), not retried |
| Mesh wiring (both Blueprints) | Done and saved **before this session**; independently re-verified via component-level read-back in a fresh editor/MCP session |
| Compile | Clean for both Blueprints, re-verified via log read-back |
| Packaging | Already done before this session (454.5 MB zip, under 1 GB gate); not redone (would be redundant) |
| Push to Legion Go S | Already done before this session; independently re-verified by launching the exe over SSH and reading its log |
| Interactive playability | **CONFIRMED 2026-10-29** — owner tested on-device, projectile/target/score and controller input all work |
| Cleanup | Editor/Xvfb killed, no MCP registration to remove, Legion scratch files removed, GPU confirmed free |

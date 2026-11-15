# Mock jam 3: interactive mechanic through Unreal MCP, packaged and pushed to the Legion Go S

Date: 2026-10-29. Builds on mock jam 2's live-editor Unreal MCP smoke test (PR #37): that test
proved a simple BeginPlay -> PrintString Blueprint could be built and independently verified
through MCP tool calls alone, but it never saved the Blueprint and never got anything into a
packaged, playable build. This rehearsal closes both gaps: build a real interactive mechanic,
save it to disk, and carry it all the way through packaging onto the actual Windows handheld.

## Scope (owner-set, unchanged from HANDOFF.md)

Minimal proof mechanic only: one input -> spawn/throw a projectile -> overlap detection
increments a score variable -> shown via print/text. Reuse the proven MCP setup (no regenerated
art; primitive shapes). Package it and push to the Legion Go S. Be honest about what could and
couldn't be personally verified as interactively playable.

## What was built

Project: `~/Projects/ue-mcp-verify` (mock jam 2's actual project no longer existed on disk —
already cleaned up per standing post-PR practice — so this reused the same proven MCP/plugin
setup in the surviving smoke-test project instead, per the HANDOFF's prior pivot).

Three Blueprints and a level, all under `/Game/MinimalProof/`:

- **BP_Target** (Actor): a cube primitive mesh with overlap collision
  (`collisionProfileName=OverlapAllDynamic`, `bGenerateOverlapEvents=true`), a `Score` int
  variable, and an `OnComponentBeginOverlap` handler that casts the overlapping actor to
  `BP_Projectile`, and only on a successful cast: increments `Score`, converts it to a string,
  `PrintString`s "Score: N", and destroys the projectile.
- **BP_Projectile** (Actor): a sphere primitive mesh, `Movable`, overlap collision enabled. On
  `EventTick` it moves forward (`GetActorForwardVector * 600 * DeltaSeconds` via
  `AddActorWorldOffset`); on `EventBeginPlay` it self-destroys after a 5-second delay as a leak
  guard.
- **BP_InputSpawner** (Actor): `AutoReceiveInput = Player0` (so it gets key events without being
  a pawn), a `SpaceBar` key-press event wired straight into `SpawnActorFromClass` with
  `Class=BP_Projectile`, a fixed spawn transform, and `CollisionHandlingOverride=AlwaysSpawn`.
- **L_MinimalProof** (level): duplicated from the engine's `Template_Default` map (the project
  had no map at all — content-only, never had one), with one `BP_Target` placed 500 units from
  one `BP_InputSpawner`.

## How it was built (tooling notes for the next session)

- The `megajam-mcp3` MCP server (Unreal's own HTTP MCP plugin, port 8011) was already registered
  at local scope from a prior session, and was confirmed `Connected` via `claude mcp list` — but
  `ToolSearch` could not resolve any `mcp__megajam-mcp3__*` tool in *this* session either, despite
  being a fresh session (the HANDOFF's documented workaround — "a fresh session's handshake will
  pick it up" — did not hold this time). **Workaround used:** drove the server directly over raw
  HTTP JSON-RPC with `curl` (MCP `initialize` to get a session ID, then `tools/call` ->
  `call_tool` with `toolset_name`/`tool_name`/`arguments`). The server only exposes three
  top-level tools (`list_toolsets`, `describe_toolset`, `call_tool`) that proxy into ~50
  registered toolsets — this works identically to the tool-call shape ToolSearch would have
  exposed, just without the harness's schema binding. Next session: if `ToolSearch` still can't
  resolve `mcp__megajam-mcp3__*` after confirming `Connected`, don't burn more time on it — use
  this curl/call_tool pattern immediately.
- `BlueprintTools` exposes a DSL (`write_graph_dsl`/`read_graph_dsl`/`get_graph_dsl_docs`) that is
  far faster than raw `create_node`/`connect_pins` for anything with real control flow (casts,
  branches, variables). **Caveat found this session: the DSL cannot create or target an
  `AddEvent`-incompatible event node** — component-bound overlap events and raw input-key events
  (`Input|KeyboardEvents|SpaceBar`) are not in the `AddEvent|*` registry the DSL's `(event ...)`
  form looks up, even after the node already exists in the graph and shows up by name in
  `read_graph_dsl`'s output. Workaround: create that one event node imperatively with
  `create_node`, then wire everything downstream of it with `create_node`/`set_pin_value`/
  `connect_pins` directly (DSL for the rest of each graph where possible).
- `read_graph_dsl`'s pretty-printer silently flattens cast `(:then)/(:CastFailed)` branching into
  a flat sequential list when there's only one continuation with a body — this looks like the
  conditional got lost but it did not. Confirmed via `get_node_infos` on the actual
  `K2Node_DynamicCast` node that `CastFailed`'s output pin has zero connections and `then`'s
  output correctly drives the rest of the chain. **Do not trust `read_graph_dsl`'s shape for
  verifying branch structure — check real pin connections with `get_node_infos` instead**, per
  the standing "MCP can report success without doing the thing" discipline (`_config/reference/knowledge-base.md`).
- Struct-typed pins (e.g. `SpawnTransform`) did not accept a literal default value string via
  `set_pin_value` (the pin's `value` stayed empty after a "success" response) — had to build a
  `Math|Transform|MakeTransform` node and wire its output in instead, and that style of struct
  literal (`"(X=0,Y=0,Z=100)"`) *did* work for the `Vector`/`Rotator` sub-pins directly on that
  node. Lesson: struct-literal pin defaults work for some pin types and not others, verify with a
  read-back every time rather than assuming the pattern transfers.
- No level asset existed in the project at all. Created one by duplicating the engine's
  `/Engine/Maps/Templates/Template_Default` into `/Game/MinimalProof/L_MinimalProof` via
  `AssetTools.duplicate`, then `SceneTools.load_level` (which refused until the then-current
  transient level's dirty assets were saved first), then placed actors with
  `SceneTools.add_to_scene_from_class`.
- All three Blueprints compiled clean — confirmed by reading `LogBlueprint`/error-pattern log
  entries after each `compile_blueprint` call, not just trusting its `null` return.
- Saved everything (`AssetTools.save_assets` with an empty path list = save all dirty) and
  confirmed on disk: `Content/MinimalProof/{BP_Target,BP_Projectile,BP_InputSpawner}.uasset` and
  `L_MinimalProof.umap` all exist with real file sizes.

## What was independently verified vs. merely attempted

**Verified** (read back after the fact, not just trusted from a tool's success response):
- Every pin wiring described above, via `get_node_infos` pin-by-pin (cast branch wiring, overlap
  event params, input-key `Pressed` -> `SpawnActorFromClass` exec chain, `SpawnTransform` ->
  `MakeTransform` connection).
- `bGenerateOverlapEvents` / `collisionProfileName` / `mobility` on both mesh components, via
  `get_properties` read-back after `set_properties`.
- Clean compiles for all three Blueprints, via `LogsToolset.GetLogEntries` on `LogBlueprint` (no
  error entries for any of the three compile passes).
- All four assets exist on disk with real content (`ls -la` on
  `~/Projects/ue-mcp-verify/Content/MinimalProof/`).
- The packaged Windows build actually launches on the Legion Go S and loads real content: ran
  `MinimalProofGame.exe -log` directly over SSH and watched it mount both `.pak`/`.utoc` content
  containers, detect the GPU (`AMD Radeon Graphics`, driver found), and get through engine/audio
  init before failing at the final swapchain-creation step.

**UPDATE 2026-10-29 (owner, physically on the Legion Go S):** confirmed. The owner unzipped and ran
`SilentBlade_MinimalProof.zip` on the device's own screen — Space spawns the projectile, it hits the
target, and the score increments as designed. Controller/joypad input also navigates correctly. This
closes the one gap every mock jam so far had left open: a human pressing a button and seeing a packaged
build actually respond. The SSH/PIE limitations below are still accurate as a record of why this
couldn't be confirmed by an agent — they're just no longer the final word.

**Attempted but not confirmed as actually playable (superseded by the update above):**
- A real interactive playtest (press Space, watch a projectile spawn, hit the target, see the
  score print) was attempted two ways and neither reached a real conclusion:
  1. **In-editor PIE under the live `-nullrhi` headless editor.** `StartPIE` succeeded and
     `SlateInspectorToolset.PressKey("SpaceBar")` reported success, but a Slate UI snapshot of the
     editor window showed no viewport widget in the accessibility tree at all (every widget had
     `size=0,0` — a known `-nullrhi` limitation: the viewport panel doesn't register normally
     without a renderer backing it). No `LogBlueprintUserMessages` entries appeared afterward, so
     the key press almost certainly never reached the game's input stack; this does **not** mean
     the Blueprint logic is wrong, only that this specific headless setup cannot drive real input
     into PIE.
  2. **The packaged exe on the Legion Go S, launched over SSH.** The exe loads correctly (content
     mounts, GPU detected) but fails at
     `LogD3D12RHI: Error: hr failed ... DXGI_ERROR_NOT_CURRENTLY_AVAILABLE` when creating its
     swapchain. `tasklist` confirmed the process ran in the `Services` session (Session 0, no
     attached interactive desktop) — SSH sessions on Windows don't get a real display surface, so
     this is an artifact of launching remotely over SSH, not a build or content defect.
- **Net result: I cannot personally confirm the mechanic is interactively playable.** Both
  failures are display/session-context limitations of how I can reach this device and this
  editor, not evidence against the logic. The logic itself is as thoroughly checked as
  non-interactive inspection allows (every relevant pin, wire, and property read back after the
  fact, zero compile errors). **The owner needs to launch
  `C:\jam\MinimalProof\Packaged\SilentBlade_MinimalProof.zip` by hand on the Legion Go S's own
  screen** (unzip, run `MinimalProofGame.exe` while physically at/on the device) and press
  Space to get the first real confirmation that this plays.

## Packaging (new findings beyond section 6 of `mock-jam-findings.md`)

The two already-documented `.uproject` fixes (blank `EngineAssociation`, omit `Modules` entirely
for a content-only project) were applied and necessary again here, but **two new blockers showed
up that the prior two mock jams never hit**, because this project had `ModelContextProtocol` and
`AllToolsets` enabled as plugins (the prior mocks used headless Python, no MCP plugin):

1. **The project folder/.uproject name cannot contain a hyphen.** `ue-mcp-verify.uproject`
   produced *syntactically invalid* auto-generated `Target.cs` files
   (`public class ue-mcp-verifyEditorTarget : TargetRules` — `-` is illegal in a C# identifier),
   which failed with a wall of C# parser errors before `AutodetectSettings` even got to a real
   error message. Renamed the copy on the build machine to `MinimalProofGame.uproject` (the
   *project file's name* is what matters for this, not the containing folder's name) and the
   syntax errors disappeared. **If the real jam project's name or any working copy's filename
   ever contains a hyphen, this will recur — pick a hyphen-free `.uproject` name up front.**
2. **An enabled C++ plugin with no `TargetAllowList` forces the whole project to be treated as
   code-based for every platform, which then needs a full MSVC toolchain.** With
   `ModelContextProtocol`/`AllToolsets` enabled project-wide, `RunUAT` logged "is being treated as
   a code-based project ... because: ModelContextProtocol plugin is enabled" and then failed
   needing MSVC Build Tools 14.50/VS 17.8 (the Legion Go S only has an older toolchain). **Fix:**
   restrict both plugins to `"TargetAllowList": ["Editor"]` in the `.uproject` (matching the
   pattern the project already used for `ModelingToolsEditorMode`) — this keeps them available in
   the live editor/MCP session while excluding them from the Win64 packaged target, so UBT no
   longer needs to compile anything for the shipping build.
3. **Cooking still failed afterward** with `LogGameFeatures: Error: Asset manager settings do not
   include a rule for assets of type GameFeatureData` — the `GameFeatures` plugin (a transitive
   dependency, likely pulled in by `AllToolsets`' `GameFeaturesToolset`) still runs during the
   cook step itself even with the owning plugin's `TargetAllowList` restricted to Editor, because
   cooking runs inside an editor-context process. Fixed with the standard one-line
   `DefaultGame.ini` addition:
   ```
   [/Script/Engine.AssetManagerSettings]
   +PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",AssetBaseClass="/Script/GameFeatures.GameFeatureData",bHasBlueprintClasses=True,bIsEditorOnly=False,Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=true,CookRule=AlwaysCook))
   ```
4. With all three fixes in place, `scripts/package-and-push.ps1` (reused unmodified from mock
   jam 2, run directly over `ssh <device-host> -- powershell ...`, **not** `pwsh` — this Legion Go S
   image doesn't have PowerShell 7 on PATH, only Windows PowerShell) completed in ~23 seconds and
   produced `SilentBlade_MinimalProof.zip` at 430.9 MB — well under the 1 GB gate.
5. The project/source copy lands at `C:\jam\MinimalProof` on the Legion Go S (via plain `scp -r`
   of `Content/`, `Config/`, and the renamed `.uproject`); the engine there is at
   `C:\Dev\UE_5.8` (not the `C:\UE_5.8` the script's own doc comment example uses — check with
   `ssh <device-host> "dir C:\Dev"` rather than assuming the docstring's example path).

## Packaging/playtest-handoff status

- **Packaged:** yes. `C:\jam\MinimalProof\Packaged\SilentBlade_MinimalProof.zip` (430.9 MB) on
  the Legion Go S, built from a clean `RunUAT BuildCookRun` (exit 0, "BUILD SUCCESSFUL").
- **Exe launches and loads real content:** confirmed (paks mounted, GPU detected, got to the
  swapchain-creation step) — but only run remotely over SSH with no interactive desktop attached,
  so rendering itself was never actually exercised.
- **Interactively playable:** **CONFIRMED 2026-10-29.** The owner, physically at the Legion Go S,
  unzipped and ran the build, pressed Space, and watched the projectile spawn and hit the target
  with the score incrementing. Controller input also worked.
- Editor-side logic (the actual mechanic: input -> spawn -> move -> overlap -> score -> print)
  was independently verified via pin-level inspection and clean compiles, **before** packaging,
  per the task's requirement — but not via an actual observed runtime play-through, for the
  reasons above.

## Process cleanup

Torn down at the end of this session: killed the `-nullrhi` `UnrealEditor` process and the Xvfb
`:111` display, and ran `claude mcp remove megajam-mcp3 -s local`. Rationale: everything that
needed to survive (the three Blueprints, the level, the `.uproject`/config fixes, the packaged
zip on the Legion Go S) is already saved to disk or pushed off-machine and independently
verified; there was no remaining reason to keep a `-nullrhi` (non-rendering) editor instance
running, and the exact relaunch command is already on record in `HANDOFF.md` if a future session
needs the same live-editor MCP setup again. The remote `Extracted/` scratch copy of the packaged
build on the Legion Go S was also removed after the SSH launch test; the zip itself was left in
place at `C:\jam\MinimalProof\Packaged\SilentBlade_MinimalProof.zip` for the owner's playtest.

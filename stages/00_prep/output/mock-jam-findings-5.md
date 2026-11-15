# Mock jam 5: "Last Light" — packaged, owner-playtested, two root causes confirmed and deferred

Date: 2026-10-29. Builds on mock jam 4 (PR #41 area) and mock jam 3's packaging/push workflow.
This is the first mock jam where a human actually played the packaged build on the target hardware
(the Legion Go S) and reported real bugs back, rather than the agent only verifying via MCP graph
inspection. That gap — and what it caught — is the headline finding.

## Scope

Top-down tiny arena, "Last Light": a glowing lantern-orb player (static mesh) lights 3 unlit beacons
by walking up and holding E; a roaming shadow blob causes a loss on touch; lighting all 3 beacons
wins. Full workflow rehearsal: greybox + Blueprints, real mesh import, UI widgets (menu/HUD/end
screen), packaging, push to the Legion Go S, owner playtest, dev log, submission-checklist dry run,
findings doc.

## Packaging and push — succeeded

- Packaging-related config fixes from mock jam 3 were already in place in `ue-mcp-verify`'s project
  files (checked by reading the files, not assumed): the `ModelingToolsEditorMode` /
  `ModelContextProtocol` / `AllToolsets` plugins all have `"TargetAllowList": ["Editor"]`;
  `DefaultGame.ini` has the `GameFeatureData` primary-asset-type scan line; `DefaultEngine.ini`'s
  default/startup map is still `/Game/LastLight/L_LastLight`.
- `ue-mcp-verify.uproject` still has a hyphen in its name, which breaks packaging if used directly.
  Same workaround as mock jam 3: push a renamed **copy** of `Content/`, `Config/`, and the
  `.uproject` (renamed to `LastLightGame.uproject`) to the Legion Go S rather than renaming the live
  project. Landed at `C:\Dev\MockJam\LastLightGame\`.
- Result: `BUILD SUCCESSFUL`, `SilentBlade_LastLight.zip` at 431.6 MB (well under the 1 GB cap),
  BuildCookRun took ~36 seconds. The packaged build ran cleanly for ~26 seconds in its own smoke-run
  log (18:47:47–18:48:13), no crash, clean `LogExit: Exiting.`
- One harmless "Handled ensure" fires at runtime in the packaged build's own log, not the packaging
  log: `Ensure condition failed: AssetBaseClassLoaded ... Failed to load class
  /Script/GameFeatures.GameFeatureData for Primary Asset Type GameFeatureData!`. The `DefaultGame.ini`
  fix stops this from failing the **cook**, but does not stop a runtime ensure from firing. Not
  blocking, not investigated further — worth a look if it recurs on a real build.

## The owner's playtest caught two bugs graph-level QA missed

Before the playtest, `read_graph_dsl` confirmed `BP_GameMode`'s and `WBP_MainMenu`'s event wiring
matched spec exactly (menu dismiss, HUD progress updates, win/lose transitions). That check only
proves the **event wiring** is intact — it does not catch whether the player can actually move or
whether the meshes have real materials. The owner then played the actual packaged build on the
Legion Go S and reported: "super rough no textures really basic and controls dont work."

**Lesson: `read_graph_dsl`-based QA is necessary but not sufficient.** A clean graph-wiring pass must
never be read as "gameplay works" — only an actual playtest (task #5 in this project's standing
workflow) catches that. Keep playtesting on every build, not just at the end.

### Bug 1 — controls don't work

Root cause confirmed: `BlueprintTools.get_parent` on `BP_PlayerOrb` returns a bare `/Script/Engine.Pawn`,
not `DefaultPawn` or `Character`. `BP_PlayerOrb`'s EventTick DSL calls `Pawn|Input|AddMovementInput`
every tick (built from raw `IsInputKeyDown` polling of WASD, not Enhanced Input bindings — a separate
code smell, not itself fatal). A bare `Pawn` has no movement component (no `FloatingPawnMovement`, no
`CharacterMovementComponent`) to consume that input, so `AddMovementInput` is a silent no-op. The orb
never moves, regardless of input. **Not yet verified:** whether `BP_GameMode`'s `DefaultPawnClass` is
even set to `BP_PlayerOrb`, and whether it's actually auto-possessed — no working MCP tool was found
this session to read default-object property values (`ObjectTools.get_property` doesn't exist). Check
possession first in whichever session fixes this; fixing only the movement component won't help if
possession is also broken.

### Bug 2 — no textures, "really basic" look

Root cause confirmed: `StaticMeshTools.get_material_slots` on `SM_PlayerOrb` returns exactly one slot,
a generic `Material_0`. A filesystem check of `Content/LastLight/Meshes/` shows only that one material
asset, shared across all three meshes, and no texture asset (diffuse/normal/etc.) anywhere in the
folder. "Import real meshes" (task #2) imported geometry only — no material/texture pipeline was ever
run on these three meshes. What the owner saw is the raw import's flat default material, not a
rendering bug.

**Correction, 2026-10-30 (mock jam 6 tooling plan):** root-caused further. The generated GLBs
themselves were never the problem — `lastlight_orb.glb` etc. embed real PBR materials with bound
albedo/normal/AO textures (confirmed by parsing the glTF JSON chunk directly). The bug is that this
import did not go through `scripts/ue_import_asset.py`'s documented `AssetImportTask`/Interchange path
(which nests output and is proven elsewhere, e.g. mock jam 2's `seed_pod` import). It most likely went
through a different, MCP-native import tool that only pulls in geometry. Fix: `scripts/ue_import_asset.py`
is now the only sanctioned import path, with a `--require-pbr` assertion (default on) that fails loudly
instead of silently shipping a flat-material mesh. See `stages/00_prep/references/mock-jam-6-tooling-plan.md` Phase A.

**Both bugs are documented findings only, not fixed.** Presented to the owner with three options (fix
both now, fix movement only, or stop and document); the owner chose to stop here and move straight to
findings/cleanup. Don't attempt either fix without being asked again.

## Tooling gotchas for the next session

- **`read_graph_dsl`'s `graph` param is a direct EdGraph refPath, not `{blueprint, graph: "name"}`.**
  Example: `/Game/LastLight/BP_GameMode.BP_GameMode:EventGraph`. The `{blueprint: ..., graph:
  "EventGraph"}` form errors with "Parameter error: EventGraph is not a valid object path for property
  'graph'."
- **The refPath suffix differs by Blueprint kind, but not the way you'd guess.** A C++-base Blueprint
  like `BP_GameMode` uses `BP_GameMode.BP_GameMode:EventGraph`. A Widget Blueprint like `WBP_MainMenu`
  uses the plain Blueprint name with **no** `_C` suffix: `WBP_MainMenu.WBP_MainMenu:EventGraph`, not
  `WBP_MainMenu.WBP_MainMenu_C:EventGraph` — even though `_C` shows up correctly inside node type_ids
  like `UserInterface|CreateWidget "...WBP_HUD_C"`.
- **`StaticMeshTools.get_material_slots` takes `mesh`, not `staticMesh`** — same inconsistent param
  naming as every other toolset in this project; found by trial and error against the error message.
- **Running `package-and-push.ps1` via plain `powershell` over SSH to the Legion Go S now requires
  `-ExecutionPolicy Bypass`** on that specific invocation (`powershell -NoProfile -ExecutionPolicy
  Bypass -Command "..."`). The box's default execution policy blocks running `.ps1` files at all
  ("running scripts is disabled on this system"). Not hit in exactly this form in mock jams 3/4 —
  always include it on future invocations on this box. Still plain `powershell`, not `pwsh` — not on
  PATH on this Legion image.
- **`scp` to the Legion Go S's Windows OpenSSH server needs forward slashes in the remote path.**
  `<device-host>:C:/Dev/MockJam/...` works; `<device-host>:C:\\Dev\\MockJam\\...` fails with "No such file or
  directory."

## Process cleanup

- A peer session confirmed during this session that it is not touching the live Unreal MCP session,
  the Legion Go S, or the two pending CSV rows — no actual collision occurred, but this check (via
  `ListAgents` + a direct message) should be repeated by every session before touching either, not
  assumed safe because a prior handoff says it was clean once.
- The two in-flight `stages/02_build/output/asset-pipeline-log.csv` / `stages/02_build/output/audio-pipeline-log.csv` rows noted in prior
  handoffs are still pending a commit — not from this session's work, confirmed independently by a
  peer session too. See this PR's commit for that.
- Orphan probe nodes in the Blueprints (flagged in earlier mock-jam findings docs) are still not
  cleaned up — deferred again, not addressed this session either (read-only diagnostic session, no
  Blueprint edits made).

## Status summary

Packaging and push: working, verified end to end. QA via graph inspection: passed clean, but proven
insufficient on its own — a real playtest is what actually caught the two bugs below. Gameplay:
broken in two confirmed, root-caused ways (no player movement; no real materials/textures), both
deferred by owner choice to a future session. Dev log and submission/playtest checklist dry runs for
this mock jam are in `stages/05_devlog/output/2026-10-29.md` and `stages/00_prep/references/mock-jam-5-checklist-dryrun.md`.

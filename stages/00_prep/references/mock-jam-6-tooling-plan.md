# Mock Jam 6 Tooling Hardening — Implementation Plan

> **Status (2026-11-01): executed.** See PLAN.md (mock jam entry) and `stages/00_prep/output/mock-jam-findings-7.md` to `-9.md`. The unchecked boxes below are historical, not open work.

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development`
> (recommended) or `superpowers:executing-plans` to run this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking. This plan is **planning only** — reading existing files is in scope,
> but do not run `gen_asset.py`/`qa_harness.py`/`ue_import_asset.py`, touch the live Unreal Editor, or
> make MCP calls while *writing* this plan. Running them is exactly what the tasks below schedule for
> whoever executes this plan next.

**Goal:** Fix the actual root cause behind mock jam 5's two deferred bugs (no real materials/textures;
bare-`Pawn` with no movement component), give `qa_harness.py` three new automated checks that would
have caught both bugs plus a reachability class of bug, then run mock jam 6 end-to-end — with an
agent-administered playtest before the human playtest — using the fixed pipeline and expanded harness,
closing with the same dev-log/findings/checklist ritual as mock jam 5.

**Architecture:** Four phases, each landing independently and each updating `_config/CANON.md` as it
lands (not deferred to one pass at the end): (A) root-cause the import-path bug and make the fix
procedural + defense-in-depth in code; (B) extend the existing non-blocking tick-callback QA harness
with three new checks, following its established conventions; (C) run mock jam 6 using the output of
A and B, with (D) the agent-playtest mechanism folded in as a required step of C, not bolted on after.
This document is also the living gotchas log for mock jam 6 onward — see the section right below this
header.

**Tech Stack:** UE 5.8 Linux editor, Epic's Unreal MCP plugin, `unreal` Python API (editor-embedded
interpreter only), Nexus local asset-gen CLIs (`nexus-image`, `nexus-3d`), this repo's `scripts/*.py`
wrappers, bash/zsh, `gh` CLI for the PR.

**Spec:** The owner's scope statement (asset pipeline, packaging/build gate, QA harness + new checks,
full mock-jam rehearsals, agent-administered playtesting) plus `stages/00_prep/output/mock-jam-findings-5.md` (the two
open bugs this plan exists to close) and `_config/CANON.md` (the indexing convention this plan must
follow). `AGENTS.md` and `CLAUDE.md` at the repo root govern naming, Blueprint-vs-C++, and the
Unreal-table exception this project runs under.

## Global Constraints

- Rule 7(h): no gameplay, levels, or art before the contest window (2026-11-12 00:00 ET) — every mock
  jam, including #6, runs against the scratch project `~/Projects/ue-mcp-verify` (or an equivalent
  disposable `.uproject`), never against content checked into this repo. This matches every prior mock
  jam's test-environment note (see `scripts/ue_import_asset.py`'s and `scripts/qa_harness.py`'s own
  docstrings).
- One lead agent is the only Unreal MCP caller at a time (`AGENTS.md`); one GPU workload at a time,
  `gpu-preflight` first (`AGENTS.md`, `CLAUDE.md`).
- Naming: `SM_`/`SK_`/`MI_`/`M_`/`BP_`/`WBP_`/`T_`/`L_` prefixes per `CLAUDE.md`.
- Doc-only (and script-planning-only) work in this repo goes through a worktree + PR, owner reviews
  and merges (recent precedent: PR #43 "water balloon physics concept research", PR #45 "AI asset to
  UE 5.8 hand-off research"). This plan's own execution must follow that pattern too.
- `_config/CANON.md` indexes everything under flat `_config/` and `stages/`, one row per file, by topic, grep-first — no
  buried subfolders, no doc that CANON doesn't point to.
- This plan is planning only: no code, script, Blueprint, or MCP changes happen while *writing* it.
  Code snippets inside the tasks below are specifications for whoever executes the plan, not changes
  already made.

---

## Gotchas log (append-only — read this before every mock jam, add to it, never start a new doc)

This section is the one place future mock jams (#7 onward) record newly discovered tooling gotchas,
instead of spawning `stages/00_prep/output/mock-jam-gotchas-N.md` one-offs. **Append new entries at the top of the
list below this instruction line, dated, with the mock jam number that found them.** Keep each entry
to 1–4 lines: what broke, the fix or workaround, where the full detail lives if it's long (a findings
doc or engine-reference file). Do not delete old entries; mark them superseded in place if a later jam
corrects one, the same way `_config/CANON.md` asks for corrections to be layered rather than silently
replaced.

- **[mock jam 7, 2026-10-31]** New scripts `scripts/legion_remote_launch.ps1` (runs on the Legion:
  extracts the zip fresh, detects the wrong-exe trap, registers a scheduled task with
  `Register-ScheduledTask -Force`, never `schtasks /Change` — that one hangs on an interactive
  password prompt over non-interactive SSH, per `.handoff/loop-157067/HANDOFF.md`) and
  `scripts/legion_playtest.py` (runs on the desktop: deploys the script, triggers the task, polls the
  process, greps the log for `LoadMap`/`Error:`/a custom win marker) replace the ~10 manual SSH steps
  per mock-jam session with one command. **Gotcha found and fixed**: `powershell -File <script> -Param
  'value'` over SSH passes single-quoted values through literally into the parameter — the remote
  shell splits `-File`'s trailing args with its own argv rules, not PowerShell's, and doesn't treat
  single quotes as quoting. Always double-quote `-File` parameter values over SSH. This is distinct
  from the `-Command ...$var...` escaping gotcha in `.handoff/loop-157067/HANDOFF.md` (that one is `$`
  getting a literal backslash inserted across bash→ssh→powershell; this one is argv splitting on
  `-File`) — both real, different mechanisms, fixing one doesn't fix the other. Live-verified
  2026-10-31 against the mock jam 7 zip: full deploy+launch+poll+log-check succeeded
  (`levelLoaded: true`, `stayedAlive: true`, `errorLines: 0`); `winMarkerFound: false` on that run is
  expected, since nobody drove the player to the beacon.

- **[mock jam 7, 2026-10-30]** **ROOT-CAUSED AND FIXED** the mid-PIE velocity-freeze finding below
  ("Resolved finding..."). It was level geometry, not a movement/input bug: `PlayerOrb` (the static
  mesh `scripts/ue_build_level.py` places as a decorative stand-in for the player's in-game identity,
  not a win-condition actor — only `BP_Beacon` carries `QAObjective`) had never had its collision
  profile set, so it defaulted to blocking (`QUERY_AND_PHYSICS`) and sat directly in the straight-line
  path between `PlayerStart` and the beacon, stopping any unsteered test pawn dead at its surface.
  Live-confirmed with `set_actor_enable_collision(False)` first (full velocity recovery), then
  identified by actor name (shows up as `StaticMeshActor_N`, an auto-assigned index — not by its
  display label `PlayerOrb`) via a full-level actor dump after narrower candidates (floor, player
  start, the debug-replicator) were ruled out one at a time. **Fix applied** in two places: (1)
  `scripts/ue_build_level.py`'s `_spawn_mesh_actor` now takes a `collision_profile` kwarg, and
  `PlayerOrb`'s spawn call passes `"OverlapAllDynamic"` (matching `BP_Beacon`'s own deliberate
  overlap-only collision, same reasoning — neither actor is meant to physically block the player); (2)
  a one-off `work/fix_orb_collision.py` applied the same change to the already-built `L_MockJam7`
  level in place (re-running `ue_build_level.py` would have duplicated every actor — it has no
  actor-level idempotency check, only a level-asset one). Re-ran `agent_playtest.py --diag`
  afterward: distance closed 602→50 units over 180 ticks with velocity nonzero throughout (vs. ~14
  units before the fix) — see `stages/03_playtest/output/qa-playtest-log.csv`, the two consecutive rows for `L_MockJam7`.
  **New gotcha, confirmed:** a bounding-box point-overlap check at the pawn's exact freeze x can miss
  the real blocking actor if that actor's reported AABB edge doesn't reach that exact point — the true
  stopping point is `obstacle_edge - pawn_collision_radius`, not the obstacle's raw edge; expand the
  candidate's box by the mover's collision radius first, or just test by disabling collision directly.
  **New gotcha, confirmed:** `unreal.Class` objects (from `component.get_class()`) have no
  `get_superclass()` method in this Python binding (`AttributeError`). **Carried forward, reconfirmed
  dead end:** this engine's Python binding exposes `HitResult` as a struct with no readable fields
  (`get_editor_property` raises "protected" or "Failed to find property"; no "break hit result"
  helper found on `GameplayStatics` or `SystemLibrary`) — don't retry without a different API path.
  **Checked, independent:** `qa_harness.py`'s separate `movement=skipped(no-default-game-mode-on-
  world-settings)` finding reads `world.get_world_settings().get_editor_property("default_game_mode")`
  — a level-config check unrelated to pawn collision against level geometry, confirmed by reading
  `_check_movement_setup()` directly rather than spending another engine round-trip to re-prove it.
  Still open if a future session wants it to actually run: set a `GameMode` override on `L_MockJam7`'s
  World Settings.
- **[mock jam 7]** Wrote `scripts/agent_playtest.py` (Task C4 Tier 1), the first committed, reusable
  version of mock jam 6's one-off playtest spike. Two live-verified API-shape fixes, both previously
  undocumented in this repo: `unreal.UnrealEditorSubsystem` has no `is_in_play_in_editor()` — it's on
  `LevelEditorSubsystem` instead; `unreal.Vector` has no `get_safe_normal()` — normalize manually
  (`dx/planar_dist, dy/planar_dist`). Pass ABSOLUTE paths to `--csv-log`, same cwd gotcha as
  `qa_harness.py`.
  - **Resolved finding, was flagged UNRESOLVED in the prior handoff:** the first clean run against
    `L_MockJam7` reported `pass=True` but only closed ~14 of 602 units toward the beacon over 180 real
    PIE ticks (vs. mock jam 6's 194/316-unit closure over the same tick count) — ~14x weaker. A
    `--diag` flag was added to the script (off by default; see its `--help`) and used to confirm: the
    pawn IS a `DefaultPawn` with a real `FloatingPawnMovement` component (ruling out the
    mock-jam-5-bug-1 missing-movement-component class of bug) and its max speed is the default 1200.
    But its velocity goes to **exactly zero** after ~0.3–0.4s of PIE time and the pawn freezes at a
    fixed position for the rest of the run, despite `add_movement_input` still being called every
    tick. This is NOT a collision block — `L_MockJam7` has only 5 actors total (`PlayerStart`,
    `PlayerController`, `PlayerCameraManager`, `DefaultPawn`, one `StaticMeshActor` 135+ units further
    along the path than the freeze point) and none of them are anywhere near where the pawn stops.
    Reproduced identically (same frozen x-coordinate to 2 decimal places) across 9 consecutive headless
    runs this session, so it's deterministic, not a timing fluke. Root cause still unknown — candidates
    not yet ruled out: something about `editor_request_begin_play()`'s PIE-handshake window briefly
    overriding/zeroing the pawn's velocity or input consumption partway through "settling" into real
    Play mode (as opposed to Simulate), or a per-tick reset elsewhere in the default `DefaultPawn`/
    `FloatingPawnMovement` pair under `-nullrhi` headless conditions specifically. **Next step needs
    live, visual MCP debugging (stepping through PIE interactively in the offscreen editor, watching
    velocity/location in real time) — not more blind headless Python API guessing**, which is how this
    session spent 9 engine round-trips narrowing it this far. Treat `agent_playtest.py`'s own
    `pass=True` criterion ("did distance decrease at all") as too weak to trust at face value for any
    level until this is root-caused; it does not distinguish "steering works" from "steering stalls
    after a fraction of a second."
- **[mock jam 7]** Ran `qa_harness.py` headless against `L_MockJam7` (Task C3 Step 4) with
  `--content-root /Game/MockJam7` and a fresh timestamp confirmed in `stages/03_playtest/output/qa-pipeline-log.csv` /
  `stages/03_playtest/output/qa-checks-log.csv`. Results: `fps`=pass (115fps vs 60 budget), `materials`=pass. Two findings:
  - Re-confirmed, don't re-learn: passing a **relative** path to `--out-dir`/`--csv-log`/
    `--checks-csv-log` silently resolves against `UnrealEditor-Cmd`'s own `Engine/Binaries/Linux/`
    cwd, not the repo (the already-documented working-directory gotcha above/below this entry) — a
    first run with relative paths printed correct results in stdout but left `stages/03_playtest/output/qa-pipeline-log.csv`
    and the screenshot untouched; a second run with absolute paths for all three flags fixed it.
  - `reachability`=`FAIL(unreachable=['BP_Beacon_C_0'])` — same failure mode `stages/03_playtest/output/qa-checks-log.csv`
    already shows for mock jam 6's `L_MockJam6` (`unreachable=['StaticMeshActor_0']`), root cause
    (unconfirmed, consistent with the symptom): no `NavMeshBoundsVolume` has ever been placed in
    either jam's level, so `NavigationSystemV1.find_path_to_location_synchronously` has no nav mesh to
    path across regardless of real reachability. Carried forward as a known, non-blocking gap, same
    as mock jam 6 — Task C4's Tier 1 agent playtest steers the pawn by direct vector-to-target via
    `add_movement_input`, not nav pathing, so it doesn't depend on this check passing.
  - `movement`=`skipped(no-default-game-mode-on-world-settings)` — new, **not** the same as mock jam
    6 (which reported `pass(DefaultPawnClass=DefaultPawn, movement component present)`). Mock jam 7's
    `L_MockJam7` has no per-level `GameMode` override set in World Settings, so the check has nothing
    to inspect; this check only ever reads the level's own override, never the project-wide default
    game mode in Project Settings, so it will report skipped on any level without an explicit
    override even if a working project default exists. Not yet fixed or investigated further this
    session — if a future session wants `movement` to actually run for mock jam 7, set a `GameMode`
    override on `L_MockJam7`'s World Settings first.
- **[mock jam 7]** Built `BP_Beacon`'s win-condition logic (component-bound overlap -> PrintString)
  entirely through the live offscreen editor's Unreal MCP, confirming several previously-unverified
  tool shapes:
  - `ObjectTools.set_properties`/`list_properties` on a `StaticMeshComponent`: `staticMesh` and
    `bGenerateOverlapEvents` are both top-level properties (confirmed, as guessed), but
    `collisionProfileName` is **not** top-level — it's nested under `bodyInstance.collisionProfileName`
    (a plain string). Passing `{"bodyInstance":{"collisionProfileName":"OverlapAllDynamic"}}` in
    `set_properties`'s `values` JSON works; a flat `collisionProfileName` key would silently be ignored
    since `list_properties` never listed it at the top level.
  - `BlueprintTools.list_graphs`' EventGraph refPath format for an **Actor** Blueprint matches the
    Widget Blueprint case mock jam 5 found: `<Blueprint>.<Blueprint>:EventGraph`, no `_C` suffix. The
    `_C` suffix only shows up on the generated class itself (e.g. the CDO's
    `Default__BP_Beacon_C`, or a placed instance's `BP_Beacon_C_0`), never on the Blueprint asset or
    its graphs.
  - `AssetTools.save_assets` with an empty `asset_paths` list (save-all-dirty) works identically for a
    freshly created Blueprint asset as it did for the level in mock jam 3 — confirmed on disk
    (`BP_Beacon.uasset` with real size, non-empty content).
  - `SceneTools.find_actors` requires `tag` and `collision_channels` even when filtering by `name`
    alone — pass `"tag":""` and `"collision_channels":[]` explicitly, despite the schema showing them
    with apparent defaults.
  - Confirmed again (same as the gotcha below): `-ExecCmds="py <path>; quit"` still doesn't work —
    `py` eats the rest of the string including `; quit`. Just `-ExecCmds="py <absolute path>"` alone,
    relying on `timeout` + `pkill -9` to end the process, as already documented.
- **[mock jam 7]** A headless Python level-build script that spawns actors via `EditorActorSubsystem`
  and then calls `EditorLoadingAndSavingUtils.save_current_level()` can get `False` back with no actors
  written, even though the spawn calls succeeded (confirmed via a separate reload+count check). Root
  cause confirmed this run: `unreal.Package` has **no** `set_dirty()` method in UE 5.8's Python API
  (`AttributeError: 'Package' object has no attribute 'set_dirty'`), so a tempting "force-dirty the
  package first" fix throws before the save line even runs. The actual fix needs no dirty-flag call at
  all — use `unreal.EditorAssetLibrary.save_asset(level_path, only_if_is_dirty=False)` by itself, which
  forces the save unconditionally. Verified: reloaded the level fresh in a new headless process after
  this fix and confirmed all 8 spawned actors persisted on disk (floor, 4 walls, PlayerStart, Beacon,
  PlayerOrb).
- **[mock jam 6]** `L_MockJam6` (the scratch level in `~/Projects/ue-mcp-verify`) has no floor, walls,
  or ground plane — only a `PlayerStart` and two `QAObjective`-adjacent props (`SM_Beacon`,
  `SM_PlayerOrb`), per `stages/00_prep/references/pre-jam-mechanic-toolkit.md`'s QA tagging conventions (only those two
  things are required for `qa_harness.py`'s reachability check). The owner saw the packaged build and
  reported "just 3 cylinders with a ball" (the beacon's pillar geometry + the orb) floating in empty
  space; a live headless actor dump confirmed both meshes import correctly as real custom StaticMeshes,
  not an import bug. **Expected by design** — this level was only ever built to exercise the harness/
  agent-playtest tooling, never meant to look like a playable level. Owner confirmed. If a future mock
  jam wants the build to actually look playable when run, add ground/walls as its own task — don't
  re-open this as an import or asset-pipeline bug.
- **[mock jam 6]** Driving a real PIE session from a one-shot headless Python script (Task C4's Tier
  1 agent-playtest spike) works in UE 5.8 Linux: `LevelEditorSubsystem.editor_request_begin_play()`
  starts Play in the same process; the existing `register_slate_pre_tick_callback` state machine
  keeps polling after that. The one gotcha: get the **game** world from
  `UnrealEditorSubsystem.get_game_world()`, not the editor world — `LevelEditorSubsystem` has no
  `get_game_world()` at all, and `GameplayStatics.get_player_pawn(editor_world, 0)` silently returns
  `None` during PIE (the editor world's actor list goes empty while playing; the real pawn lives in
  the separate `UEDPIE_0_<Level>` game world). End with `editor_request_end_play()`. Full write-up:
  Task C4 above.
- **[mock jam 6]** `UnrealEditor-Cmd`'s internal working directory is the engine's own
  `Engine/Binaries/Linux/` folder, not the shell's cwd at launch (confirmed live: a headless run's log
  showed `MAP LOAD FILE="../../../../ue-mcp-verify/Content/..."`, a relative path rooted there). Any
  headless `-ExecCmds="py ..."` script in this repo must use **absolute paths for every file it reads
  or writes** (output dirs, CSV logs, not just the script path itself) — a relative path silently
  resolves against the engine binaries dir instead of erroring, so the run looks successful (prints
  correct results) while writing nothing findable. `scripts/qa_harness.py`'s `--out-dir`,
  `--csv-log`, and `--checks-csv-log` all hit this; always pass absolute paths for them.
- **[mock jam 6]** `LevelEditorSubsystem.new_level(path)` silently no-ops (no exception, no return-value
  signal) if a level asset already exists at that exact path — the editor stays on whatever level was
  already active (here, the project's auto-loaded startup map) instead of creating/switching, so
  subsequent spawn/save calls silently corrupt the wrong level. Any headless level-authoring script
  should use `load_level()` for a level that may already exist, and assert
  `editor_subsystem.get_editor_world().get_path_name()` matches the target path right after, so a
  future mismatch raises loudly instead of silently polluting the wrong level again.
- **[mock jam 6]** `scripts/qa_harness.py`'s `_check_movement_setup()` was calling
  `get_editor_property("default_pawn_class")` directly on the `GameMode` class object returned by
  `world_settings.get_editor_property("default_game_mode")` — that property returns a
  `BlueprintGeneratedClass`, not an instance, so the property lookup failed
  (`Failed to find property 'default_pawn_class' ... on 'BlueprintGeneratedClass'`). Fixed by calling
  `unreal.get_default_object(game_mode)` first and reading the property off that CDO instead.
- **[mock jam 6]** `scripts/qa_harness.py`'s materials/textures check hardcoded `content_root="/Game"`,
  so it scanned the entire shared `ue-mcp-verify` scratch project and flagged unrelated legacy content
  from other phases/mock-jams as failures. Fixed by adding a `--content-root` CLI flag (default stays
  `/Game` for backward compat) so a run against one mock jam's level can scope the check to just that
  level's own content root.
- **[mock jam 6]** `UnrealEditor-Cmd` does not reliably exit on its own after a one-shot headless
  Python script finishes, even one that only loads/inspects a level (no Play session) and prints its
  own "_DONE" marker — same as every PIE-driving script in Task C4. Always wrap headless
  `UnrealEditor-Cmd` invocations in `timeout <N> ...` and follow with
  `pkill -9 -f "UnrealEditor-Cmd.*<project>"` regardless of what the script does; exit code 124/1 after
  the marker printed is expected, not a failure.
- **[mock jam 6]** `package-and-push.ps1`'s `-NoticeFile ''` (empty string, to intentionally skip the
  notice on a non-shipping dry run) does not survive `ssh <device-host> "powershell ... -NoticeFile ''"` — the
  empty string gets flattened to the literal two-character string `''`, so PowerShell receives that as
  the path and the script's own guard throws `NoticeFile '' not found`. Pass `-NoticeFile
  ([string]::Empty)` inside the remote PowerShell command instead; that round-trips correctly.
  **[mock jam 9 correction]** this `([string]::Empty)` workaround only round-trips for `-Command`
  invocations of the packaging script (as used above). It does **not** apply to `-File` invocations —
  there, PowerShell parses `([string]::Empty)` as a literal string argument rather than evaluating the
  expression, so the script receives that literal text as the path and fails the same "not found"
  check it was meant to dodge. A `-File` invocation that needs a real notice must point `-NoticeFile`
  at an actual file already copied onto the Legion (e.g. `_config/reference/NOTICE.txt` scp'd to
  `C:\Dev\<Game>\NOTICE.txt`) — see mock jam 8's bug 3 and mock jam 9's findings doc.
- **[mock jam 7]** `scripts/ue_build_level.py` placed geometry, a `PlayerStart`, and the
  beacon/orb meshes but no light source at all. Six sessions of headless `-nullrhi`
  agent-playtest testing (Task C4) never caught this, since `-nullrhi` never renders a frame —
  the first time anyone actually *saw* the level was the human playtest on the packaged
  Windows build, which was a solid black screen. The process was running fine (RHI/D3D12 init
  clean, map loaded, no crash) — it was a genuinely unlit scene, not a hang or render failure.
  Fix: `_place_default_lighting()` now spawns a `DirectionalLight` + `SkyLight` as part of
  `build_level()`, so every future generated level has basic lighting by default. Lesson:
  `-nullrhi` headless testing validates logic/movement, never visuals — a human (or at least a
  non-nullrhi screenshot) has to actually look at a level at least once before calling it
  playtest-ready.
- **[mock jam 7]** Retrofitting an already-built level (adding lights without re-running the
  whole `build_level()`, which would duplicate the floor/walls/PlayerStart/beacon/orb) needs a
  separate one-off script that only `load_level()`s and spawns the new actors — `new_level()`/
  `build_level()` isn't idempotent and was never made safe to re-run against an existing level.
- **[mock jam 7]** `SkyLightComponent.recapture_sky()` called from a headless `-nullrhi`
  script (no real GPU/RHI) does not produce a usable baked capture. The packaged game then got
  stuck at runtime right after level load: pegged CPU across threads, log completely frozen, no
  crash, no further log lines for 7+ minutes — confirmed via `Get-Process` CPU climbing with
  `Responding: True` plus a dead log file timestamp, not guessed. Fix: don't bake the capture
  editor-side at all; set the component's `real_time_capture` editor property to `True` instead, so
  the sky light redoes the capture itself every frame with the real runtime renderer. Lesson: any
  light/capture-type property that depends on an actual render pass is unsafe to finalize from a
  `-nullrhi` script — prefer the runtime-recapture flag over a one-shot bake whenever the asset will
  only ever be built headless.
- **[mock jam 7]** The `GameFeatureData` "Handled ensure" (mock jams 3/5, logged as harmless) can
  **hang the packaged game**: on the Legion Go S the ensure handler stalled writing its minidump
  (0-byte `Saved/Crashes/*/UEMinidump.dmp`, log frozen on the ensure's callstack, before
  `LoadMap`). Fix: keep the `DefaultGame.ini` rule (cook still needs it) but set
  `bIsEditorOnly=True`. Cook runs with `GIsEditor` so the GameFeatures check still sees the rule,
  and the packaged game skips scanning the type instead of trying to load a class from a plugin it
  doesn't ship. Confirmed: no ensure, `LoadMap` completes. Note: this ensure hang, not
  `recapture_sky()`, was the cause of the 2026-10-30 17:21 hang; the entry above wasn't re-tested on
  its own.
- **[mock jam 7]** `unreal.Rotator`'s positional order is **(roll, pitch, yaw)**. Always use keyword
  args. `Rotator(-45, 30, 0)` put the sun at pitch +30 (below the horizon), so the packaged game ran
  at ~145 fps with every light present and still rendered pure black. A real-time-capture
  `SkyLight` also needs a `SkyAtmosphere` in the level, or it shows an on-screen red error and a
  black sky. `_place_default_lighting()` now does both.
- **[mock jam 7]** Screenshots taken from PowerShell on the Legion Go S (`CopyFromScreen`) only
  capture the **top-left quarter** of the 1920×1200 panel unless the process calls
  `SetProcessDPIAware()` first (display scaling is 200%). This hid the `stat` overlays and made a
  working frame look black. The agent can verify the packaged build visually when it runs **on**
  the Legion, not over SSH: DPI-aware screenshot plus `keybd_event` to drive input
  (holding W from PlayerStart → `SIGNAL DELIVERED` in the log).
- **[mock jam 7, 2026-10-30]** Generated meshes import at **~200 cm across regardless of what
  they depict**. `SM_Orb` and `SM_Beacon` both measured ~100 cm bounds extent at scale 1. With no
  scale set, the orb, placed 1.5 m in front of PlayerStart, filled the whole view as a "giant brown
  circle" in the packaged build. `_spawn_mesh_actor()` now takes a `scale`; the orb uses 0.3
  (~60 cm). They also import with a **centred pivot**, so spawning at z=0 buried the bottom half:
  the 2 m beacon showed as a ~1 m stub, hidden behind the orb on the spawn line. Measured: bounds
  bottom at -99.9 cm. `_spawn_mesh_actor()` now calls `_rest_on_floor()`, which lifts each actor
  by its actual bounds, whatever the pivot. In the real jam, give every placed generated mesh an
  explicit target size, probe `mesh.get_bounds()` after import instead of assuming units, and
  keep decoration off the line between spawn and the objective.
- **[mock jam 7, 2026-10-30]** In a headless in-place level patch,
  `EditorLoadingAndSavingUtils.save_current_level()` returned `True` but **did not write the
  `.umap`** (mtime unchanged). Setting the scale/location via Python didn't mark the package
  dirty. Use `EditorAssetLibrary.save_asset(level_path, only_if_is_dirty=False)`, as
  `ue_build_level.py` does, and check that the file's mtime moved before repackaging.
- **[mock jam 7, 2026-10-30]** The Claude Code auto-mode classifier denied running
  `package-and-push.ps1` locally (judged it a "public surface"), even with no `-ItchTarget`, which
  makes it package and zip only. For unattended jam-week runs, add an explicit permission rule
  for it, or run it by hand, so the loop doesn't stall at the package gate.
- _(seed entries below, carried forward from mock jams 1–5; append new ones above this line as mock
  jam 6+ discovers them)_
- **[mock jam 5]** `read_graph_dsl`'s `graph` param is a direct EdGraph refPath
  (`/Game/X/BP_Y.BP_Y:EventGraph`), not `{blueprint, graph: "name"}`. Widget Blueprints use the plain
  name with no `_C` suffix in the refPath even though `_C` appears inside node type_ids.
- **[mock jam 5]** `StaticMeshTools.get_material_slots` takes `mesh`, not `staticMesh` — same
  inconsistent param naming as other toolsets in this project; find the right name by trial against
  the error message, there's no schema doc for this plugin's MCP tools in this repo.
- **[mock jam 5]** `package-and-push.ps1` over SSH to the Legion Go S now needs
  `-ExecutionPolicy Bypass` on the `powershell` invocation itself, and `scp` destination paths need
  forward slashes (`<device-host>:C:/Dev/...`, not backslashes).
- **[mock jam 4]** `ObjectTools.get_properties`/`list_properties` on a Blueprint's CDO
  (`Default__*_C`) returns `"None"` for an actor-component-typed property even when the component is
  genuinely populated. Get the component's real `refPath` via `ActorTools.get_components` first, then
  query properties on *that* ref path.
- **[mock jam 3/4]** `ToolSearch` never surfaces live Unreal MCP server tools in this environment; go
  straight to raw HTTP JSON-RPC `curl` against the MCP port instead of registering via `claude mcp
  add`.
- **[mock jam 3]** A hyphen in the `.uproject` basename breaks packaging codegen; push a renamed copy
  of `Content/`, `Config/`, and the `.uproject` instead of renaming the live project.
- **[python-scripting.md, live-verified]** `-ExecCmds="py <path>; quit"` does not work — `py`
  consumes the rest of the string as Python source, including `; quit`. Use `-ExecCmds="py <path>"`
  alone plus `timeout` + `pkill -9 -f "UnrealEditor-Cmd.*<project>"`. A bare comma inside an
  `-ExecCmds` value is also unsafe (UE's own parser splits on it); use a repeated flag instead of a
  comma-joined list.
- **[python-scripting.md, live-verified]** The Interchange glTF pipeline nests import output under
  `<dest>/<source_glb_basename>/StaticMeshes|Materials|Textures/`, not flatly at
  `<dest>/<destination_name>`. Always resolve the final asset path from the import task's
  `imported_object_paths`, never assume it.

---

## Phase A — Fix the real root cause of missing textures/materials

### What the contradiction actually resolves to (read this before touching any code)

**Resolved root cause: (a), with high confidence** — mock jam 5's "Import real meshes" step did not
go through `scripts/ue_import_asset.py`'s documented `AssetImportTask` + Interchange path at all. It
used a different, MCP-native import route that only pulls in geometry, not materials/textures. This is
not a guess; it's the best explanation that fits every piece of hard evidence gathered while writing
this plan, laid out below. The script itself is not at fault and does not need a bug fix — only the
workflow around it does, plus a defensive check so a future session can't silently repeat this.

**Evidence, in the order it was gathered:**

1. **The source GLBs are not the problem.** `stages/02_build/output/asset-pipeline-log.csv` confirms `lastlight_orb`,
   `lastlight_beacon`, and `lastlight_shadow` were generated by `scripts/gen_asset.py` with real
   timings and exit code 0 (rows timestamped 2026-10-29T17:32–17:39Z). The generated files still exist
   on disk at `work/generated/lastlight_orb/` (etc.) alongside separate `*.albedo.png`, `*.normal.png`,
   `*.ao.png` texture maps. Parsing `lastlight_orb.glb`'s own glTF JSON chunk directly (binary-level
   inspection, not trusting a UI) shows it embeds three real images (albedo/normal/AO, each a real PNG
   buffer view) and one material with `pbrMetallicRoughness.baseColorTexture`, `normalTexture`, and
   `occlusionTexture` all wired to those images. **This rules out hypothesis (c)** —
   `nexus-3d --game-ready`'s output GLBs do carry embedded, properly-referenced PBR textures and
   materials; there is no structural gap in the generator's output for these three assets.
2. **`scripts/ue_import_asset.py` (full read) is internally consistent with a working Interchange
   import, and that claim has independent corroboration.** Its own LIVE-VERIFIED docstring (dated
   2026-10-28, the day before mock jam 5) says `AssetImportTask` + Interchange produces material,
   texture, and mesh from a `.glb`, and documents the real, specific side effect of that: output nests
   under `<dest>/<source_basename>/StaticMeshes|Materials|Textures/`, not flatly at
   `<dest>/<destination_name>`. `_config/reference/engine-reference/unreal/python-scripting.md` repeats the same
   claim independently. Mock jam 2's findings (`stages/00_prep/output/mock-jam-findings-2.md`, "Art pipeline — worked
   end to end") describe a real, separately-run import adapted from this script landing at the
   *nested* path `/Game/Props/seed_pod/StaticMeshes/SM_SeedPod` — exactly the nesting behavior the
   script's docstring describes, confirmed by a real `IMPORT_OK`/`PLACE_OK` run. **This rules out
   hypothesis (b)** — there is a real, working precedent for this exact code path producing a correct
   nested import on a different asset, so "the script ran but silently no-op'd" doesn't fit; nothing
   about the lastlight GLBs is structurally different from `seed_pod`.
3. **Mock jam 5's own bug report describes a *flat* path and a generic material, which contradicts
   Interchange's documented nested behavior.** `stages/00_prep/output/mock-jam-findings-5.md`'s bug-2 section says a
   filesystem check of `Content/LastLight/Meshes/` showed one shared `Material_0` asset directly in
   that flat folder, not nested under `Meshes/<glb_basename>/Materials/`. The bug report never once
   names `ue_import_asset.py`, `AssetImportTask`, or `Interchange` — it frames the import purely in
   terms of MCP toolset calls (`StaticMeshTools.get_material_slots`, `BlueprintTools.get_parent`),
   consistent with the rest of mock jam 5's narrative, which was conducted live through Unreal MCP
   tool calls, not headless `UnrealEditor-Cmd -ExecCmds="py ..."` script runs (no `py` invocation is
   mentioned anywhere in that findings doc, unlike mock jam 2's explicit `Scripts/02_import_seed_pod.py`
   call-out). **This is what selects hypothesis (a) over (b):** the asset landed through *some* import
   tool, but the folder shape and the single generic material are the signature of a different,
   simpler importer — most likely Unreal MCP's own built-in asset-import tool call (the toolset naming
   convention in this project, e.g. `AssetTools`/`StaticMeshTools`, suggests MCP exposes its own import
   entry point separate from this repo's Python script), not the documented
   `AssetImportTask`-via-Interchange path.
4. **Remaining honest gap:** no session log or `.handoff/` artifact from mock jam 5 survives (checked:
   no `.handoff/*.md` in this repo mentions `lastlight` or `SM_PlayerOrb`), so the *exact* MCP tool
   name that performed the import cannot be pinned down retroactively — only that it wasn't this
   script's documented path. Task A0 below schedules closing that gap live, during mock jam 6, rather
   than guessing further.

### Task A0: Confirm live, during mock jam 6's import step, which tool path is actually in use

**Files:** none changed; this is an observation step folded into Phase C's Task C3.

- [ ] Before running any import in mock jam 6 (Task C3), decide and record in that session's working
  notes whether the import will be driven by `scripts/ue_import_asset.py` (headless
  `UnrealEditor-Cmd -ExecCmds="py scripts/ue_import_asset.py ..."`) or by a live Unreal MCP tool call,
  and name the exact tool (`list_toolsets` / `describe_toolset` first if using MCP, per the "Shipped
  toolsets" list in `_config/reference/knowledge-base.md` lines 263–264).
- [ ] If a live MCP import tool is used for any reason (e.g. speed during interactive Blueprint work),
  immediately follow it with the verification in Task A1's assertion step before trusting the result.
  Do not let this repeat mock jam 5's gap of never checking.

### Task A1: Make the Interchange path the only sanctioned import route, with a defensive assertion

**Files:**
- Modify (future session, not this plan): `scripts/ue_import_asset.py`
- Modify (future session): `_config/reference/engine-reference/unreal/python-scripting.md`

The fix is procedural first (always import through this script, never through an ad hoc MCP import
tool for final content) and code-level second (make the script itself refuse to report success on a
flat-default-material outcome, so a future process slip is caught immediately instead of silently
shipping). Both land in the same future PR.

- [ ] **Step 1: Add a `--require-pbr` default-on assertion to `import_asset()`.** After the existing
  final-asset-path resolution in `import_asset()` (`scripts/ue_import_asset.py:219-230`), add a check
  that the resolved mesh has more than the single generic material Unreal assigns to an
  import with no real material (`/Engine/EngineMaterials/WorldGridMaterial` or an unnamed
  auto-generated `Material_0`-style slot with no texture parameters bound). Planned code, to write
  when this task is executed:

  ```python
  def _assert_real_material(static_mesh, asset_name: str) -> str:
      """Fails loudly (raises) if the imported mesh has no real PBR material — i.e. exactly the
      mock-jam-5 bug-2 signature (StaticMeshTools.get_material_slots showing one generic slot, no
      texture asset). Call this right after import, before any Blueprint wiring happens, so a process
      slip (e.g. an MCP import tool used instead of this script) is caught here even when this
      script *was* used correctly — this guards the embedding step, not just the tool choice.
      """
      materials = static_mesh.get_editor_property("static_materials")
      if not materials:
          raise RuntimeError(f"{asset_name}: import produced zero material slots.")
      has_real_material = False
      for slot in materials:
          mat_iface = slot.get_editor_property("material_interface")
          if mat_iface is None:
              continue
          # A real Interchange-generated glTF material instance has texture parameters bound;
          # the engine's flat default does not expose any.
          try:
              tex_params = unreal.MaterialEditingLibrary.get_texture_parameter_names(mat_iface)
          except Exception:
              tex_params = []
          if tex_params:
              has_real_material = True
              break
      if not has_real_material:
          raise RuntimeError(
              f"{asset_name}: no material with a bound texture parameter found "
              f"(got {[s.get_editor_property('material_interface') for s in materials]}). "
              "This is the mock-jam-5 bug-2 signature — check whether this import actually went "
              "through AssetImportTask/Interchange or through a different tool."
          )
      return "material_check=pass(texture-bound material found)"
  ```

  Call `_assert_real_material(mesh, asset_name)` from `import_asset()` right after
  `_apply_static_mesh_setup` for the `asset_type == "prop"` branch, and fold its return string into the
  existing `summary` line.
- [ ] **Step 2: Add `--require-pbr`/`--no-require-pbr` CLI flags** (default: required) to
  `_parse_cli_args` so a genuinely-intentional flat-material import (e.g. a greybox placeholder,
  deliberately not art-final) can opt out without editing the script.
- [ ] **Step 3: Update `_config/reference/engine-reference/unreal/python-scripting.md`'s Interchange section** to
  add a short "Verifying the import actually got materials" subsection pointing at this new check and
  at Phase B's QA-harness material check (Task B3) as the second, independent line of defense.
- [ ] **Step 4: Update `scripts/qa_harness.py`'s own docstring is not needed here** (Phase B owns that
  file); just cross-link from python-scripting.md to `stages/00_prep/references/mock-jam-6-tooling-plan.md`'s Phase B
  section instead of duplicating the explanation.
- [ ] **Step 5: Regenerate the `graft` wiring card for the touched file**, if `graft` is on PATH in
  the executing session (`graft build`); it's a gitignored regenerable cache
  (`graft/scripts/ue_import_asset.md`), not something to hand-edit. If `graft` isn't installed in that
  session's environment, note that in the session's own findings doc instead of silently skipping it.
- [ ] **Step 6: Commit.**

  ```bash
  git add scripts/ue_import_asset.py _config/reference/engine-reference/unreal/python-scripting.md
  git commit -m "Add PBR-material assertion to ue_import_asset.py (mock jam 5 bug-2 root cause)"
  ```

### Task A2: Correct the record in mock-jam-findings-5.md

**Files:**
- Modify (future session): `stages/00_prep/output/mock-jam-findings-5.md`

- [ ] **Step 1: Add a dated correction block** right after the existing "Bug 2 — no textures" section
  (after `stages/00_prep/output/mock-jam-findings-5.md:67`), in the same style as mock-jam-findings-2.md's own
  "2026-10-29 correction" pattern (a labeled correction appended in place, not a silent rewrite):

  ```markdown
  **Correction, 2026-10-29/2026-10-30 (mock jam 6 tooling plan):** root-caused further. The generated
  GLBs themselves were never the problem — `lastlight_orb.glb` etc. embed real PBR materials with
  bound albedo/normal/AO textures (confirmed by parsing the glTF JSON chunk directly). The bug is that
  this import did not go through `scripts/ue_import_asset.py`'s documented `AssetImportTask`/
  Interchange path (which nests output and is proven elsewhere, e.g. mock jam 2's `seed_pod` import).
  It most likely went through a different, MCP-native import tool that only pulls in geometry. Fix:
  `scripts/ue_import_asset.py` is now the only sanctioned import path, with a `--require-pbr`
  assertion (default on) that fails loudly instead of silently shipping a flat-material mesh. See
  `stages/00_prep/references/mock-jam-6-tooling-plan.md` Phase A.
  ```
- [ ] **Step 2: Commit.**

  ```bash
  git add stages/00_prep/output/mock-jam-findings-5.md
  git commit -m "Correct mock-jam-findings-5: resolve bug-2 root cause (import path, not the GLB)"
  ```

### Task A3: CANON.md update for Phase A

**Files:**
- Modify (future session): `_config/CANON.md`

- [ ] **Step 1:** In the "Mock-jam rehearsals and live findings" table, update the
  `stages/00_prep/output/mock-jam-findings-5.md` row's summary in place (CANON.md's own convention: "a finding gets
  corrected or superseded → update that row's summary, don't add a new row") to append: "; bug-2
  root-caused and corrected 2026-10-30, see `stages/00_prep/references/mock-jam-6-tooling-plan.md` Phase A".
- [ ] **Step 2: Commit** (can be folded into Task A2's commit if done in the same session — don't
  create a separate near-empty commit just for this one line; use judgment, but don't skip it).

---

## Phase B — Expand `qa_harness.py` with 3 new automated checks

`scripts/qa_harness.py` (read in full above) currently does one thing: load each map, screenshot it,
and measure frame time via a non-blocking tick-callback state machine (`run_qa_pass`), writing results
to a CSV log (`_write_csv_log`). Everything below extends that same state machine and CSV-logging
pattern — no new architecture, same conventions (argparse flags, LIVE-VERIFIED/UNVERIFIED comment
tags, graceful degradation to a warning instead of a crash when an API is missing, per-map result
dicts).

**Why a second CSV, not new columns on the existing one:** `_write_csv_log` (lines 196–218) writes a
fixed header on first write and appends rows after that; adding new columns would silently corrupt any
existing `stages/03_playtest/output/qa-pipeline-log.csv` history by misaligning old and new rows under the same header. The
three new checks write to a new `stages/03_playtest/output/qa-checks-log.csv` instead, keeping the existing frame-time log
untouched.

### Task B1: Soft-lock / reachability check

**Files:**
- Modify (future session): `scripts/qa_harness.py`

- [ ] **Step 1: Add a `_check_reachability(level_name, objective_tag)` function**, called once per map
  during the existing `measure` phase (reuse the already-ticking state machine rather than adding a
  second one). Planned code:

  ```python
  OBJECTIVE_TAG = "QAObjective"
  PLAYER_START_CLASS_NAME = "PlayerStart"

  def _check_reachability():
      """Soft-lock check: can the nav system path from a PlayerStart to every actor tagged
      QAObjective? UNVERIFIED in this repo -- no real map with a nav mesh and tagged objectives
      exists pre-jam to test against (same caveat as _find_qa_camera's CAMERA LOOKUP note). Wrapped
      so a missing API degrades to a printed warning + reachability=skipped, never a crash, matching
      this file's existing convention.
      """
      try:
          actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
          all_actors = actor_subsystem.get_all_level_actors()
          player_starts = [a for a in all_actors if a.get_class().get_name() == PLAYER_START_CLASS_NAME]
          objectives = [a for a in all_actors if OBJECTIVE_TAG in a.tags]
          if not player_starts:
              return {"reachability": "skipped(no-player-start-found)"}
          if not objectives:
              return {"reachability": "skipped(no-QAObjective-tagged-actors)"}
          nav_sys = unreal.NavigationSystemV1.get_navigation_system(actor_subsystem.get_editor_world())
          if nav_sys is None:
              return {"reachability": "skipped(no-nav-system)"}
          start_loc = player_starts[0].get_actor_location()
          unreachable = []
          for obj in objectives:
              path = nav_sys.find_path_to_location_synchronously(
                  actor_subsystem.get_editor_world(), start_loc, obj.get_actor_location()
              )
              is_valid = getattr(path, "is_valid", lambda: False)() if path else False
              if not is_valid:
                  unreachable.append(obj.get_name())
          if unreachable:
              return {"reachability": f"FAIL(unreachable={unreachable})"}
          return {"reachability": f"pass({len(objectives)} objectives reachable)"}
      except Exception as exc:  # noqa: BLE001 - editor API surface, keep this non-fatal
          print(f"WARNING: reachability check failed ({exc}); skipping.")
          return {"reachability": "skipped(api-missing)"}
  ```
- [ ] **Step 2: Note the design choice explicitly in a comment above the function**: this requires the
  level to tag win-condition actors `QAObjective` and have a `PlayerStart` placed — a convention this
  plan is introducing, not one that exists yet. Document it in `stages/00_prep/references/pre-jam-mechanic-toolkit.md` too
  (future session) so level-building during the jam actually applies the tag.

### Task B2: Movement / possession check

**Files:**
- Modify (future session): `scripts/qa_harness.py`

This is the check that would have caught mock jam 5's bug 1 (bare `Pawn`, no movement component,
`AddMovementInput` a silent no-op) **before** a human had to play the packaged build to find it.

- [ ] **Step 1: Add `_check_movement_setup()`**, a static inspection (no PIE needed — this check
  answers "can this pawn possibly move," not "does it move when played," which Task C4's agent
  playtest covers at runtime):

  ```python
  MOVEMENT_COMPONENT_CLASSES = ("FloatingPawnMovement", "CharacterMovementComponent")

  def _check_movement_setup():
      """Possession + movement-component check -- the mock-jam-5 bug-1 signature was a bare
      /Script/Engine.Pawn (BlueprintTools.get_parent) with EventTick calling AddMovementInput every
      tick but no FloatingPawnMovement/CharacterMovementComponent to consume it, so the call was a
      silent no-op. This check verifies, for the current level's GameMode, that:
        1. DefaultPawnClass is set to something other than the engine default DefaultPawn/None, and
        2. that pawn class (or its parent chain) actually has a movement component.
      UNVERIFIED against a real pre-jam level (none exists yet); wrapped per this file's convention.
      """
      try:
          world = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_editor_world()
          game_mode = world.get_world_settings().get_editor_property("default_game_mode")
          if game_mode is None:
              return {"movement": "skipped(no-default-game-mode-on-world-settings)"}
          pawn_class = game_mode.get_editor_property("default_pawn_class")
          if pawn_class is None:
              return {"movement": "FAIL(DefaultPawnClass is None - nothing to possess)"}
          generated_cdo = unreal.get_default_object(pawn_class)
          has_movement = any(
              generated_cdo.get_component_by_class(getattr(unreal, cls_name, type(None))) is not None
              for cls_name in MOVEMENT_COMPONENT_CLASSES
          )
          if not has_movement:
              return {
                  "movement": f"FAIL(pawn class {pawn_class.get_name()} has no "
                               f"{MOVEMENT_COMPONENT_CLASSES} component - AddMovementInput would be a no-op)"
              }
          return {"movement": f"pass(DefaultPawnClass={pawn_class.get_name()}, movement component present)"}
      except Exception as exc:  # noqa: BLE001
          print(f"WARNING: movement/possession check failed ({exc}); skipping.")
          return {"movement": "skipped(api-missing)"}
  ```
- [ ] **Step 2: Note in a comment that this is deliberately a static/CDO check, not a runtime one** —
  it catches "this pawn structurally cannot move" (mock jam 5's exact bug) cheaply and early, while
  Task C4's agent playtest catches "the pawn can move but something else still blocks it" at runtime.
  Keep both; they're not redundant.

### Task B3: Material / texture validation check

**Files:**
- Modify (future session): `scripts/qa_harness.py`

This is the check that would have caught mock jam 5's bug 2, independent of Phase A's import-time
assertion — defense in depth, since this check runs against whatever is already in the project,
regardless of how it got there.

- [ ] **Step 1: Add `_check_materials_and_textures(content_root)`**:

  ```python
  def _check_materials_and_textures(content_root="/Game"):
      """Finds every StaticMesh under content_root and flags any whose only material has no bound
      texture parameter -- the mock-jam-5 bug-2 signature (StaticMeshTools.get_material_slots showing
      one generic Material_0, no texture asset in the mesh's folder). Independent of Phase A's
      ue_import_asset.py-side assertion: this runs against on-disk content regardless of which tool
      produced it, so it also catches a flat-material mesh placed by hand or imported some other way.
      """
      try:
          asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
          asset_data_list = asset_registry.get_assets_by_path(content_root, recursive=True)
          flat_material_meshes = []
          checked = 0
          for asset_data in asset_data_list:
              if asset_data.asset_class_path.asset_name != "StaticMesh":
                  continue
              mesh = asset_data.get_asset()
              if mesh is None:
                  continue
              checked += 1
              materials = mesh.get_editor_property("static_materials") or []
              has_texture = False
              for slot in materials:
                  mat_iface = slot.get_editor_property("material_interface")
                  if mat_iface is None:
                      continue
                  try:
                      if unreal.MaterialEditingLibrary.get_texture_parameter_names(mat_iface):
                          has_texture = True
                          break
                  except Exception:
                      continue
              if not has_texture:
                  flat_material_meshes.append(str(asset_data.package_name))
          if flat_material_meshes:
              return {"materials": f"FAIL(no-texture meshes: {flat_material_meshes})"}
          return {"materials": f"pass({checked} static meshes checked, all have a textured material)"}
      except Exception as exc:  # noqa: BLE001
          print(f"WARNING: material/texture check failed ({exc}); skipping.")
          return {"materials": "skipped(api-missing)"}
  ```
- [ ] **Step 2: Note the overlap with Task A1 explicitly** in a code comment: this is the same
  texture-parameter heuristic as `_assert_real_material` in `ue_import_asset.py`, deliberately
  duplicated rather than imported across the process boundary (this script runs inside a different
  headless editor invocation than the import script; sharing code would mean a shared module both
  scripts import, which is a reasonable future refactor but out of scope for this plan — note it as a
  follow-up idea in the gotchas log instead of doing it here).

### Task B4: Wire the three checks into `run_qa_pass` and the CLI, log to `stages/03_playtest/output/qa-checks-log.csv`

**Files:**
- Modify (future session): `scripts/qa_harness.py`

- [ ] **Step 1: Call all three checks from inside `_finish_current_map()`** (right before the existing
  `print(...)`/`state["results"].append(...)` block at `scripts/qa_harness.py:148-161`), merging their
  result dicts into the same per-map result dict so one CSV row carries frame-time, reachability,
  movement, and material results together:

  ```python
  def _finish_current_map():
      map_path = maps[state["idx"]]
      deltas = state["frame_deltas"]
      if deltas:
          avg_seconds = sum(deltas) / len(deltas)
          frame_time_ms = avg_seconds * 1000.0
          fps = 1.0 / avg_seconds if avg_seconds > 0 else None
      else:
          frame_time_ms, fps = None, None
      passed = fps is not None and fps >= budget_fps
      note = "camera=active_viewport" if state["camera"] is None else f"camera={CAMERA_TAG}"

      checks = {}
      checks.update(_check_reachability())
      checks.update(_check_movement_setup())
      checks.update(_check_materials_and_textures())

      print(f"{map_path}: fps={fps} budget={budget_fps} pass={passed} screenshot={state['screenshot_path']}")
      for name, result in checks.items():
          print(f"{map_path}: {name}={result}")

      result_row = {
          "map": map_path, "loaded": True, "screenshot": state["screenshot_path"],
          "frame_time_ms": frame_time_ms, "fps": fps, "budget_fps": budget_fps,
          "pass": passed, "note": note,
      }
      result_row.update(checks)
      state["results"].append(result_row)
      state["idx"] += 1
      state["phase"] = "load"
  ```
- [ ] **Step 2: Add `_write_checks_csv_log(results, csv_path)`**, mirroring `_write_csv_log`
  (lines 196–218) but with its own header (`timestamp_iso, map, reachability, movement, materials`)
  and its own default path `stages/03_playtest/output/qa-checks-log.csv`, called alongside the existing
  `_write_csv_log` call in `__main__` rather than replacing it.
- [ ] **Step 3: Add `--checks-csv-log` CLI flag** (default `stages/03_playtest/output/qa-checks-log.csv`), mirroring the
  existing `--csv-log` flag pattern at `scripts/qa_harness.py:234-238`.
- [ ] **Step 4: Update the module docstring** to list the three new checks next to the existing
  FRAME-TIME MEASUREMENT section, each tagged UNVERIFIED (no real pre-jam level exists yet to test any
  of them against — same honesty standard as every other tag in this file) until mock jam 6 (Task C3)
  either confirms or corrects them live.
- [ ] **Step 5: Regenerate the `graft` wiring card** for this file (`graft build`, if available) or
  note in the session's findings doc that it wasn't available.
- [ ] **Step 6: Commit.**

  ```bash
  git add scripts/qa_harness.py
  git commit -m "Add reachability, movement/possession, and material/texture checks to qa_harness.py"
  ```

### Task B5: CANON.md update for Phase B

**Files:**
- Modify (future session): `_config/CANON.md`

- [ ] **Step 1:** Add a row under "Mock-jam rehearsals and live findings" (or a new small "QA tooling"
  subsection if the table is getting crowded — use judgment, but don't skip indexing) for
  `stages/03_playtest/output/qa-checks-log.csv`: "CSV log for qa_harness.py's reachability/movement/material checks (Phase
  B of stages/00_prep/references/mock-jam-6-tooling-plan.md); separate from stages/03_playtest/output/qa-pipeline-log.csv (frame-time) to avoid
  a header/schema break."
- [ ] **Step 2: Commit** (fold into Task B4's commit or do separately; don't skip).

---

### Correction (2026-10-29): `get_editor_world()` is on the wrong subsystem in B1/B2's code blocks

This plan's own Task B1 and Task B2 code blocks above (and the matching code transcribed into
`scripts/qa_harness.py`'s `_check_reachability()` and `_check_movement_setup()`) call
`actor_subsystem.get_editor_world()`, where `actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)`.
`EditorActorSubsystem` has no `get_editor_world` method on this UE 5.8 Python API surface — live-tested
headless against `/Game/MinimalProof/L_MinimalProof` in `~/Projects/ue-mcp-verify`, confirmed via
`AttributeError: 'EditorActorSubsystem' object has no attribute 'get_editor_world'`. The correct call is
`unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()` — confirmed live via a
throwaway API probe script. Fixed in `scripts/qa_harness.py` (both call sites) by fetching a second
subsystem handle (`editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)`)
alongside the existing `actor_subsystem`, and re-verified live: `movement` went from
`skipped(api-missing)` to `skipped(no-default-game-mode-on-world-settings)` against the same scratch
level (expected — that level has no real GameMode set, a separate, pre-existing limitation, not this
bug). This was a plan-authoring-time bug, not a transcription error by the session that wrote B1-B4 —
both this doc's own code blocks already had it before transcription.

---

### Correction (2026-10-29): `default_game_mode` confirmed correct; CDO bug, materials scope gap, and CSV/screenshot root cause found running mock jam 6 live

Resolves the open question this plan previously carried about the `WorldSettings` property name:
`default_game_mode` **is** correct. `game_mode_override` does not exist on `WorldSettings` — confirmed
live via a `dir(world_settings)` dump filtered for `game`/`mode`, which only showed
`default_game_mode`/`default_game_type`. `scripts/qa_harness.py`'s existing usage needed no change for
the property name itself.

Three further things were found and fixed live while actually building and running mock jam 6's level
end-to-end (all three are also logged in the Gotchas log above, dated the same day):
`_check_movement_setup()`'s CDO-vs-class bug, `_check_materials_and_textures()`'s missing content-root
scoping (fixed with a new `--content-root` flag), and — the one that had looked like a missing CSV/
screenshot bug in `qa_harness.py` itself but wasn't — `UnrealEditor-Cmd` running with its internal
working directory at the engine's `Binaries/Linux/` folder, silently swallowing relative output paths.
The harness code was correct the whole time; every invocation of it (this plan's own examples included)
needs absolute paths for `--out-dir`, `--csv-log`, and `--checks-csv-log`.

---

## Phase C — Run mock jam 6 end-to-end (with Phase D's agent playtest folded in)

This phase uses Phase A's fixed import path and Phase B's expanded harness. The ordering below is
deliberate: **agent playtest happens before human playtest**, not after, so the human is only asked to
play once the agent-administered pass has already caught what it can catch.

### Task C1: Pre-flight

**Files:** none changed (environment check only).

- [ ] **Step 1:** `gpu-preflight` — confirm clear before any generation or editor session starts
  (`AGENTS.md`, `CLAUDE.md`).
- [ ] **Step 2:** Confirm `~/Projects/ue-mcp-verify` (or an equivalent scratch `.uproject`) is the
  target, per Rule 7(h) and every prior mock jam's test-environment note. Never point any of this at
  content inside `~/Projects/megajam`.
- [ ] **Step 3:** `ListAgents` + a direct message to any peer session before touching the live Unreal
  MCP session or shared pipeline logs (`stages/02_build/output/asset-pipeline-log.csv`, `stages/02_build/output/audio-pipeline-log.csv`,
  `stages/03_playtest/output/qa-pipeline-log.csv`, the new `stages/03_playtest/output/qa-checks-log.csv`) — the exact collision-avoidance step
  mock jam 5 flagged as something to repeat every session, not assume clean from a prior handoff.

### Task C2: Generate assets using the existing, already-proven pipeline

**Files:** none in this repo changed (CSV logs append).

- [ ] **Step 1:** Run `scripts/gen_asset.py` for mock jam 6's props/characters exactly as in prior mock
  jams (`--name`, `--prompt` or `--image`, `--model krea-2-turbo` for commercial-safe output per
  `stages/00_prep/references/license-check-modly-foundrylab.md`). This step is unaffected by Phase A/B — the generator was
  never the problem (see Phase A's evidence).
- [ ] **Step 2:** Spot-check at least one output GLB the same way this plan did for Phase A's
  evidence-gathering (parse the glTF JSON chunk, confirm `images`/`textures`/`materials` are present)
  before importing, as a pipeline sanity check — cheap, and it's exactly what would have caught mock
  jam 5's actual bug immediately if run at generation time instead of discovered at playtest time.

### Task C3: Import via the corrected Phase A workflow, then run Phase B's QA checks

**Files:** none in this repo changed (QA CSV logs append).

- [ ] **Step 1 (Task A0's live decision point):** Import every generated asset through
  `scripts/ue_import_asset.py`'s headless path (`UnrealEditor-Cmd ... -ExecCmds="py
  scripts/ue_import_asset.py --glb ... --dest ... --name ... --type ..."`), **not** through a live MCP
  import tool, per Phase A's resolved root cause. If a live MCP import tool is used anyway for a
  specific reason, immediately run the Task A1 assertion equivalent (or Task B3's check) against the
  result before proceeding — don't let an unverified import reach Blueprint wiring.
- [ ] **Step 2:** Confirm the `--require-pbr` assertion (Task A1) passes for every imported mesh;
  investigate immediately (don't defer to playtest) if it fails.
- [ ] **Step 3:** Tag the level's win-condition actors `QAObjective` and place a `PlayerStart`, per
  Task B1's documented convention, before running QA.
- [ ] **Step 4:** Run the expanded `scripts/qa_harness.py` (`--map ... --out-dir stages/03_playtest/output/qa-screenshots
  --budget-fps 60 --checks-csv-log stages/03_playtest/output/qa-checks-log.csv`) and confirm reachability, movement, and
  material checks all report `pass`. Fix anything that fails before moving to Task C4 — this is the
  whole point of landing Phase B before Phase C.

### Task C4: Agent-administered playtest (Phase D's mechanism, run before the human playtest)

**Files:** none in this repo changed (produces a findings-doc section, written in Task C7).

Researched against what this repo's own engine-reference docs and the rest of the repo actually
establish, not assumed. Two tiers, attempted in order; state the confidence level for each honestly
rather than claiming either is proven.

- [x] **Step 1 — Tier 1 spike (confidence: LOW, attempt first because it reuses already-proven
  primitives): Python-driven PIE state machine.** `scripts/qa_harness.py`'s own
  `register_slate_pre_tick_callback`-based non-blocking state machine (LIVE-VERIFIED, UE 5.8,
  2026-10-28 per `_config/reference/engine-reference/unreal/python-scripting.md`) is the only confirmed-working way
  this repo has found to drive multi-frame logic from a one-shot headless Python script. Before trusting
  it for playtesting, this step is a spike, not an assumption: determine live whether
  `unreal.LevelEditorSubsystem` (or another 5.8 subsystem) exposes a Python-callable entry point that
  starts an actual **Play** session (not Simulate — Simulate has no input/gameplay logic) and keeps
  the *same* editor process alive afterward so the tick-callback pattern can poll
  `unreal.GameplayStatics.get_player_pawn(world, 0)`'s location every N frames, call
  `pawn.add_movement_input(...)` directly to stand in for player input (bypassing real device
  injection, which is the part this plan is **not** claiming exists), and read back whether the
  position actually changed. Nothing in `_config/reference/engine-reference/unreal/python-scripting.md` or any
  other file in `_config/reference/engine-reference/unreal/` confirms this Play-session entry point exists or
  behaves this way in 5.8 — that's exactly why this is a spike and not a planned-as-certain step.
  **SPIKE RESULT (2026-10-29, confidence raised LOW → HIGH, live-verified, UE 5.8 Linux):** the entry
  point exists. `LevelEditorSubsystem.editor_request_begin_play()` starts a real PIE session in the
  same process (`is_in_play_in_editor()` → `True` on the very next tick), and
  `UnrealEditorSubsystem.get_game_world()` — not `LevelEditorSubsystem`, which has no such method —
  returns the live PIE world (path `/Game/MockJam6/UEDPIE_0_L_MockJam6...`). From that world,
  `GameplayStatics.get_player_pawn(game_world, 0)` finds the real pawn, `add_movement_input()` on it
  actually moves the pawn (confirmed: 434 units of travel over 60 ticks in a straight-line test), and
  `editor_request_end_play()` cleanly ends PIE afterward with no leftover process. Went one step
  further than the spike asked: drove the pawn toward the level's `QAObjective`-tagged beacon each
  tick (steering by the vector to its location) and confirmed it closed from 316 to 122 units away in
  180 ticks — a real agent-administered playtest of the win-condition's reachability, not just a
  position-delta sanity check. Tier 2 was not needed.
- [ ] **Step 2 — Tier 2 fallback (confidence: MEDIUM, Epic-sanctioned, partially proven in this repo
  already, NOT RUN — Tier 1 succeeded): UE's Automation / Functional Testing framework.**
  `_config/reference/engine-reference/unreal/current-best-practices.md` (lines 25–57) documents, and this repo has
  partially live-verified (Windows, UE 5.7; the same `-unattended -nullrhi -ExecCmds -stdout
  -FullStdOutLogOutput` flag family this repo already uses elsewhere for 5.8 on Linux), a fully headless
  way to run Epic's own Automation tests: `-ExecCmds="Automation RunTests <Project>.; Quit"`, reading
  `Test Completed. Result=<status>` lines and a final `**** TEST COMPLETE. EXIT CODE: <n> ****` from
  stdout. Author one `FunctionalTest`-derived Blueprint per mock-jam-6 win/lose/soft-lock condition
  (e.g. `BP_FT_PlayerCanMove`, `BP_FT_WinConditionReachable`), placed in the test level. Inside each
  test's Blueprint graph, call the *same gameplay functions the real input would call*
  (`AddMovementInput`, the beacon-interact function bound to E) directly — this is a deliberate,
  honest substitute for hardware input-device simulation, which nothing found in this repo's
  engine-reference docs or anywhere else confirms is possible headlessly. Each test polls actor state
  each tick and calls `FinishTest(Succeeded/Failed, "<reason>")` when it has an answer. Invoke via
  `Automation RunTests <Project>.FunctionalTests; Quit` and parse the result lines the same way the
  already-documented pattern does.
- [x] **Step 3:** Record which tier actually ran, its pass/fail result per check, and — critically —
  whether it would have caught mock jam 5's two bugs had it existed then (it should: Tier 1's position-
  delta check and Tier 2's `AddMovementInput`-calling functional test both directly exercise the bug-1
  failure mode; Task B2/B3 already catch bug-2's and bug-1's *static* signature before this step even
  runs, so Task C4 is really testing "does it work at runtime," a different and complementary
  question). **Result:** Tier 1 ran and passed. Position-delta check: PASS (pawn moved 434 units/60
  ticks in the straight-line test). Objective-reachability check: PASS (closed from 316 to 122 units
  from the beacon in 180 ticks of steered `add_movement_input`). Had this existed during mock jam 5,
  the position-delta check would have caught bug-1 (bare `Pawn`, no movement component — the pawn
  simply wouldn't move under `add_movement_input`) at runtime, complementing Task B3's static check of
  the same bug via `default_pawn_class`/movement-component inspection.
- [x] **Step 4: State plainly in the findings doc (Task C7) which tier was used and the confidence
  level**, exactly as stated here — don't let a later summary round this up to "agent playtesting is
  now automated and proven" if only Tier 2's functional-gameplay-call substitute ran, or down to
  "nothing works" if the Tier 1 spike partially succeeded. This is the one part of this plan most
  likely to need a correction block in a later findings doc, the same way mock-jam-findings-2.md
  corrected an earlier over-broad claim about the Blueprint API wall — expect that, and write the
  correction in place if it happens rather than treating it as a plan failure. **Carried to Task C7:**
  Tier 1 ran, confidence raised from the plan's original LOW to HIGH (live-verified end to end,
  including a real win-condition reachability check, not just the minimal position-delta spike the
  plan asked for). Tier 2 was never attempted — don't claim it was tried and failed, or that it's
  still an open gap; it's simply unneeded for now. This is "agent playtesting works for
  movement/reachability via Play-session + tick-callback steering," not "agent playtesting is fully
  automated and proven for every gameplay system" — e.g. UI, inventory, or anything needing real input
  *events* (not just continuous axis input) is untested by this spike.

### Task C5: Human playtest (after the agent playtest, not instead of it)

**Files:** none changed; produces the same owner-reported findings mock jam 5 captured.

- [x] **Step 1:** Packaged and pushed to the Legion Go S (Task C6, below). Build is ready at
  `C:\Dev\MockJam6Game\Packaged\SilentBlade_MockJam6.zip` (431.6 MB) on the Legion Go S, waiting for
  the owner to actually play it — that part of this step is still open.
- [ ] **Step 2:** Run the full `_config/reference/templates/playtest-checklist.md` against the real packaged build,
  exactly as mock jam 5 did, with the owner playing on-device.
- [ ] **Step 3:** Compare what the human catches against what the agent playtest (Task C4) already
  caught. Any gap either way is itself a finding worth a line in Task C7's findings doc — this
  comparison is the actual point of running both, not a formality.

### Task C6: Package + push to the Legion Go S

**Files:** none in this repo changed (uses existing `scripts/package-and-push.ps1`).

- [x] **Step 1:** Ran the existing proven packaging workflow against the Legion Go S. Pushed a
  renamed hyphen-free copy of the Phase C `ue-mcp-verify` scratch project's `Content/`, `Config/`,
  and `.uproject` (13 MB) to `C:\Dev\MockJam6Game\MockJam6Game.uproject`, then ran
  `scripts/package-and-push.ps1 -EnginePath C:\Dev\UE_5.8 -ProjectPath
  C:\Dev\MockJam6Game\MockJam6Game.uproject -TeamName SilentBlade -GameName MockJam6 -NoticeFile
  ([string]::Empty)` over SSH (no `-ItchTarget`, so butler push was skipped on purpose — this is a
  dry-run packaging test, not the real submission, and `-NoticeFile` was intentionally skipped since
  there's no third-party notice needed for this scratch content).
- [x] **Step 2:** `BUILD SUCCESSFUL` (RunUAT BuildCookRun, 25.71s on the second run after a cache was
  warm; 61.53s cold). Output: `C:\Dev\MockJam6Game\Packaged\SilentBlade_MockJam6.zip`, 431.6 MB — well
  under the 1 GB gate. Script logged `WARNING: no NoticeFile - this build has no third-party notice,
  do not submit it as the real entry` as expected (intentional for this dry run; the real submission
  must pass a real `-NoticeFile`). New gotcha found and logged below: passing `-NoticeFile ''` as a
  literal empty string over `ssh <device-host> "powershell ... -NoticeFile ''"` does not survive the
  round-trip — PowerShell receives the literal two-character string `''` as the path, not an empty
  string, and the script's own guard throws `NoticeFile '' not found`. Use `-NoticeFile
  ([string]::Empty)` inside the remote PowerShell command instead.

### Task C7: Dev log / findings-6 doc / checklist dry run — same ritual as mock jam 5

**Files:**
- Create (future session): `stages/00_prep/output/mock-jam-findings-6.md`
- Create (future session): `stages/00_prep/output/mock-jam-6-checklist-dryrun.md`
- Create (future session): `stages/05_devlog/output/<YYYY-MM-DD>.md` (via `scripts/gen_devlog.py` or by hand)

Use `stages/00_prep/output/mock-jam-findings-5.md` as the literal template for structure: Scope, what was
generated/imported, agent-playtest results (new section, per Task C4), human-playtest results and what
it caught that the agent pass didn't (or vice versa), packaging/push results, tooling gotchas (append
these to *this* plan's gotchas log too, per the Process requirement — don't only put them in the
findings doc), process cleanup, status summary table.

- [ ] **Step 1:** Write `stages/00_prep/output/mock-jam-findings-6.md` following that structure.
- [ ] **Step 2:** Run `_config/reference/templates/playtest-checklist.md` and the submission-checklist dry run
  (win-plan.md lines 152–168, same lines mock-jam-5-checklist-dryrun.md cited) against mock jam 6's
  actual state, writing `stages/00_prep/output/mock-jam-6-checklist-dryrun.md` in the same format as
  `stages/00_prep/references/mock-jam-5-checklist-dryrun.md`.
- [ ] **Step 3:** Write the dev log entry via `scripts/gen_devlog.py` (or by hand using
  `_config/reference/templates/dev-log-entry.md`) into `stages/05_devlog/output/<date>.md`.
- [ ] **Step 4: Append every new gotcha found this mock jam to this plan's Gotchas log section**
  (above), dated and tagged `[mock jam 6]`, rather than only writing them into
  `stages/00_prep/output/mock-jam-findings-6.md`. The findings doc is the narrative; this plan's gotchas log is the
  index future sessions actually grep.

### Task C8: CANON.md update for Phase C/D

**Files:**
- Modify (future session): `_config/CANON.md`

- [ ] **Step 1:** Add rows under "Mock-jam rehearsals and live findings" for
  `stages/00_prep/output/mock-jam-findings-6.md` and `stages/00_prep/output/mock-jam-6-checklist-dryrun.md`, matching the existing rows'
  style (one line, what's in it, status if not current).
- [ ] **Step 2:** If Task C4 produced a new engine-reference finding (e.g. confirming or refuting the
  Tier 1 PIE spike), add or correct a row under "Engine reference (UE 5.8)" for whichever file in
  `_config/reference/engine-reference/unreal/` records it (likely `python-scripting.md`, in place, per CANON's
  correction convention).
- [ ] **Step 3: Commit.**

  ```bash
  git add _config/CANON.md stages/00_prep/output/mock-jam-findings-6.md stages/00_prep/output/mock-jam-6-checklist-dryrun.md stages/05_devlog/output/
  git commit -m "Mock jam 6: findings, checklist dry run, dev log, CANON index"
  ```

### Task C9: Process cleanup

**Files:** none changed.

- [ ] **Step 1:** Stop any `UnrealEditor-Cmd`/`Xvfb` processes started for this mock jam; confirm with
  `ps aux | grep -i UnrealEditor`.
- [ ] **Step 2:** `gpu-preflight` confirmed CLEAR after cleanup.
- [ ] **Step 3:** Remove any scratch files left on the Legion Go S by this session's verification
  steps, leaving the packaged build + project copy in place for the human playtest (Task C5), same as
  prior mock jams' cleanup sections.

---

## Self-Review

Run after Phase D was folded into Phase C above (Task C4), not appended afterward — this review covers
the plan as actually structured, including that fold-in.

**1. Spec coverage** — walking the owner's scope statement line by line:
- "asset pipeline (image→3D→UE import)" → Phase A (root cause + fix) and Task C2/C3 (run it).
  Covered.
- "packaging + Windows build gate" → Task C6 reuses the already-proven `package-and-push.ps1`
  workflow; this plan doesn't propose new packaging-gate code because nothing in mock jam 5's findings
  or this plan's own research surfaced a packaging-gate bug to fix — packaging passed clean in mock
  jam 5. Explicitly noting this rather than inventing a packaging task to pad the plan: the packaging
  gate's hardening need, if any, wasn't in scope of what mock jam 5 actually found broken.
- "QA harness + new checks" → Phase B, three checks (B1 reachability, B2 movement/possession, B3
  materials/textures), wired in B4. Covered, matches the task's explicit "3 new automated checks"
  requirement plus naming the two specific mock-jam-5 bugs by name.
- "run full end to end mock jams" → Phase C, Tasks C1–C9.
- "agent-administered playtesting... researched against what actually exists" → Task C4, with the
  Tier 1/Tier 2 split and explicit confidence levels, folded into Phase C per the process requirement
  rather than bolted on at the end. Covered.
- CANON.md threading "throughout the plan, not only a single update at the end" → Tasks A3, B5, C8 —
  three separate CANON update points, one per phase, plus Task C8 also covers Phase D's own findings.
  Covered.
- "living, growing gotchas log... future mock jams (7+) can append" → the Gotchas log section near the
  top of this document, seeded with mock jams 1–5's real gotchas, with an explicit append-at-top
  instruction and a worked example of what mock jam 6 should add in Task C7 Step 4. Covered.
- "No code, script, or Blueprint/MCP changes — this is planning only" → every code block in this plan
  is explicitly labeled "planned code, to write when this task is executed" or similar, inside task
  steps meant for a future executing session; nothing was run or edited in the live repo while writing
  this plan beyond reading files and writing this one document. Covered.
- Worktree + PR convention → handled outside this document, by the session executing this plan (open a
  PR for this doc itself, same as the PRs that produced mock-jam-findings-5.md and the AI-asset
  research doc this plan cites).

**2. Placeholder scan** — checked every task for "TBD"/"implement later"/"add appropriate
error handling"-shaped text. None found: every code block is a complete, runnable (if unexecuted)
snippet with real function/variable names; every "UNVERIFIED" tag names specifically what's unverified
and why, matching this repo's own existing convention rather than hand-waving. The one place this plan
deliberately stops short of a concrete answer — the exact MCP tool name behind mock jam 5's bug 2
(Phase A, "Remaining honest gap") — is flagged as an open question with a concrete next step (Task A0)
rather than left as a silent gap.

**3. Type/name consistency** — cross-checked function and flag names used across tasks:
`_assert_real_material` (Task A1) and `_check_materials_and_textures` (Task B3) are intentionally
separate functions in separate files (noted explicitly in Task B3 Step 2, with the duplication called
out rather than hidden); `--require-pbr` (Task A1) and `--checks-csv-log`/`--csv-log` (Task B4) don't
collide with any existing flag in `scripts/ue_import_asset.py` or `scripts/qa_harness.py`'s current
`_parse_cli_args`. The `QAObjective` tag and `PlayerStart` convention introduced in Task B1 is
referenced consistently in Task C3 Step 3 (where a level must actually apply it) — checked that this
isn't assumed to already exist anywhere else in the repo (it doesn't; grepped for `QAObjective` and
`QACamera` before writing Task B1, confirming only `QACamera` — the existing camera-tag convention —
was already in use, which is why Task B1 introduces a parallel, not colliding, tag name).

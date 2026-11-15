---
tier: tested
source: stages/00_prep/output/mock-jam-findings-9.md
updated: 2026-11-10
---

# Importing our generated meshes and fixing material warnings

Mostly tested on 5.8.4; the two newest Tips ran on 5.9. Re-test the rest on 5.9 before relying on it.

## Tip: import a sound file while the editor is OPEN (`--live`) — watch-folder route, proved by hand 2026-11-09
- **Command (lead agent only, editor started with the MCP port):**
  `python3 scripts/ue_import_asset.py --live --project /abs/PROJECT_DIR --wav /abs/jump.wav --dest /Game/Audio/ --name Jump`
  prints `Created /Game/Audio/S_Jump` after the editor has imported and saved the file. **The time varies:**
  measured on the real UE 5.8 editor (MockSlime) as **57 s** on 2026-11-09 ~17:5xZ (first import) and
  **4 s** on 2026-11-09 18:38Z (a later import; log showed `FactoryCreateFile SoundWave` then `Saving Package`).
  A first import versus a warm editor is the guess; the cause is UNTESTED (n=2). Plan for the slow case: the
  script waits up to 120 s by default (`--wait SECONDS` raises it); never set a wait under about 90 s.
  The asset name is the file name, so the script always names it `S_<name>`.
- **Real-editor facts (UE 5.8, MockSlime):** the editor has no Python tool and no audio import tool.
  `import_file` exists only in the Texture, StaticMesh, SkeletalMesh, CurveTable, DataTable and StringTable
  tools; `TextureTools.import_file` on a `.wav` says "TextureFactory does not support .wav".
- **The route:** (1) over MCP, `call_tool` on the ConfigSettings toolset, tool `SetSectionProperties`
  (`containerName` Editor, `categoryName` General, `sectionName` LoadingSaving,
  `propertiesJson` `{"bPromptBeforeAutoImporting": false}`) returns `true`; (2) copy the wav to
  `<project>/Content/<dest>/S_<name>.wav`; (3) the editor imports AND saves `S_<name>.uasset` by itself,
  about 57 s later in the one sample (log: `FactoryCreateFile: SoundWave with SoundFactory`, then `Saving Package`).
- **Gotcha:** the default is prompt ON, which shows an Import / Don't Import popup and imports nothing (no
  asset after 60 s). If `--live` times out, look for that popup. The script copies via `.part` then renames,
  so the editor never sees a half file, and refuses if the `.uasset` already exists.
- **Headless now refuses** while another UnrealEditor process has the project open (exit 3, message names the
  `--live` command). Meshes (`--glb`) stay headless-only because that path carries the PBR check: close the editor.
- **Status:** the hub proved the route by hand; the script is checked against a fake editor with only the three
  meta tools (`tests/test_ue_import_asset.py`). Only `.wav` is supported; convert mp3/ogg first.

## Tip: import only through `scripts/ue_import_asset.py`
- **Why:** an MCP-native import pulled in geometry only. The GLBs did carry PBR textures, but the mesh showed a
  flat default material ("really basic"). The script uses the `AssetImportTask`/Interchange path and has a
  `--require-pbr` check, on by default, that fails loudly.
- **How to check:** `StaticMeshTools.get_material_slots` should list real slots, and the textures exist in Content.

## Tip: "missing usage flag Nanite" on an imported glTF mesh
- **Why:** Interchange makes a `MaterialInstanceConstant` whose parent chain ends at the plugin material
  `/InterchangeAssets/gltf/M_Default`. `bUsedWithNanite` exists only on the base `Material`. Setting the
  instance's usage-flag bitmask override did NOT silence the warning (tried and verified).
- **Fix that worked:** set `bUsedWithNanite = true` on `M_Default` itself, recompile, save, repackage. Note it is
  shared engine-plugin content on the build machine too, and six other project materials inherit from it.
- **How to check:** `Select-String` the packaged log for `missing usage flag Nanite`; no match.

## Tip: "sky light with real-time capture" warning
- **Why:** the level had a SkyLight with `bRealTimeCapture = true` and no `SkyAtmosphere`.
- **How to check:** add a `SkyAtmosphere` actor (do not just turn capture off, that changes the look).

## Tip: audio import routes and formats (5.8 and 5.9)
- **Why:** MCP cannot import a wav on 5.8 or 5.9; `TextureTools` and `StaticMeshTools` `import_file` refuse it, and `execute_tool_script` has no `unreal` module (`mock-jam-findings-12.md:45`). The route proven in mock 12: `UnrealEditor-Cmd X.uproject -ExecutePythonScript=SCRIPT.py -unattended -nullrhi` with the editor closed, a script that builds `unreal.AssetImportTask` objects. `import_sound` refuses `.ogg` (convert with ffmpeg to wav, or use a raw `AssetImportTask`; `asset-test-ue59-2026-11-10.md:21`).
- **How to check:** the log prints the new `S_` asset path; wire it with `Audio|PlaySound2D` over MCP.

## Tip: sourced mesh quirks measured on 5.9 (asset test 2026-11-10, n=1)
- **Why:** from `asset-test-ue59-2026-11-10.md:18-43`:
  - A skeletal GLB (a Kenney door with a joint) crashes `import_asset` (`add_simple_collisions` TypeError); the asset still imports.
  - Poly Haven FBX imports as separate meshes and ignores `destination_name`; four LODs come in as four meshes (use LOD0).
  - A Kenney house is knee-high; scale about x4.
  - `get_simple_collision_count` reads 0 on 5.9 (it ignores convex hulls); `import_asset` was fixed on 2026-11-11 to count them.
  - Nanite is on by default; the HDRIBackdrop plugin must be enabled and its dome z-fights a floor at Z=0.
  - Poly Haven normals are OpenGL; use the `nor_dx` map for hand-built materials.
- **How to check:** list the destination folder after each import and read the sizes in the editor before you place anything.

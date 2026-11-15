# Sourced-asset smoke test on UE 5.9 (2026-11-10)

Throwaway project `~/scratch/asset-test-59/AssetTest59.uproject` (made with `scripts/new-mock-project.py`,
outside the megajam repo). Engine: `~/Projects/UnrealEngine-5.9` (5.9.0-preview-1). Nothing was imported into
megajam and `sourced_assets.py add` was not run. Import driver (calls megajam's `scripts/ue_import_asset.py`
`import_asset()` / `import_sound()` headless): `~/scratch/asset-test-59-tools/import_and_build.py`; raw results:
`~/scratch/asset-test-59-tools/results.json`. Headless import of everything took about 15 s once the editor was up.

Screenshots (looked at, not committed): `~/scratch/asset-test-59-tools/shots/04-assettest-final.png` and `03-assettest-closeup-ph-crate-tree.png`.
It shows the brick floor (Poly Haven Red Brick, tiled material), Poly Haven Kloofendal sky on an HDRI Backdrop,
Kenney houses (x1 and x4), Kenney tree/rock/crate, the Poly Haven boulder and crate, and a 180 cm cylinder for scale.

## Per-pack result

| Pack (sample) | Import | Scale | Materials | Collision | Licence / flags |
|---|---|---|---|---|---|
| Kenney Prototype Kit (`crate-color.glb`) | OK via `import_asset` | 50 cm cube, fine | colormap texture bound, PBR check pass | yes (see note 1) | CC0 |
| Kenney Prototype Kit (`door-garage.glb`) | **Crashes `import_asset`**: the GLB has a joint, so Interchange makes a **SkeletalMesh** and `add_simple_collisions` raises TypeError. Asset itself imports and renders | small | ok | n/a | CC0 |
| Kenney Nature Kit (`tree_default.glb`, `rock_largeA.glb`) | OK | tree 171 cm tall, rock 1 m wide: small but usable | bark/leaf, dirt/grass materials bound | yes | CC0 |
| Kenney City Kit Suburban (`building-type-a` GLB and FBX) | OK, GLB and FBX identical size | **house is 130x103x83 cm: knee-high. Scale about x4 for a walkable house** | colormap bound | yes | CC0 |
| Kenney Impact Sounds (`.ogg`) | **`import_sound` refuses `.ogg`** (wav only). Raw `.ogg` through a plain `AssetImportTask` works (SoundWave). ffmpeg ogg->wav then `import_sound` works | - | - | - | CC0 |
| Poly Haven Wooden Crate 01 (FBX) | Imports, but **as 3 meshes** (body `wooden_crate_011`, lid, latch), flat in the dest folder, **`destination_name` ignored**; `import_asset` reports and sets up only the first mesh (the lid) | 83x41x32 cm, real-world | diffuse/rough/metal/normal bound; parts line up (close-up shot) | yes | CC0 |
| Poly Haven Boulder 01 (FBX) | Imports, but **the FBX's LOD0-LOD3 come in as 4 separate meshes**; use `boulder_01_LOD0` (Nanite is on anyway) | 1.8 m, real-world | bound | yes | CC0 |
| Poly Haven Red Brick (texture set) | 3 JPGs import as Texture2D; hand-built tiled material (diff + nor_dx + ARM) renders right | - | normal set to TC_Normalmap, ARM to TC_Masks, both sRGB off | - | CC0 |
| Poly Haven Red Brick (glTF sample) | OK via `import_asset` (Interchange builds the PBR material itself) | 139 cm | bound | yes | CC0 |
| Poly Haven Kloofendal sky (`.hdr` 4K) | OK: imports as **TextureCube**; works in the HDRIBackdrop actor (enable plugin `HDRIBackdrop`) | - | - | - | CC0 |

Not tested: the other 6 Kenney packs and 9 Poly Haven files (same formats as the samples above), Kenney music/UI
sound packs (same `.ogg` issue applies), packaging/cooking any of this.

## Notes

1. **Collision is there, but the check reads 0.** In 5.9 `EditorStaticMeshLibrary.get_simple_collision_count()` returns 0
   for every mesh, while `body_setup.agg_geom` holds 2 shapes (Interchange's own + the NDOP18 that `import_asset` adds).
   So: do not trust `get_simple_collision_count` on 5.9; there are 2 overlapping hulls per mesh (harmless, slightly wasteful).
   Cause (found 2026-11-11): that call counts only boxes/spheres/capsules, never convex hulls. `import_asset` now counts
   simple + convex shapes and keeps Interchange's hull instead of adding a second (see python-scripting.md, Collision).
2. Every imported mesh has **Nanite on** by default in 5.9.
3. **HDRIBackdrop's ground dome z-fights a floor at Z=0.** Put the floor 1-2 cm above the backdrop, or lower the backdrop.
4. Poly Haven FBX normals are **OpenGL** (`nor_gl`) EXRs; Interchange bound them and the crate looked right, but for
   hand-built materials use the `nor_dx` map (texture ZIPs have it) or flip green.
5. `-ExecCmds="py file.py; quit"` on 5.9 passes `; quit` into the Python call (SyntaxError) and the editor never quits.
   End the script with `unreal.SystemLibrary.quit_editor()` instead. (`ue_import_asset.py`'s docstring shows the `; quit` form.)
6. `launch-editor.sh` uses the repo scope (MemoryMax=28G), not 16G; the live editor ran under that.

## Fab (9 claimed items)

The 5.9 engine ships a **Fab plugin with an MCP toolset** (`FabToolset.FabToolset`: `SearchFabListings`,
`GetFabListingDetails`, `SearchFabMyLibrary`, `InstallFabListing`, `FabSignIn`). Loaded in the scratch editor.
Read-only calls work without sign-in; library search and install say **"Not signed in to Fab"**.
Per the plugin source, an `unreal-engine` asset pack built for an older version installs into 5.9 (only newer
versions and old code plugins are refused). Nothing was installed (needs sign-in; and installs belong in the jam project, inside the window).

| Item | Formats | Install route into 5.9 | AI flag |
|---|---|---|---|
| Underground Tunnel | unreal-engine, UE_5.8 asset_pack | `InstallFabListing` after sign-in (5.8 pack into 5.9: allowed by plugin, not tried). Seller says it is built for baked lighting / Lumen off | `aiTrainingForbidden=true` |
| SciFi Beast06 Bull | unreal-engine UE_5.8 asset_pack (+unity) | same as above | `aiTrainingForbidden=true` |
| 3D Platformer Game Bundle | unreal-engine, **complete_project**, UE 4.27-5.8, `installOptions` empty | **No in-editor install.** Needs Epic Launcher (Legion, Windows): create a 5.8 project from it, then migrate. Owner OK needed (gameplay code) | `aiTrainingForbidden=true` |
| Wooden Barrel, Rusty Metal Barrel, Historic Crate Wood Old 03, Granite Rock, Small Beach Rock (Quixel) | fbx, gltf, converted-files | `InstallFabListing` with `fbx`/`gltf` after sign-in; same Interchange path as Poly Haven FBX above | not forbidden (null) |
| Forest Floor (Quixel surface) | texture-set, gltf | `InstallFabListing` (`gltf`) after sign-in | not forbidden |

Note: `GetFabListingDetails` today shows the three limited-time items as `free:false` (the listing price); they are
already in the library per LEDGER-PRE, so this should not matter, but the library search after sign-in confirms it.

### Owner steps for Fab (one time, before the window)

1. Start any 5.9 editor with MCP, e.g.
   `~/Projects/megajam/scripts/launch-editor.sh ~/scratch/asset-test-59/AssetTest59.uproject`
2. Sign in to Fab: open the editor's Fab tab and click Sign in (menu location in 5.9 not checked; or let the agent
   call `FabSignIn`, which only opens the browser). In the browser, sign in to the owner's Epic account and approve. Sign-in persists across editor restarts on this machine.
3. Check: the agent runs `mx.py call FabToolset.FabToolset SearchFabMyLibrary '{"Count":12}'` and sees the 9 items.
4. Platformer bundle only (if wanted, after deciding on gameplay code): on the Legion, Epic Launcher > Library > Fab
   > the bundle > Create Project (UE 5.8), then migrate the needed folders into the jam project.

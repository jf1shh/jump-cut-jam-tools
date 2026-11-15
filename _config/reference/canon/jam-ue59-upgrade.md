---
tier: epic
source: _config/reference/engine-reference/unreal/ue59-release-notes.md; https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-9-release-notes; https://forums.unrealengine.com/t/2852840
updated: 2026-11-10
---

# Moving the jam from UE 5.8.4 to UE 5.9 Preview: what to do differently

The owner ordered the move to "UE 5.9 MegaJam Preview" (tag 5.9.0-preview-1, commit acf0265, source build in `~/Projects/UnrealEngine-5.9`). 5.8.4 stays as the fallback. Tier is `epic` because only some items were run here; each Tip says which: [observed] = we ran it on 2026-11-10 (5.9 editor, copy of the mock project), [docs] = Epic docs, [source] = engine diff only. Full list: `_config/reference/engine-reference/unreal/ue59-release-notes.md`. Epic gave no statement on whether the jam requires 5.9 (UNCONFIRMED; check the rules page).

## Tip: start the Linux editor with the X11 video driver
- **Why:** under KDE Wayland the 5.9 editor fails in SDL init ("did not add any displays"). [observed] The flag is not new; 5.8.4 has it too.
- **How to check:** `SDL_VIDEODRIVER=x11` in the environment, or `-sdlvideodriver=x11` on the command line. The editor window appears.

## Tip: enable "All Toolsets" in every new project
- **Why:** the MCP server starts with the editor, but the toolset plugins are off by default (Epic known issue UE-412135), so agents see no level or asset tools. [docs] [forum]
- **How to check:** Edit > Plugins > "All Toolsets", or add `{"Name":"AllToolsets","Enabled":true,"TargetAllowList":["Editor"]}` to the `.uproject`. Restart the editor, reconnect the agent. `list_toolsets` then returns many toolsets.

## Tip: wait for MCP and use the new tool names
- **Why:** the port listened only after about 195 s on our test project [observed]; mock 16 measured 14.2 s [observed], so the 300 s wait stays as a ceiling. `describe_toolset` is gone; the meta-tools are `list_toolsets`, `describe_toolsets`, `describe_tools`, `call_tool`. [observed]
- **How to check:** poll the port (`ss -ltnp | grep :8010`) instead of assuming a crash. `describe_toolsets` takes toolset names (add `include_schemas:true` for schemas); `describe_tools` takes `Toolset.Tool`. Calls run one at a time and Claude Code gives up near 120 s, so keep calls short. [docs]

## Tip: `call_tool` arguments are an object; a CodeBlock is an object too
- **Why:** `arguments` must be a JSON object. A CodeBlock parameter has `Content` and `Language`; a plain string fails to import. [source] [observed]
- **How to check:** `{"toolset_name":"PythonScriptingTools","tool_name":"execute_python","arguments":{"script":{"Content":"...","Language":"Python"}}}`. It returns the value of the last expression; `print` goes to `LogPython`, not the result. [observed] Imports must be at the top level and `from x import *` is rejected; send one script for many edits. [docs]

## Tip: use the new ini section name
- **Why:** `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]` logs a deprecation warning. [observed] It is still redirected, but write the new name.
- **How to check:** `[/Script/ModelContextProtocol.ModelContextProtocolSettings]` with `ServerPortNumber=8010`, or keep `-ModelContextProtocolPort=8010` (the default is 8000, which Nexus holds). `bAutoStartServer` is already true. [docs] [source]

## Tip: copy the project, do not convert it; expect a DDC rebuild
- **Why:** Epic advises copying. The default DDC graphs lost the "Local" and "Shared" stores, so the first open may rebuild through Zen. [forum] [source]
- **How to check:** commit first and open the copy in 5.9. If it will not open, wipe `Saved`, `Intermediate` and `DerivedDataCache` in the copy.

## Tip: Windows packaging needs a newer SDK and an older compiler
- **Why:** the Windows SDK main version is 10.0.26100.0 (minimum 10.0.22621.0, was 10.0.19041.0); the .NET 4.8 targeting pack is required; Visual Studio 2026's 14.51 toolchain is flagged as a miscompile with memory corruption and has no fix. UBT bans every 14.51 build, and the Visual Studio 2022 minimum rose to 17.14. These matter when something compiles (a C++ module or a source-built engine); whether a Blueprint-only package on a Launcher 5.9 build needs them is UNTESTED. [source]
- **How to check:** before the first Windows build, run `scripts/legion_preflight.py` and check the SDK and toolchain on the Legion by hand.

## Tip: the Legion needs a matching 5.9 install (now a source build at `C:\Dev\UE_5.9`)
- **Why:** engine versions must match across the two machines (see `jam-packaging-windows`); a 5.8.4 Legion cannot open or cook a 5.9 project. (our reasoning from `jam-packaging-windows`, not run) Update 2026-11-10 [observed, read-only]: the Legion has a 5.9 **source** build at `C:\Dev\UE_5.9` (task `UE59Build`); the editor finished at 21:00 PT. The scripted helper-tools stage failed (`exit=1`) on cmd quoting in `_build-logs\ue59_build.ps1` line 25 (cmd drops the outer quotes when the `/c` string holds more than two; fix wraps the whole argument in one more pair), so ShaderCompileWorker, UnrealPak and CrashReportClient were rebuilt by hand. *Superseded:* "install 5.9 via the Launcher". *Update (mock 16, 2026-11-10):* the first 5.9 Win64 package worked (370.2 MiB zip, itch build #2354706) after 9 missing AutomationTool files were restored; see `jam-legion-ship-preflight` and `jam-packaging-windows`. *Superseded:* "No 5.9 Win64 package has been made yet."
- **How to check:** `ssh <device-host>` and read `C:\Dev\UE_5.9\_build-logs\status.txt` (every stage `exit=0`, manual tools done); `legion_ship.py PROJECT --engine C:\Dev\UE_5.9 --dry-run`; then the Wed 12:00 throwaway Win64 package. On a source build keep the Development config (a Shipping package compiles more, untested).

## Tip: keep these 5.9 features off the critical path
- **Why:** Epic's own known issues or experimental status: Web target, Unreal Canvas, Lumen World Cache, Adaptive Voxel OIT, Python Blueprint root swaps (UE-411502), scripted Deformer Graph undo (UE-410941), Dataflow pin edits with a comment box (UE-411097). [forum] [docs]
- **How to check:** use the 5.8-proven route; try a 5.9 feature only in a scratch project.

## Tip: Fab toolset exists; do not count on MetaHuman, CommonUI, CaptureManager or Mass toolsets
- **Why:** `FabToolset` loaded in the 5.9 editor on 2026-11-10 (search, details, install; the owner must sign in once). [observed] *Superseded (2026-11-10):* "do not count on a Fab toolset" (source diff). MetaHuman, CommonUI, CaptureManager and Mass are still listed as not part of 5.9. [source]
- **How to check:** `list_toolsets` in the editor; if a toolset is missing, use the Python route. Details and the `aiTrainingForbidden` flag: `jam-sourced-assets-ledger`.

## Tip: `scripts/mx.py` is updated for 5.9 (it used to call only `describe_toolset`)
- **Why:** the helper was written for 5.8. Updated 2026-11-10 (branch `feat/ue59-switch`): it probes `tools/list` once; with `describe_toolsets` present it calls that (`toolset_names`, `include_schemas`), else `describe_toolset`. `mx.py py SCRIPT` and `mx.py shot` send a CodeBlock when the tool's schema asks for one. Unit-tested against fakes, then live-smoked on the 5.9 editor on 2026-11-10 (mock 15 / `AGENTS.md`): `toolsets`, `describe PythonScriptingTools`, `py`, `shot` and `step_shot` (STEP_SHOT_OK) worked. *Superseded:* "not yet run on a live 5.9 editor". `force_save_level.py` on 5.9 is unit-tested only.
- **How to check:** run `scripts/mx.py toolsets` and `scripts/mx.py describe PythonScriptingTools` against the 5.9 editor.

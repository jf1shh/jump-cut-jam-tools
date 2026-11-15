# Jam-day start runbook

Source: `stages/00_prep/output/dress-rehearsal-2026-11-04.md` (fixes 3 and 4, owner-only items). Window: 2026-11-12 00:00 ET
(Nov 11, 9:00 PM PT) to 2026-11-15 8:59 PM ET. Before the window opens, nothing here creates gameplay,
levels or art (Rule 7(h)).

**Read first, every work block: `_config/reference/canon/jam-top-lessons.md`** (one screen: the 15 rules from mocks 10-15
that most change our odds, each with its source). Index of everything else: `_config/CANON.md`.

## 1. Free the GPU (first step, every session)

Lemonade (`lemond`) keeps a model in VRAM while idle, and `gpu-preflight` reports `BLOCKED` until it is
unloaded (seen 2026-11-04: Qwen3-Coder-30B at ctx 65536, 15.86 GB VRAM).

```bash
lemonade unload
gpu-preflight   # must print "CLEAR — safe to start a large job."
```

Only then open the editor or start a generation job. One GPU workload at a time. When the GPU work is
done, restore Lemonade with `--ctx-size 32768` (never 8192): `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768`.
*Superseded (2026-11-10, execution plan ruling C3):* "use the ctx value `gpu-preflight` prints (32768 vs 65536 open)".

## 2. Every UE editor launch passes the MCP port

The plugin default port 8000 is held by the Nexus backend (uvicorn), so the editor must serve 8010.
Nothing in a project's config sets it, so pass the flag on every launch (own scope, per `AGENTS.md`):

```bash
systemd-run --user --scope --unit=megajam-job-$(date +%H%M%S) -p MemoryHigh=26G -p MemoryMax=28G -p MemorySwapMax=8G -- \
  <UE5.9>/Engine/Binaries/Linux/UnrealEditor <path-to>/<Project>.uproject \
  -ModelContextProtocolStartServer -ModelContextProtocolPort=8010 -nosplash
```

Prefer `scripts/launch-editor.sh <Project>.uproject`: it picks the engine (5.9 by default; `UE_VERSION=5.8` or
`--ue58` for the 5.8.4 fallback) and exports `SDL_VIDEODRIVER=x11`, which the 5.9 editor needs under KDE Wayland
(without it: "InitSDL ... no displays"). 5.9 can take about 195 s before :8010 listens; the default wait is 300 s (`WAIT_TIMEOUT`). If the editor log says "HttpListener unable to bind" the script stops that editor and exits 9: wait a few seconds and run it again.

Also pin the port in the jam project once it exists (the repo has no editor config yet; the project is
created inside the window), in `Config/DefaultEditorPerProjectUserSettings.ini` (not DefaultEngine.ini):

```ini
[/Script/ModelContextProtocol.ModelContextProtocolSettings]
ServerPortNumber=8010
[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]
ServerPortNumber=8010
```

(First name is 5.9's, second is 5.8.4's; `new-mock-project.py` writes both there, so edit both if you change the port. The `AllToolsets` plugin goes in the `.uproject`, not an ini.)

**Keep Auto Start Server off** in project/editor config (the default; do not turn it on in Editor Preferences,
and do not set `bAutoStartServer=True` in any ini). The server starts only from the launch line above
(`-ModelContextProtocolStartServer`). Why: the MCP plugin is an Editor module, so it also loads inside the
cook commandlet. With Auto Start on, a cook tries to bind the same port; if an editor already holds 8010 it
logs `LogHttpListener: Error: unable to bind`, and `-CrashForUAT` turns that Error into exit code 1 even
though the cook worked. Even with no editor open, every cook would start an MCP server for nothing
(Epic forum topic 2735398, UE 5.8.0, no Epic reply, not stated as fixed in 5.8.x notes we saw). Keep the
port flag even after pinning; it costs nothing.

**To test (Legion still untested; Linux run 2026-11-10, below):**
- [ ] One Legion cook (scratch project, MCP plugin enabled, Auto Start off): `RunUAT BuildCookRun` exits 0.
  Expect the 5.9 `.uproject` problem found in the Linux run below; test with the fixed MCP entry.
- [x] One Linux cook while the editor holds 8010: exit code is 0, and the log shows no `unable to bind`.
  Check the exit code with `echo $?` right after the cook, not just the log text.
  **Passed 2026-11-10 on UE 5.9, but only after a `.uproject` fix** (details below).
- [x] If either cook exits 1 with `unable to bind`, fall back to disabling the plugin for the cook.
  **No bind error happened, so no fallback is needed.** `-DisablePlugins=ModelContextProtocol` is ruled out
  anyway: it does not keep MCP off in 5.9 (below). The working fix is the `.uproject` change, not a flag.

**Linux cook result (2026-11-10, UE 5.9 source build, scratch project from `new-mock-project.py`, not the
rehearsal project, which no longer exists).** Editor started with `scripts/launch-editor.sh` and held
127.0.0.1:8010 (`curl` 405) through every run. A level `/Game/Maps/L_MainLevel` (cube + light) was made
and saved over MCP first. Each cook ran in its own scope (16G memory, 2G swap) as:

```bash
RunUAT.sh BuildCookRun -project=<P>.uproject -noP4 -platform=Linux -clientconfig=Development -cook -skipbuild -skipstage -unattended -nullrhi
```

| Run | `.uproject` | Extra flag | Exit (`$?`) | `unable to bind` | Result |
| --- | --- | --- | --- | --- | --- |
| a | as written by `new-mock-project.py` (MCP `TargetAllowList: ["Editor"]`) | none | **1** | 0 | UAT fails before cooking (below) |
| b | cook-only copy, MCP entry without `TargetAllowList` | none | 1 | 0 | leftover temp targets from run a (below) |
| c | same copy, after deleting run a's temp targets | none | **0** | 0 | 533 packages cooked in 90 s, map in the cooked asset registry, `BUILD SUCCESSFUL` |
| d | as written (allow list kept) | `-DisablePlugins=ModelContextProtocol` | 1 | 0 | same failure as run a; UAT never reads the flag |
| e | cook-only copy | `-AdditionalCookerOptions=-DisablePlugins=ModelContextProtocol` | 0 | 0 | cook passes, but the cook log still mounts and loads MCP |

Why run a fails: in 5.9 the MCP plugin is `EnabledByDefault: true` (5.8.4's was not). Limiting it to
`"TargetAllowList": ["Editor"]` disables it for game targets, which differs from the engine default, so UBT
says *"is being treated as a code-based project for platforms Android, Linux, LinuxArm64, Wasm because:
ModelContextProtocol plugin is disabled"* (`NativeProjects.cs`, `RequiresTempTargetForCodePlugin`). UAT then
writes temp `Intermediate/Source/<P>*.Target.cs` files and, with `-skipbuild`, looks for
`Binaries/Linux/<P>Editor.target` and throws `DirectoryNotFoundException` (exit 1). Without `-skipbuild` it
would presumably try to compile a game target instead (not tested). Those temp `*.Target.cs` files stay behind and make the next cook
fail the same way even after the `.uproject` is fixed (run b): delete `Intermediate/Source/<P>*.Target.cs`.

Why `-DisablePlugins` does not help: UAT decides "code-based" from the `.uproject` alone (run d), and inside
the cook other default-on engine plugins depend on `ModelContextProtocol` (for example `AIAssistant`,
`UnrealCanvasBridge`), so it is enabled again as a dependency (run e log: `Mounting Engine plugin
ModelContextProtocol`).

The bind question itself is answered: in run c the cook loaded the MCP modules and never tried to
listen (no `LogHttpListener` line), because Auto Start is off and the cook gets no
`-ModelContextProtocolStartServer`. The editor kept :8010. The 2 cook warnings were only the deprecated 5.8.4
ini section name that `new-mock-project.py` writes on purpose.

**What to do on jam day (5.9):** in the jam `.uproject`, list `ModelContextProtocol` with
`"Enabled": true` and **no** `TargetAllowList` (or leave it out; it is on by default). Keep
`AllToolsets` and `ModelingToolsEditorMode` as Editor-only (both are off by default, so they do not trip the
check). Do not use a cook-only copy for packaging: the copy's file name becomes the project name in the
cooked output. Follow-up (not in this change): `new-mock-project.py` still writes the allow list on MCP.

Check: `ss -ltnp | grep :8010` shows the editor, and the project `.mcp.json` points at
`http://127.0.0.1:8010/mcp`. Only the lead agent calls Unreal MCP.

### Normal vs real MCP log lines

Do not treat the first two as failures (Epic forum topic 2841847, UE 5.8.3). The third is real.
Details: `_config/reference/knowledge-base.md`, "MCP log lines: normal and real".

| Log line | Meaning |
| --- | --- |
| `LogModelContextProtocol: Error: Call to unknown method "server/discover"` | Normal. Claude Code probes this on every connection; the 5.8.3 server answers MethodNotFound. |
| `Unknown session id ... client should reinitialize` | Normal after an editor restart (stale client session id). |
| `Invalid MCP server URL path` | **Real.** The client URL is wrong; it must end in `/mcp`. |

### Editor-restart recovery check (UNTESTED)

The unattended loop may restart a hung editor (`AGENTS.md`, "Editor recovery"). The loop cannot type `/mcp`.
Forum reports disagree on whether Claude Code reconnects by itself: one user (June, topic 2731505) needed a
manual `/mcp`; another (Oct, 5.8.3, topic 2841847) says it reinitializes alone. Not tested on our setup.
Test before Nov 11 (not during the window):

1. With Claude Code connected over MCP, kill the editor and relaunch it with the launch line above.
2. Wait until `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8010/mcp` prints **405**. That means
   the server is up. It comes up only after the editor has fully loaded (map and shaders), so this can take minutes.
3. Make one Unreal MCP tool call from the same Claude Code session. Record whether it works **without** `/mcp`.
4. If it fails, the recovery rule needs a wait-for-405 helper plus a reconnect step. That rule lives in
   `AGENTS.md` ("Editor recovery"), which this ticket may not edit: **owner/hub follow-up to add it there if
   step 3 fails.**

Never wait on a port or the editor without a timeout (`launch-editor.sh` exits 8 if :8010 is held by a hung process; its wait is `WAIT_TIMEOUT`, default 300 s; exit 9 = port-bind failure, retry in a few seconds).

### Plugins the rehearsal project enables

Read-only from `~/Projects/ue-mcp-verify/ue-mcp-verify.uproject` (the dress-rehearsal project, UE 5.8.4;
`EngineAssociation` is empty). The `Plugins` array holds exactly three entries, all `Enabled: true`:

- `ModelingToolsEditorMode`
- `ModelContextProtocol` (Unreal MCP)
- `AllToolsets`

**Editor Toolsets is not listed.** Epic's webinar says a missing Editor Toolsets plugin gives "connected but
can't do anything" (`_config/reference/research/get-ready-links-review-2026-11-05.md`, link 5). The rehearsal still listed
about 50 toolsets and spawned an actor, so `AllToolsets` probably pulls it in as a dependency; that is not
verified (the engine's `.uplugin` files were not read). Toolset Registry also auto-enables and is not in the
`.uproject` either. In the jam project, check Edit > Plugins for **Editor Toolsets** after enabling, and
enable it explicitly if it is off. Then record the final `Plugins` list here.

## 3. Owner-only steps

An agent must not do these (they sign in, accept terms, or start the unattended run).

| When | Step | Command / note |
| --- | --- | --- |
| Before Nov 11 | Accept the **UE EULA update 22** | In a browser, signed in to the Epic account. Also read the EULA text for open question 21 (`_config/reference/knowledge-base.md`). |
| Before Nov 12 | **butler login** check | Login was done on the Legion 2026-11-02 (`jf1shh/megajam-pretest`). Re-check: `ssh <device-host>`, then `butler status`. Log in again by hand only if it fails. Never done by an agent. |
| Window open (Nov 11, 9 PM PT) | Start the lead agent loop | `HANDOFF_MAX_RESTARTS=300 proj start megajam` |
| Window open, same time | Give the new UE project `~/Projects/megajam-game` its own Layer 0/1 | Copy `_config/reference/templates/game-project-identity.md` to `IDENTITY.md` and `game-project-context.md` to `CONTEXT.md` there, fill the blanks. Do not move `Content/`, `Source/`, `Config/`. |
| After that | Confirm it runs | `proj list`: `megajam` is `busy` and the handoff time moves. |

Notes on the loop:
- Megajam is **not** on the auto-revive list, so a reboot revives nothing until `proj start` runs.
- `HANDOFF_MAX_RESTARTS` is not saved in the loop state (dress rehearsal 3d). A loop revived after a reboot
  falls back to the default cap of 20. After any reboot, restart by hand with the 300 value:
  `proj stop megajam --yes`, then `HANDOFF_MAX_RESTARTS=300 proj start megajam`.
- Stall fallback and crash-log locations: `AGENTS.md`, "Manual fallback runbook".

## 4. Agent context budget and prompt habits

Source: Epic webinar and UEFN stream notes, `_config/reference/research/get-ready-links-review-2026-11-05.md` (links 5, 7).

**`describe_toolset` can blow the context.** Epic's trainer: materials about 2,000 to 26,000 tokens,
**Niagara close to 250,000 tokens**. A small context truncates it and the agent then loops by trial and error.
- Describe only the toolset in use, only when needed. Never describe Niagara unless the task is Niagara.
- A simple material should take about one minute. If it takes much longer, suspect truncated tool descriptions.
- Confirm the lead agent's context window holds what it asks for before a large describe.

**Prompt habits** (for the agent prompt library):
- Use exact names. One task per prompt.
- Ask intent first ("do you understand my intent?"), and read the plan before accepting it.
- Name the target Blueprint class (`BP_ThirdPersonCharacter`), not "the player's head".
- Save after batches of edits. A "save content" dialog blocks compiling and looks like a hang.
- Add `print` lines in generated code so the output log gives the agent feedback.

## 5. Build #1 checklist (Windows, Legion Go S)

- [ ] **Before every package step**, `python3 scripts/force_save_level.py --expect-actor <something you just placed>` printed `VERIFIED` (mock jam 10: MCP edits never reached the `.umap`, `save_assets` said "already saved", and the build shipped the old level). Details and the failure fallback: `stages/02_build/references/force-save-level.md`
- [ ] **The package is not PIE** (mock 10, `stages/00_prep/output/mock-jam-findings-10.md` lines 88-95): any demo/autopilot flag is **off**; the level has no template Landscape, HLOD, duplicate lights, spare placed pawn or props stacked at the origin; the HUD is a real widget or HUD draw (not PrintString). Look at one packaged frame before calling it playable (`_config/reference/canon/jam-top-lessons.md` #5)
- [ ] **Owner answers the Windows Firewall prompt once for the entry's exe** at the Legion console before the first Legion playtest (mock 16: the prompt covered every frame; agents never answer it). Make the game the front window before frame 01
- [ ] **Zip has no `*.pdb`/`*.debug`/`*.sym` and is under 1,000,000,000 bytes** (mock 16: a 2.5 GB `.pdb`, first zip 1023.8 MiB). The symbol move and strict gate came from `mock16-findings` (merged to master 2026-11-11)
- [ ] **Budget ~1 h 25 min for the first package** on the fresh 5.9 source engine (mock 16: game target compiled with `-build`); later packages are incremental
- [ ] **Game Default Map** is set, and **Cooked Maps** lists every map (a missing default gives a black screen)
- [ ] A **quit path** works in the packaged build (a pause-menu Quit; the shipped config is Development, but the same check covers a Shipping fallback, which has no console; see the recommendation below)
- [ ] Run the game **from the staging folder** on the Legion, not from the editor
- [ ] The **prerequisites installer** is in the staged output. `scripts/package-and-push.ps1` passes no `-prereqs`; look in the staged folder and add it to the clean-machine test (Rule 7(f))
- [x] **Development vs Shipping: DECIDED by the owner 2026-11-11 (~02:00 PT): "dev mode it is".** Ship **Development** for every gate build and the final build (`stages/05_devlog/output/decisions.md` D-009). Reasons and sources are in "Development vs Shipping" below. "If the owner picks Shipping" stays only as the fallback if Epic later requires Shipping.
- Epic's packaging page has no Linux-to-Windows route and no zip step: we build on the Legion and zip ourselves.

### Development vs Shipping: decided, Development (owner 2026-11-11)

**Recommendation: Development.** `scripts/package-and-push.ps1:99` already passes `-clientconfig=Development`, and
`win-plan.md` line 158 (submission checklist) already says "Packaged **Development** build". No script change is needed.
Decided: the owner confirmed Development on 2026-11-11 (~02:00 PT, "dev mode it is"; decisions.md D-009).

**Why Development**
1. **It is the wording the jam uses.** The itch.io jam page says "(development build)" (`RULES.md` line 52); a press relay
   quotes Epic as "Package a development build… Unpackaged projects are not accepted"
   (`_config/reference/knowledge-base.md` line 96); the 2023 MegaJam rules used the same words
   (`_config/reference/research/ue_fast_build_assets_shipping.md` line 41). Epic's own release-config advice (Shipping) is general
   packaging guidance, not a jam rule. Shipping would be an extra choice nobody asked for, and
   `_config/reference/research/jam_rules_judging_past_winners.md` line 165 lists "a Shipping or Debug configuration where a
   'development build' is specified" as a disqualification risk (that note's own inference, not a quoted rule).
2. **It is the only path we have proven.** Every mock jam packaged Development on the Legion (first Win64 package:
   28 s cook, 374.6 MB zip, `stages/00_prep/output/mock-jam-findings.md`). A Windows Shipping package has never been built here (only
   the Android script has a `--config Shipping` option, untested on Windows). We also moved to UE 5.9, where no Windows
   package has been built yet (`_config/reference/canon/jam-ue59-upgrade.md`). Do not add a second untested variable.
3. **The Development costs are small and already covered** (table below).

**What changes between the two**

| Area | Development (recommended) | Shipping | Matters? |
| --- | --- | --- | --- |
| Console | Available (apostrophe key, `stat unit`) | Stripped (Epic Build Configurations Reference, via `_config/reference/research/get-ready-links-review-2026-11-05.md` line 105) | Low. Judges will not use it; for us it helps diagnose a perf report. |
| Quit path | Alt+F4 works; a pause-menu Quit is still on the judge-shell list | Same, but with no console fallback | Build the Quit button either way (checklist line above). The playtest harness closes the window itself (`scripts/visual_playtest.py`, `close()`), so it does not depend on it. |
| On-screen debug text | `PrintString` and engine warnings draw on screen (mock jam 10 HUD was PrintString, "Development build only"; mock jam 15 saw "LIGHTING NEEDS TO BE REBUILT" in a Development package) | Not drawn | **This is Development's real cost.** Remove the `PrintString` calls, build lighting, and let the playtest gate's HUD check (`stages/03_playtest/references/playtest-gate.md` item 5) pass. |
| Logging | Writes `Saved/Logs` in the packaged build, useful when a judge reports a crash | Most `UE_LOG` output is normally compiled out | Favours Development. This Shipping detail is engine knowledge, **not checked in this repo**. |
| Size | Larger, but the only measured package is 374.6 MB against the 1 GB cap; push with `--ignore '*.pdb'` if needed (`_config/reference/research/ue_fast_build_assets_shipping.md` line 365) | Smaller | Low. No Development-vs-Shipping size was measured here. |
| Speed at runtime | Slightly slower (engine knowledge, **not measured here**) | Faster | Low unless the Legion run misses 60 fps by a small margin. |
| Unreal MCP plugin | Not in the build: `ModelContextProtocol` and `AllToolsets` have `"TargetAllowList": ["Editor"]` (`stages/00_prep/output/mock-jam-findings-5.md`, `stages/00_prep/references/pre-jam-declaration-2026-10-29.md` line 99) | Same | **No difference.** The plugin is editor-only in both. |
| "For Distribution" (Project Settings > Packaging) | Keep **Off**: it forces Shipping (`_config/reference/knowledge-base.md` line 200) | n/a | Keep it off, or the build silently becomes Shipping. |

**What is not known (say so, do not guess)**
- The Nov 5 Official Rules digest (`RULES.md`) records no numbered rule about build configuration; the requirement comes from the
  jam page and relays. Epic never answered the forum question on it (`_config/reference/knowledge-base.md` line 625).
- The Legion's UE 5.9 is a **source build** at `C:\Dev\UE_5.9` (checked read-only 2026-11-10 21:05 PT; editor built,
  helper tools rebuilt by hand). On a source build a Shipping package also compiles the game's Shipping binaries, which is
  slow and untested. That is one more reason not to switch late. *Superseded:* "installed or source build is not recorded".

**Cheap re-checks (already in the schedule)**
- Re-read the jam page when it opens on Nov 11 and the Official Rules on Nov 15 morning (section 6). Look for "development", "shipping", "release build".
- If the Epic forum thread or the livestreams (11 AM PT daily) give a build-configuration answer, it wins over this note.

**If the owner picks Shipping** (or Epic says so)
1. Change `scripts/package-and-push.ps1:99` to `-clientconfig=Shipping -serverconfig=Shipping` (a one-line edit; the script has no config parameter).
2. Do one full package and clean-machine run **by Thu Nov 12 night**, never first on Sunday.
3. Confirm the Quit button works, the game starts from the staged `<Game>.exe`, and the playtest gate passes. The Legion tools already
   know the `<Game>-Win64-Shipping.exe` process name (`scripts/legion_ship.py` line 497; `_config/reference/canon/jam-legion-ship-preflight.md`).
4. Update `win-plan.md` line 158 and `RULES.md` line 52 so they stop saying Development.

## 6. Start-of-session checklist

- [ ] `lemonade unload`, then `gpu-preflight` is `CLEAR`
- [ ] `python3 scripts/gen_asset.py --providers-check` shows which concept-image providers are ready (local / gpt / grok); see `_config/reference/ai-providers.md`
- [ ] Editor launched with `-ModelContextProtocolStartServer -ModelContextProtocolPort=8010` (Auto Start stays off); `ss -ltnp | grep :8010` shows it
- [ ] Before each gate build and every package step: `scripts/force_save_level.py` prints `VERIFIED` (`stages/02_build/references/force-save-level.md`)
- [ ] Before each gate build: packaging gate cook exit code is 0 (see the cook to-test lines in step 2; untested until run)
- [ ] If the project will not open after an engine update: delete `Saved`, `Intermediate`, `DerivedDataCache` first (topic 2849229)
- [ ] `proj list` shows `megajam` busy (window only)
- [ ] Rules re-check against the Box PDF on Nov 10 and Nov 15 morning

## 7. Crash and recovery: MCP logging

When MCP misbehaves, turn on verbose logging in the editor console: `Log LogModelContextProtocol Verbose`.
Read the `LogModelContextProtocol` category in the Output Log. Last resort: the MCP Inspector
(`npx @modelcontextprotocol/inspector`, Streamable HTTP). Copy `Saved/Logs/` out first, per `AGENTS.md`
("Editor recovery").

## 8. Sourced assets (Rules 1(d), 15(c))

Plan and pack shortlist: `stages/02_build/references/sourced-assets-plan.md`. Sourced assets are never scored, so use them for filler only.

- [ ] Before Nov 12 (owner): claim Fab freebies into the Epic library and download Kenney / Poly Haven packs to `~/sourced-packs/`, outside the repo. **Do not import into the project before the window opens** (Rule 7(h), safe reading).
- [ ] Before each import: copy the exact licence line from the pack page. No licence line, no import.
- [ ] Log it first: `python3 scripts/sourced_assets.py add --name "..." --url ... --licence "..." --author "..." --files "/Game/Sourced/<Pack>"`
- [ ] Then import into `/Game/Sourced/<Pack>/` only. Check for logos, brand names and non-English text.
- [ ] Never use a sourced pack as a reference image for an AI generator (Fab "NoAI" tag, knowledge-base question 21).
- [ ] Submit step: `python3 scripts/sourced_assets.py credits`, paste into the itch.io page and the entry form.

## 9. Every night (dev log)

The dev log feeds the itch.io devlog for the Glass Box modifier (`_config/reference/canon/jam-rules-cheatsheet.md`) and is
part of the pre-jam declaration trail (Rule 7(h)). One entry per night, about 15 minutes. Format:
`_config/reference/templates/dev-log-entry.md`. First entry (prep catch-up): `stages/05_devlog/output/2026-11-10.md`.

- [ ] Draft: `python3 scripts/gen_devlog.py --dry-run` (resumes from the last entry's Build/version commit). Drop `--dry-run` to write `stages/05_devlog/output/YYYY-MM-DD.md` (it refuses to overwrite an existing entry; `--force` replaces it, `--date` picks another day). Add `--notes-file` for "What's next" and "One thing that surprised us".
- [ ] Edit the draft by hand: plain language, 4 to 8 bullets grouped by theme, not a commit list. Fill the AI disclosure from what the repo records. Keep the commit hash in backticks under "Build/version" (the next night resumes from it).
- [ ] Commit it as `stages/05_devlog/output/YYYY-MM-DD.md` through a PR (merge follows the jam-week autonomy rule in `AGENTS.md`).
- [ ] **Owner**: read the entry, then post it to the itch.io devlog. An agent never posts it without the owner's OK.
- [ ] Before posting, `grep -n OWNER-FILL stages/05_devlog/output/YYYY-MM-DD.md` prints nothing. Post shape: `stages/05_devlog/references/itch-devlog-template.md` (A).

### How to log as you go (all day, about 1 minute each)

The nightly draft is only as good as what was logged during the day. Glass Box is scored on the dev log, so:

- **A decision is made** (scope cut, mechanic picked, tool swapped, risk fork taken, owner answers a question):
  add one row to `stages/05_devlog/output/decisions.md` right away (`| D-NNN | YYYY-MM-DD HH:MM | who | what | why | link |`,
  next free ID, Pacific time). Tonight's draft copies every row no entry mentions yet.
- **A build is pushed to itch:** add a row to `stages/05_devlog/output/builds.csv` (time, gate tag, commit, itch target, the
  build number from `butler status`, a note). The evidence index lists it.
- **A screenshot, clip, playtest frame or scorecard is made:** keep it under `stages/NN_*/output/` (committed evidence) or
  `work/` (local), with a name that says what it shows. Before the nightly draft run
  `python3 scripts/evidence_index.py --out stages/05_devlog/output/evidence.md` and commit the result with the entry.
  Evidence on another machine (OBS clips on the Legion) is listed with `--dir <path>`.
- **Something surprising happens:** one line in the night's notes file (passed with `--notes-file`) while it is fresh.
- **Any tool is used in the entry for the first time** (AI or not): append a row to the tools-used ledger, section 0 of `stages/05_devlog/references/ai-disclosure-draft.md` (tool, what for, first used, evidence). The form's "Tools you used" field and partner prizes (Hyper3D, NVIDIA RTX) are filled from it.
- Final day: the "How it was built" post follows the outline in `stages/05_devlog/references/itch-devlog-template.md` (B).

# Jam execution plan: hour by hour, plus overnight run cards

Draft 2026-11-10, reviewed and ruled by Fable the same day (section 7). All times **Pacific (PT)**.
It turns the day gates in `PLAN.md` (Phase 1) and `stages/00_prep/references/win-plan.md` into an hour-by-hour schedule.
Where this file and `AGENTS.md`, `PLAN.md` or `RULES.md` disagree, those win; the conflicts found are listed in
section 7. **UNVERIFIED** marks anything not confirmed in the repo. **ASSUMPTION** marks a guess the owner can change.

## 0. Fixed points

| What | When (PT) | Source |
| --- | --- | --- |
| Kickoff stream + theme reveal | Wed Nov 11 11:00 | `AGENTS.md`, `RULES.md` (itch page) |
| Concept picked (thinking on paper only) | Wed 15:00 | `PLAN.md`, `win-plan.md` |
| Contest window opens (Rule 4) | Wed 21:00 | `RULES.md` |
| Build #1 launches on Windows | Thu, by end of day | `PLAN.md` |
| Full run in build #2, played by the owner (answer 2026-11-11) | Fri, by end of day | `PLAN.md` |
| Risk-fork check, feature freeze 22:00, build #3, insurance upload | Sat | `PLAN.md` |
| Fixes only to 12:00, final build 13:00, video 14:00, dev log 15:00, uploaded 16:00, submitted 16:30 | Sun | `PLAN.md` |
| `jam_clock.py` PACKAGE (T-60) / FINAL (T-15) / EXPIRED | Sun 16:59 / 17:44 / 17:59 | `stages/04_ship/references/jam-clock.md` |
| Daily Epic livestream (rule clarifications only, 15 min) | 11:00 Thu-Sun | `RULES.md` |

**Owner sleep: 01:00-08:30 every night (owner confirmed 2026-11-10)** (`win-plan.md` also says "sleep at least
6 hours"). Meals: breakfast 08:30, lunch 12:00, dinner 18:00 (ASSUMPTION). One buffer hour per day, marked **BUFFER**.

Column key: **GPU** = who holds the desktop RX 9070 XT (`Lemonade`, `Editor`, `GEN` = local Nexus jobs, `free`).
Cloud jobs (GPT/Grok images; cloud 3D once enabled) do not hold the GPU. **Legion** = what the Legion Go S is doing.

Standing rules in every row (not repeated): `gpu-preflight` before any GPU job or editor launch; one GPU workload at
a time; the editor and every GPU job in their own `systemd-run --user --scope` with the `AGENTS.md` profile
(**MemoryHigh=26G MemoryMax=28G MemorySwapMax=8G**, the `launch-editor.sh` default; the hub's 16G/2G cap is for side
jobs outside this repo, ruling C2); at most **4 live agent workers** (lead + 3); the lead is the only Unreal MCP
caller; `jam_clock.py check` every loop turn during the window; `force_save_level.py --expect-actor <X>` prints
`VERIFIED` before every package.

**Merge rule inside the window (`AGENTS.md` jam-week autonomy, ruling C1):** commits and merges to `jam-integration`
need no ask. `master` is fast-forwarded only at the four gate builds (Thu, Fri, Sat, Sun) and the agent **flags the
owner right before**, it does not wait for a GO. Itch pushes to the private pretest page (`legion_ship.py` default
target) need no ask; a push to the **real** entry page is flagged and done only while the owner is awake. Before
21:00 Wed the global rule holds: PR + review GO for anything on `master`.

## 1. Timeline

### Wed Nov 11 (pre-jam until 21:00: no gameplay, levels or art, Rule 7(h))

| Time | Owner does | Agents do | GPU / Legion | Gate at end of hour |
| --- | --- | --- | --- | --- |
| 08:00 | Asleep (ASSUMPTION) | Hub: perk email heartbeat (`perk-watch.md`). Read-only check of the Legion 5.9 source build. | Lemonade / 5.9 compile | - |
| 08:30 | Breakfast. **Perk reminder 08:30:** Cursor `agent login` ($50 ends Nov 17 17:32); sign up weloveindies.com/en/epicmegajam; Diversion MEGAJAM26 choice (by Nov 22); Reallusion iClone OK + where | Hub posts the reminder | Lemonade / compile | Owner answered the four asks |
| 09:00 | **Reminder 09:00:** say yes/no to a 55-credit Tripo test (web UI only; Tripo web credits do not cover the API). **Decide cloud 3D keys:** the fal / Hyper3D Rodin / Tripo adapters are on `master` (PR #158) but run only after you create `FAL_KEY`, `RODIN_API_KEY`, `TRIPO_API_KEY` plus the matching `*_TERMS_REVIEWED` lines in `~/.config/megajam.env` (fal's $30 covers the API; Hyper3D unknown; Tripo API needs a paid key). Accept **UE EULA update 22**. `ssh <device-host>` then `butler status`; also confirm `butler` works on the PC (default push side, UNVERIFIED) | Hub: one small PBRgen material test (throwaway, never imported). Agents: `python3 scripts/gen_asset.py --providers-check` (shows which cloud adapters are live) | Lemonade / compile | EULA accepted; butler OK on the push side; keys decided |
| 10:00 | Confirm the Legion **5.9 source build** (scheduled task `UE59Build`, `C:\Dev\UE_5.9`) finished. **Disable the Legion idle lock** for the whole window (mock 14). Pause the `obsidian-inbox-sorter` timer (it reloads Lemonade, mock 15). **Stop the mock loop:** `proj stop megajam-mock --yes` (it is running now and marked auto-start; stopping unmarks it, else revive restarts it after any reboot) | `python3 scripts/legion_ship.py <scratch> --engine C:\Dev\UE_5.9 --dry-run` against a throwaway template in `~/Projects/megajam-mock` (the script probes only 5.8 paths, so `--engine` is required) | Lemonade / idle | Preflight clean with the 5.9 path; `proj list` shows no running loop |
| 10:45 | **Reminder 10:45:** kickoff at 11:00 | - | Lemonade | - |
| 11:00 | **Watch kickoff.** Write the exact theme text and any rule news | Hub records theme text in a note (text only) | Lemonade | Theme written down |
| 12:00 | Lunch while spreading the theme (zoom-in, section 5) | Theme spread with `_config/reference/templates/theme-spread-prompt.md`; map the 5 shortlist concepts to the theme | Lemonade / **Legion: first 5.9 Win64 package of the throwaway template** (`legion_ship.py --engine C:\Dev\UE_5.9`, default pretest target, no ask) | 10 readings |
| 13:00 | Filter to 3 and score | Score with `_config/reference/templates/scoring-rubric.md` | Legion: launch the throwaway build | **Engine fork:** 5.9 Win64 package launches? If not, jam project starts on 5.8.4 (decide by 15:00) |
| 14:00 | Pick the leader + runner-up; name the risk fork and its safe fallback (`win-plan.md` D6) | Draft one-pager (`templates/gdd-one-pager.md`), asset list with counts, day-1 cut list | Lemonade / idle | Draft one-pager exists (not committed) |
| 15:00 | **Concept locked.** Development config decided (owner 2026-11-11, "dev mode it is"; decisions.md D-009) | Write slice briefs (`templates/feature-slice-brief.md`) and the overnight N1 GPU queue prompts (text only) | Lemonade | Concept, engine version, build config decided |
| 16:00 | **BUFFER** | Last tooling fixes only, each by PR with a review GO; tooling freeze for `master` at 19:00 (mock 12: tools changed under a running mock) | Lemonade | Open tooling PRs merged or parked |
| 17:00 | itch.io: create the private game page, team and game name (sets `TeamName_GameName`) | Note the target `<user>/<game>:win64` for `--target` | Lemonade | Page exists (owner only) |
| 18:00 | Dinner | Hub: prepare `pre-jam-tooling` tag (push needs GO) | Lemonade | - |
| 19:00 | Rest | Tag `pre-jam-tooling` after the last pre-jam doc edit (needs GO) | Lemonade | Tag on `master` |
| 20:00 | **Reminder 20:30:** sign in at platform.claude.com (Anthropic $25, claim after 00:00). Read the N1 card | 20:45 `lemonade unload`, `gpu-preflight` = CLEAR; `proj list` shows no running loop | free | GPU CLEAR |
| 21:00 | **Window opens.** Run `HANDOFF_MAX_RESTARTS=300 proj start megajam`; then `proj list` shows busy. Watch for the Rokoko voucher (redeem by hand only) | Lead: `python3 scripts/jam_clock.py start`; create the project (5.9 `.uproject`: MCP entry with no `TargetAllowList`, runbook step 2); `scripts/launch-editor.sh` (default 26G/28G/8G scope); commit one-pager at 21:00 | Editor / idle | `:8010` answers 405; one-pager committed |
| 22:00 | Watch first greybox | Greybox map, pawn, camera | Editor | You can move |
| 23:00 | Try the core verb | Core verb in greybox, test bot for win/lose | Editor | Core verb works |
| 00:00 | Dev log entry (15 min) with `gen_devlog.py --dry-run` draft. Approve the N1 card | Draft dev log; `force_save_level.py` VERIFIED; commit to `jam-integration` | Editor | **Wed gate (PLAN):** move + core verb in greybox |
| 01:00 | Sleep | **N1 starts** (section 2) | per N1 | - |

### Thu Nov 12 (day 1): core loop fun with juice, ending stubbed, art direction locked, build #1 launches

| Time | Owner does | Agents do | GPU / Legion | Gate at end of hour |
| --- | --- | --- | --- | --- |
| 01:00-08:30 | Asleep | **Overnight N1** | per N1 | N1 morning report written |
| 08:30 | Breakfast; read the N1 report; **reminder (was 08:00):** claim Anthropic $25 | Hub: answers report questions; re-plans the day if N1 failed | Editor | Day plan confirmed or cut |
| 09:00 | 2-min hand playtest of the greybox loop | Juice on the core verb: hit-stop, camera shake, sound stub, particles | Editor | Juice on the verb |
| 10:00 | Approve the written cut list | Finale stub: build the ending first | Editor | Ending reachable |
| 11:00 | Livestream skim (rules only, 15 min) | Loop slice 2 | Editor | `greybox_gate.py check` passes |
| 12:00 | Lunch | Save, VERIFIED, close editor; GPU: art-direction hero assets (3) | **GEN** (45 min box) | 3 hero assets on disk |
| 13:00 | **Pick art direction** from the 3 hero assets | Relaunch editor; import (`ue_import_asset.py`); palette, one master material, post-process | Editor | Art direction locked |
| 14:00 | Hand playtest | Build #1 checklist (runbook step 5): default map, cooked maps, Quit path, no PrintString HUD | Editor | Checklist ticked |
| 15:00 | Read the fast-forward flag (no GO needed in the window) | `force_save_level.py` VERIFIED; `ue_verify_level.py` → `presubmit_gate.py`; flag the owner, fast-forward `master` | Editor | presubmit PASS |
| 16:00 | If build #1 should also be the day-1 test upload to the real draft page (`win-plan.md`), say so now; else it goes to pretest | **Build #1:** `legion_ship.py <project> --engine C:\Dev\UE_5.9` (pretest by default; `--target <user>/<game>:win64` only on the owner's word; ~10 min, mock 12) | Editor / **Legion package** | Ship log ends OK |
| 17:00 | Look at the agent's frames | `agent_playtest_cli.py` start/look/press/gate, then `visual_playtest.py run` | Legion playtest | **Thu gate: build #1 launches** |
| 18:00 | Dinner | GPU: first music loop (`gen_music.py`) + prop batch | **GEN** (45 min) | Music loop on disk |
| 19:00 | Hand playtest of build #1 on the Legion | Fix list from the playtests | Editor / Legion idle | Fix list written |
| 20:00 | - | Fixes; loop slice 3 | Editor | - |
| 21:00 | **BUFFER** | Catch-up | Editor | - |
| 22:00 | Review cut list against progress | Slice 3 done or cut | Editor | Thu gate state written |
| 23:00 | Dev log: edit the draft, post to itch devlog | `gen_devlog.py` draft; commit | Editor | Entry posted (owner) |
| 00:00 | Approve the N2 card | Save, VERIFIED, commit | Editor | Clean tree on `jam-integration` |

### Fri Nov 13 (day 2): beats 1-3, win/lose, assets swapped in, chapter select, full run in build #2

| Time | Owner does | Agents do | GPU / Legion | Gate at end of hour |
| --- | --- | --- | --- | --- |
| 01:00-08:30 | Asleep | **Overnight N2** | per N2 | N2 report written |
| 08:30 | Breakfast; read N2 report | Hub re-plans | Editor | - |
| 09:00 | Hand playtest | Beat 1 with placeholders | Editor | Beat 1 playable |
| 10:00 | - | Beat 2; obstacles | Editor | Beat 2 playable |
| 11:00 | Livestream skim | Beat 3; win and lose states | Editor | Win + lose reachable |
| 12:00 | Lunch | Close editor; GPU asset swap batch | **GEN** (45 min) | Batch on disk |
| 13:00 | Pick swaps | Import swaps; chapter/level select wired to what exists | Editor | Chapter select works |
| 14:00 | Hand playtest, start to end | Fixes | Editor | Full run in PIE |
| 15:00 | Read the fast-forward flag | VERIFIED, presubmit, flag, fast-forward `master` | Editor | presubmit PASS |
| 16:00 | - | **Build #2** via `legion_ship.py` (pretest) | Legion package | Ship OK |
| 17:00 | - | Agent playtest gate, then `judge_pass.py packet` / `parse` (needs the agent playtest journal, mock 12) | Legion playtest | Agent GATE PASS; judge score recorded |
| 18:00 | Dinner | GPU: music for menu/play/climax/end | **GEN** (45 min) | Tracks on disk |
| 19:00 | **The owner plays build #2** (owner answer 2026-11-11, G7) | Hub takes notes into the fix list | Legion: human play | **Fri gate: full run, owner plays** |
| 20:00 | - | Fixes from the play session | Editor | - |
| 21:00 | **BUFFER** | Catch-up | Editor | - |
| 22:00 | Early read on the risk fork (is the core landing?) | Write the risk-fork evidence: playtest notes, judge Fun Factor | Editor | Evidence written |
| 23:00 | Dev log | Draft + commit | Editor | Entry posted |
| 00:00 | Approve N3 card | Save, VERIFIED, commit | Editor | Clean tree |

### Sat Nov 14 (day 3): art, lighting, audio, UI, juice; freeze 22:00; build #3; insurance upload

| Time | Owner does | Agents do | GPU / Legion | Gate at end of hour |
| --- | --- | --- | --- | --- |
| 01:00-08:30 | Asleep | **Overnight N3** | per N3 | N3 report written |
| 08:30 | Breakfast; read N3 report | Hub re-plans | Editor | - |
| 09:00 | **Reminder 09:00:** Tripo Pro ends Nov 17, Hyper3D Nov 20, Cursor Nov 17 | Lighting pass | Editor | - |
| 10:00 | **Risk-fork check** (section 4): keep the core or bail to the safe fallback | If bail: switch per the concept's fallback now | Editor | Decision written |
| 11:00 | Livestream skim | Audio pass: MetaSound import with loop points, SFX on every action | Editor | Every action has a sound |
| 12:00 | Lunch | Close editor; last GPU batch (fix assets, upscales `realesrgan-x4plus`) | **GEN** (45 min) | Last batch on disk |
| 13:00 | - | UI: title, pause, settings, end screen | Editor | Screens reachable |
| 14:00 | Hand playtest | Juice pass; theme visible on title and in the first minute | Editor | Theme check |
| 15:00 | - | Fixes; perf on Legion (60 fps at 1080p target) | Editor | - |
| 16:00 | **BUFFER** | Catch-up | Editor | - |
| 17:00 | - | Last features from the cut list only | Editor | - |
| 18:00 | Dinner | Rough video capture plan; OBS Game Capture source on the Legion (`capture-setup.md`) | Editor | - |
| 19:00 | Look at a rough cut | Capture rough clips (`agent_playtest_cli.py clip`) on the last good build | Legion: OBS | Rough cut exists |
| 20:00 | Hand playtest | Last features | Editor | - |
| 21:00 | - | Wrap features; nothing new starts after 21:30 | Editor | - |
| 22:00 | **FEATURE FREEZE.** Read the fast-forward flag | VERIFIED, presubmit, flag, fast-forward; **build #3** (pretest) | Legion package | Ship OK |
| 23:00 | Look at agent frames | Agent playtest gate + `visual_playtest.py` gate + judge pass | Legion playtest | Build #3 GATE PASS |
| 23:30 | **Insurance upload:** stay up for it. Agent flags, then pushes to the real page (or push it yourself); decide whether to submit the entry form now (itch lets files be replaced, `PLAN.md` Phase 0) | Flag the owner; `legion_ship.py --from-step 4 --target <user>/<game>:win64` (same staged build #3) | Legion / PC butler | Insurance build processed on itch |
| 00:00 | Dev log; approve N4 card | Draft + commit | Editor | Entry posted |

### Sun Nov 15 (day 4): fixes to 12:00, final build 13:00, video, dev log, upload, submit

| Time | Owner does | Agents do | GPU / Legion | Gate at end of hour |
| --- | --- | --- | --- | --- |
| 01:00-08:30 | Asleep | **Overnight N4** (fixes only) | per N4 | N4 report written |
| 08:30 | Breakfast; read N4 report | Hub: rank fixes | Editor | Fix list ranked |
| 09:00 | **Reminder 09:00:** re-check the Official Rules PDF; collect the "Tools you used" list | Fixes only | Editor | Rules re-checked (owner) |
| 10:00 | Hand playtest | Fixes only | Editor | - |
| 11:00 | Livestream skim | Fixes only | Editor | - |
| 12:00 | **Fix freeze.** Lunch | Last VERIFIED, presubmit, flag, fast-forward `master` | Editor | Clean `master` |
| 13:00 | Be at the desk: the real-page push is flagged to you | **Final build** via `legion_ship.py` to pretest; agent + visual playtest gate; on PASS flag, then `--from-step 4 --target <real page>` | Legion package / playtest | Final GATE PASS (else keep insurance) |
| 14:00 | Watch final video | Video: 30-60 s, 1080p, gameplay in first 5 s, ends on title card; ffmpeg two-pass `loudnorm` (-23 LUFS) | Legion OBS / free | Video file ready |
| 15:00 | Upload video unlisted (sign-in: owner). Edit + post the final dev log and "how it was built" summary | `gen_devlog.py` draft; `sourced_assets.py credits`; AI-use disclosure text | free | Dev log posted |
| 16:00 | Fill the itch page and entry form | Paste-ready text in a file for the owner | free | **Uploaded by 16:00** |
| 16:30 | **Click Submit** (Rule 17); screenshot the confirmation | Stop feature work; `jam_clock.py status` | free | **Submitted by 16:30** |
| 16:30-17:44 | **BUFFER** (only page/text fixes) | Clock: PACKAGE 16:59, FINAL 17:44 | free | - |
| 17:59 | Window closes | Clock EXPIRED: stop | free | - |
| 18:05 | **Reminder 18:05:** NetApp+AWS email (owner's yes to send) | - | - | - |
| 18:30 | Done | Closeout: stop processes, restore Lemonade `--ctx-size 32768`, final status docs | Lemonade | Closeout receipt |

## 2. Overnight run cards

Same frame for every night. **The loop keeps running all window**; a card only bounds what the lead may do while the
owner sleeps (01:00-08:30, owner confirmed).

**Common to all four nights**

| Item | Rule |
| --- | --- |
| Inputs | The newest `.handoff/*/HANDOFF.md`, `PLAN.md`, this card, the day's fix/cut list. |
| Allowed | Commits and merges to `jam-integration`; editor work via MCP (lead only); file-only C++/Python by up to 3 helpers; GPU queue below; Legion checks and playtests; **one `legion_ship.py` run per night to the default pretest target** (after VERIFIED; never while a GEN job runs, the sync reads the project). |
| Forbidden | Fast-forward to `master` (gate builds are daytime, owner awake); any push to the **real** itch page (`--target` other than the default); a second package in one night; any delete of files outside the jam project's own scratch, or any `claude rm --discard-unpushed`; sign-ins, keys, terms, redeeming codes; working around a guard; more than 4 live workers; a second GPU job; touching the engine trees. |
| Legion packaging | **Allowed to pretest.** `legion_ship.py` always pushes (step 4), but its default target is the private test page `jf1shh/megajam-pretest:win64`, which exists for this. Each night: `python3 scripts/legion_preflight.py`, then at 07:30 (after VERIFIED) `legion_ship.py <project> --engine C:\Dev\UE_5.9` with no `--target`. Dry-run only if VERIFIED or the clock says no (ruling C6; no tooling ticket). |
| Waits | Every wait has a timeout (`launch-editor.sh` exits 8/9; never wait on :8010 without one). Before relaunching the editor, `ss -ltn \| grep 8010` must be empty. Never end a turn while a background job runs unwatched: use `waitfor` or Monitor (mock 12). |
| Checkpoints | Commit at least every 30 min or each finished slice; `editor_watchdog.py` save + snapshot on its timer; one line per 30 min in the night log; HANDOFF.md written by the loop at context limit. |
| GPU switch | Save, `force_save_level.py` VERIFIED, close editor, `lemonade unload`, `gpu-preflight` CLEAR, then the job in its own scope (16G / 2G swap). Re-check `gpu-preflight` before **each** job (Lemonade reloads, mock 15). **HUB: this row says 16G / 2G for GEN jobs, but the standing-rules paragraph (about line 30) and ruling C2 say 26G/28G/8G; mock 14 and 16 use 16G through `LAUNCH_SCOPE_CMD`. Contradiction not resolved here.** |
| Clock | `python3 scripts/jam_clock.py check` every loop turn. Exit 0 only means keep going; 10/11/12 means stop feature work per `jam-clock.md`. |
| Restarts | Budget 300 for the window (`HANDOFF_MAX_RESTARTS=300`); expected about 1/hour. If one night uses more than 20, write a blocker line and drop to file-only work (ASSUMPTION threshold). Exhaustion fires an ntfy alert. |
| Blockers | Never wait on the owner: log the ask in the report and move to the next item (mock briefs). Two failed editor relaunches in a row: stop editor work, copy `Saved/Logs` + `Saved/Crashes` to `stages/04_ship/output/crash-logs/<stamp>/`, continue file-only work. |
| No early "done" | Mock 12 declared done twice with hours left. If the card's goal is met, work the idle list: fix list, step shots, dev log draft, credits list. |
| Hard stop | 07:30 last job start (the package); 08:00 nothing new starts; 08:15 morning report committed. |
| Morning report | Lands at `stages/05_devlog/output/jam-nights/<date>-morning.md` on `jam-integration` (new folder, ASSUMPTION) plus one line to the hub. Says: card goal PASS/FAIL per success item; commits (hashes); GPU jobs run (name, minutes, result, provider); editor/GPU state now; restarts used; frames to look at (paths); blockers; numbered owner asks (one line each); what was not done; risk to today's gate; first 3 actions for 08:30. |

### N1: Wed 01:00 -> Thu 08:30

| Item | Spec |
| --- | --- |
| Goal | Greybox loop won, lost and restarted (`greybox_gate.py record --project "$UPROJECT" --won --lost --restarted`); art-direction candidates ready for 13:00 Thu. |
| Queue | 01:00-03:30 **Editor**: finish the greybox loop, test bot, step shots, gate record. 03:30-03:45 switch. 03:45-06:15 **GEN**, only if `greybox_gate.py check` passes: 3 art directions x 4 concept images (`gen_asset.py`, Krea; GPT/Grok in parallel since they are cloud), then 6 props via `asset_chain.py --queue <file>` (about 3 min each, box 45 min), then 1 music loop (`gen_music.py`, box 20 min). 06:15-06:30 switch. 06:30-07:30 **Editor**: import props into a staging folder (not placed), save, VERIFIED. 07:30 first jam package to pretest (proves the 5.9 pipeline on jam content before build #1). |
| Success | Gate recorded; at least 3 directions and 6 props on disk with sidecars; 1 loop; a pretest package that launches (`agent_playtest_cli.py start`). |
| Failure | No gate by 03:30: skip GEN, keep on the loop; report says "greybox not proven" and the 09:00 slot becomes greybox. |

### N2: Thu 01:00 -> Fri 08:30

| Item | Spec |
| --- | --- |
| Goal | Build #1 fixes done; beat 1 laid out in placeholders; asset batch 2 for beats 1-3. |
| Queue | 01:00-04:00 **Editor**: fixes from Thu playtests, beat 1 layout. 04:00-06:30 **GEN**: 15 props from the asset list (box 60 min), then 2 music tracks (box 40 min). 06:30-07:30 **Editor**: import, save, VERIFIED. 07:30 package build #1 + fixes to pretest; `agent_playtest_cli.py` gate on it. |
| Success | Fix list items closed or marked; beat 1 playable in PIE; at least 12 of 15 props usable. |
| Failure | Build #1 still not launching at 08:30: report leads with it; Fri morning starts with packaging, not beats. |

### N3: Fri 01:00 -> Sat 08:30

| Item | Spec |
| --- | --- |
| Goal | Build #2 fix list closed; UI screen skeletons (title, pause, end); final hero asset swaps; music for every state. |
| Queue | 01:00-04:00 **Editor**: fixes, UI skeletons. 04:00-06:30 **GEN**: hero swaps and upscales (box 60 min), music gaps (box 40 min). 06:30-07:30 **Editor**: import, save, VERIFIED. 07:30 package to pretest (evidence for the 10:00 risk fork). |
| Success | Every state has music; UI screens reachable in PIE; risk-fork evidence file updated for 10:00. |
| Failure | Full run broken in PIE at 08:30: report says so first; Sat 10:00 risk fork leans to the fallback. |

### N4: Sat 01:00 -> Sun 08:30 (after feature freeze)

| Item | Spec |
| --- | --- |
| Goal | Bug fixes only on build #3's list; raw video clips; dev log and credits drafts. |
| Allowed extra | Agent playtest and `agent_playtest_cli.py clip` on the staged build #3 (no push). Re-generating one broken asset counts as a fix, logged as such. |
| Forbidden extra | Any new feature, mechanic, level or screen (freeze). |
| Queue | 01:00-06:00 **Editor**: fixes, each VERIFIED and committed. 06:00-07:30 Legion clips (OBS). No planned GEN. 07:30 package the fixed build to pretest, agent gate on it (Sun 08:30 then starts with a tested candidate). |
| Success | Fix list shorter; 3+ clean clips for the video; "how it was built" draft; `sourced_assets.py credits` output saved. |
| Failure | A fix broke the full run: revert it on `jam-integration` and say which commit. |

## 3. Things to settle before 21:00 Wed (UNVERIFIED or gaps)

| # | Item | Owner of fix |
| --- | --- | --- |
| G1 | Closed: overnight packages push to the private pretest page (the script's default). No tooling ticket | - |
| G2 | Legion UE 5.9 is a **source build** at `C:\Dev\UE_5.9` (task `UE59Build`); `legion_ship.py` probes only 5.8 paths, so always pass `--engine C:\Dev\UE_5.9`. *Update 2026-11-10 21:05 PT (read-only):* editor stage finished (exit 0 at 21:00); the helper-tools stage failed on cmd quoting (`ue59_build.ps1` line 25) and ShaderCompileWorker, UnrealPak and CrashReportClient were rebuilt by hand, done not yet confirmed | Owner confirms the helper tools finished (Wed 10:00) |
| G3 | *Closed by mock 16 (2026-11-10):* a 5.9 Win64 package built on the Legion and reached pretest (itch build #2354706, 370.2 MiB zip) after restoring 9 AutomationTool files (GitDependencies excludes). *Superseded:* "No 5.9 Windows package has ever been built (runbook, mock 15)" | Wed 12:00 throwaway package |
| G4 | `new-mock-project.py` still writes `TargetAllowList` on MCP; 5.9 cook fails with it (runbook step 2) | Fix by hand in the jam `.uproject`, or ticket |
| G5 | *Owner answer 2026-11-11 (hub 86):* use **all three** cloud 3D providers (fal, Hyper3D Rodin, Tripo) for the most important assets, where they impact the game most (hero/player/key props); local TripoSplat for the rest. Adapters merged (PR #158); each stays off until its key + `*_TERMS_REVIEWED` are in `~/.config/megajam.env` (owner steps: `_config/reference/ai-providers.md` "Owner steps"; Tripo API needs its own paid credits). Check with `python3 scripts/gen_asset.py --providers-check` | Owner: create keys before 21:00 Wed |
| G6 | PC-side `butler` login for the default PC push | Owner check Wed 09:00 |
| G7 | *Closed 2026-11-11 (hub 86):* the **owner** plays build #2 Fri 19:00 (owner: "I play it"). *Superseded:* "who plays build #2 (name, in person or remote)" | Owner |
| G8 | *Closed 2026-11-11 (hub 86):* jam project path is `~/Projects/megajam-game` (Diversion repo `megajam-game`; see `stages/04_ship/references/diversion.md`). *Superseded:* "jam path not written down" | 21:00: create there, write path to `~/.config/megajam/jam-path` |
| G9 | `megajam-mock` loop is running now and marked auto-start; it would fight the jam loop for the editor and come back after a reboot | Owner or hub: `proj stop megajam-mock --yes` before 21:00 Wed |

## 4. Decision gates, bail rules, cut lists

When something breaks (crash, outage, lost work, missed gate), use `stages/04_ship/references/jam-recovery.md`: break-glass steps, backups, a card per failure.

**Gates (a missed gate means cut next morning, never move the gate; `win-plan.md`)**

| When | Check | If it fails |
| --- | --- | --- |
| Wed 15:00 | Engine fork: throwaway 5.9 Win64 package launched on the Legion | Start the jam project on 5.8.4 (`UE_VERSION=5.8`); never convert later |
| Thu 01:00 | Move + core verb in greybox | N1 stays on greybox; no GEN |
| Thu 12:00 | `greybox_gate.py check` passes | Drop to the concept's "minimum complete cut" (`game-concept-shortlist.md`) |
| Wed 15:00 | Same throwaway build: the Legion's built-in gamepad reaches UE (a stick or button press registers in the packaged build). UNVERIFIED which controller mode Windows exposes | Fix the pad mode before Thu 01:00; never ship without the pad |
| Thu 01:00 | Move + core verb bound for keyboard/mouse **and** gamepad in Enhanced Input; keyboard/mouse play-tested on the desktop | Add the gamepad mappings before any new feature |
| Thu 17:00 | Build #1 launches on the Legion **and the core loop plays with the built-in gamepad alone** | Stop feature work until both pass |
| Thu 20:00 | Build #1 still fails for engine reasons twice | Hub + owner: 5.8.4 fallback via copy (costly; this is why the Wed 15:00 fork exists) |
| Fri 19:00 | Full run in build #2, played by the owner, **on the Legion gamepad** (menus, pause, restart, quit included) | Sat morning: cut beat 3 or merge beats to reach a full run |
| Sat 10:00 | **Risk fork:** owner says the verb is fun in 10 s, agent tester fun >= 3/5, judge Fun Factor >= 3 | Bail to the named safe fallback now (not at 22:00) |
| Sat 22:00 | Feature freeze | No exceptions; unfinished features are cut, not finished |
| Sat 23:30 | Insurance build processed on itch | Retry with `legion_ship.py --from-step 3` or `4` before sleeping |
| Sun 13:00-14:30 | Final build passes the agent + visual gates and a full gamepad-only run on the Legion | Keep the insurance build; do not replace it |
| Sun 16:59 | `jam_clock.py check` exit 10 | Package/upload only |

**Drop first when behind (top = first to go)**

1. Extra beats or chapters past two (keep chapter select to what exists).
2. Characters with animation; use an object, creature or abstract hero (`win-plan.md`).
3. Extra obstacle or enemy types.
4. Settings screen (keep pause + Quit).
5. Cloud 3D extras and hero swaps; keep the art-direction set.
6. Custom SFX past one per action (MetaSound, then Kenney CC0 with a ledger line).
7. Extra music variants (keep one track per state).

**Never cut:** the ending and end screen, Quit path, restart, theme visible on the title and in the first minute,
juice on the core verb, a sound for every action, the video, the dev log, the insurance upload.

**Mock lessons wired into this plan**

| Mock | What went wrong | Where the plan answers it |
| --- | --- | --- |
| 10 | Ran past the hard stop; MCP edits never saved, build shipped the old level; autopilot on in the clip | Hard stops on every card; VERIFIED before every package; agent playtest with real input |
| 12 | Stuck 3 h on a port with no timeout; idle 19 min after an upload; said "done" twice early; tools changed mid-run (`canon/jam-session-routine.md`, `canon/jam-hard-stop-clock.md`) | Waits with timeouts; Monitor/waitfor; idle list; `master` tooling freeze Wed 19:00 |
| 14 | Legion screen lock blocked playtest and video | Owner disables idle lock Wed 10:00 |
| 15 | Lemonade reloaded by the inbox sorter; no 5.9 on Legion; Linux packaging blocked | Sorter paused; `gpu-preflight` before each job; Wed 12:00 throwaway 5.9 package |

## 5. Zoom-in: first 3 hours after the theme reveal (Wed 11:00-14:00)

| Time | Owner | Agents |
| --- | --- | --- |
| 11:00-11:45 | Watch; write the exact theme words and any rule news | Hub notes rule news for `RULES.md` |
| 11:45-12:15 | 10 readings, literal to sideways, on paper | Run `theme-spread-prompt.md` Prompt 1 (readings + 5-concept theme fit + candidate list in one answer, ~25 s measured) |
| 12:15-12:45 | Lunch; read the agents' theme-fit table; add your missed readings | Hold for the owner's readings (Prompt 1 already covered the shortlist fit) |
| 12:45-13:15 | Filter to 3 (no multiplayer, open world, dialogue trees, humanoid hero) | Prompt 2 in the same session: filter, score on the rubric + "core verb playable in 12 h", risk fork, one-pager draft (~40 s measured) |
| 13:15-13:45 | Pick leader + runner-up | Legion throwaway 5.9 package result in (engine fork input) |
| 13:45-14:00 | Name the risk fork and safe fallback | Start the one-pager draft (paper; committed at 21:00) |

## 6. Zoom-in: last 6 hours (Sun 12:00-18:00)

| Time | Owner | Agents | Check |
| --- | --- | --- | --- |
| 12:00 | Fix freeze; lunch | Last VERIFIED, `presubmit_gate.py`, flag, fast-forward | presubmit PASS |
| 12:45 | - | `legion_ship.py` final (pretest) | ship OK |
| 13:00 | - | Agent playtest gate + `visual_playtest.py` gate + judge pass | GATE PASS, else keep insurance |
| 13:45 | Decide: final replaces insurance? If yes, the agent flags and pushes `--from-step 4 --target <real page>` | Push on the owner's yes | Decision written; build processed |
| 14:00 | Watch cut | Final video, loudnorm, 1080p, 30-60 s | Spec check |
| 14:30 | Upload unlisted YouTube (owner sign-in) | - | Link copied |
| 15:00 | Edit + post final dev log and summary | Drafts; credits; AI disclosure; "Tools you used" | Posted |
| 15:45 | Itch page: build channel, text, AI fields (Graphics, Sound), credits | Paste-ready text file | Page complete |
| 16:00 | **Uploaded** | `jam_clock.py status` | Build processed on itch |
| 16:15 | Entry form: team, name, email, Team Owner, game name, video, dev log | - | Form filled |
| 16:30 | **Submit**; screenshot | Stop all feature work | Submitted |
| 16:59 | - | Clock PACKAGE | Nothing new |
| 17:44 | Page/text fixes only | Clock FINAL | - |
| 17:59 | Closed | Clock EXPIRED | - |

## 7. Conflicts found and rulings (Fable review 2026-11-10; repo `AGENTS.md` wins, the owner's words beat hub habits)

| # | Conflict | Ruling |
| --- | --- | --- |
| C1 | `AGENTS.md` jam-week autonomy (merge to `jam-integration` freely, fast-forward `master` at the four gate builds after a flag) vs the hub's "every merge needs a GO" | **`AGENTS.md` wins inside the window** (owner-written, PR #23): `jam-integration` free; `master` fast-forward at the four gates with a flag, no wait; pretest pushes free; real-page pushes flagged, owner awake. Outside the window the GO rule holds |
| C2 | Memory caps: `AGENTS.md`, runbook and `launch-editor.sh` default use 26G/28G + 8G swap; hub says 16G / 2G | **26G/28G/8G** for the editor and GPU jobs (repo profile; the hub cap is for side jobs). Keep live workers at 4 (oomd, 2026-11-05). Owner may lower it; then set `LAUNCH_SCOPE_CMD` |
| C3 | Lemonade restore: runbook says use the ctx `gpu-preflight` prints (32768 vs 65536 open); hub says 32768 | **32768** (`~/.claude/CLAUDE.md`; readiness 11-06 shows the box back at 32768, mismatch gone) |
| C4 | Legion 5.9: `AGENTS.md` said Epic Launcher install at `C:\Dev\UE_5.9`; hub says source build (*update 2026-11-10:* confirmed, editor built, see G2) | **Source build at `C:\Dev\UE_5.9`** (task `UE59Build`, finishing Wed morning). Same path, so `--engine C:\Dev\UE_5.9` holds. `AGENTS.md` line 40 is stale on "Launcher"; Development config as recommended (runbook line 236 caveat on Shipping with a source build) |
| C5 | `AGENTS.md` says `claude-loop-revive.service` revives the loop after reboot; runbook says megajam is not on the revive list and the 300 budget is not saved | **Checked read-only:** the service is enabled and runs `claude_loop_revive.sh`, which revives every project in `~/.local/state/proj/wanted`; `proj start NAME` adds the mark, `proj stop` removes it. `claude_loop.sh` now writes `HANDOFF_*` to `<state>/ENV` and revive reads it back, so the 300 budget survives a reboot. Today `wanted` has `megajam-mock`, not `megajam`: it joins the list the moment `proj start megajam` runs. Runbook lines 167-168 are stale. After a reboot: `proj list`, and only if `megajam` is not `busy` run `HANDOFF_MAX_RESTARTS=300 proj start megajam` |
| C6 | Hub "no itch push" overnight vs `legion_ship.py` always pushing | **Overnight packaging allowed to the default pretest page** (private, built for this); the ban is only on the real page. One package per night, 07:30, after VERIFIED |
| C7 | Perk reminder Thu 08:00 (Anthropic claim) falls in assumed sleep | 08:30 stands (no deadline that morning) |
| C8 | Repo default branch is `master`, not `main` | `master` |
| C9 | `AGENTS.md` autonomy header says "Nov 11 00:00 ET"; the window opens Nov 12 00:00 ET (= Wed 21:00 PT, `RULES.md`) | `RULES.md` times; Rule 7(h) holds until 21:00 PT Wed |

Kickoff (Wed 11:00), window open (Wed 21:00) and close (Sun 17:59) agree across `AGENTS.md`, `RULES.md`,
`jam-clock.md` and the hub.

Sources: `PLAN.md`, `stages/00_prep/references/win-plan.md`, `stages/00_prep/references/jam-day-runbook.md`, `stages/04_ship/references/jam-clock.md`, `stages/04_ship/references/legion-ship.md`,
`stages/00_prep/output/mock-jam-findings-10.md` to `-15.md`, `stages/00_prep/references/mock-jams-10-14-plan.md`, `stages/03_playtest/references/agent-playtest.md`,
`stages/03_playtest/references/judge-pass.md`, `stages/02_build/references/asset-chain.md`, `_config/reference/ai-providers.md`, `stages/04_ship/references/capture-setup.md`,
`stages/01_concept/references/game-concept-shortlist.md`, `RULES.md`, hub `perk-watch.md` (2026-11-10).

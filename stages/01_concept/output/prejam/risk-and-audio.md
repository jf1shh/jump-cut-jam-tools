# Jump Cut: risk register with triggers, and the audio cue table

2026-11-11, pre-jam planning text only (Rule 7(h)): no sound, music or code exists before Wed Nov 11 21:00 PT. The build
target is [`../gdd.md`](../gdd.md); where this file disagrees with it, the GDD wins. Anything the GDD does not fix is marked
**Proposal** and listed in section 5.

Two jobs. Section 1-3: one risk register that merges the bail rules in `stages/00_prep/references/jam-execution-plan.md`
§4 ("exec §4"), the gates and cut order in GDD §9 and §10, and the risk table in `stages/00_prep/references/win-plan.md`,
each with a trigger time. Section 4: the one audio cue table. Step-by-step recovery for crashes, outages and lost work
stays in `stages/04_ship/references/jam-recovery.md` (its IDs such as E7 and T4 are cited, not copied).

Who: **A** = the lead agent, **O** = the owner, **H** = the hub. All times PT.

## 1. What changed when the older plans were merged

The GDD (locked 2026-11-11 13:31) is newer than both plans. These older rules no longer apply, so no trigger below uses them:

| Older rule | Now |
|---|---|
| exec §4 "Sat 10:00 risk fork: bail to the safe fallback" and win-plan D6 "named decision point on day 3" | GDD §9: the fork is decided **Thu 21:00** after the stranger test. No concept switch after that. Sat 10:00 is a scope check only (applies §10) |
| exec §4 "Thu 12:00 greybox gate fails: drop to the concept's minimum complete cut" | The GDD has no such section. Its cut order is §10, applied from the top |
| exec §4 "Fri 19:00 missed: cut beat 3 or merge beats" | GDD §9: "cut per §10" (extra replay angles first, then Scene 3) |
| exec §4 generic drop list (extra beats, animated characters, enemy types, settings screen) | GDD §10 cut order and never-cut list. Settings beyond volume and screen-shake are already out of scope (GDD §5) |
| exec §1 Thu 18:00, Fri 18:00 and the N1-N3 cards: "GPU: music with `gen_music.py`" | GDD §7: no local music generation. Music is one CC0 track plus MetaSound stingers (owner pick, README item 19) |
| exec §1 Thu 19:00 "hand playtest" then Thu 20:00 "fixes" | GDD §9: Thu 20:00 is the stranger test ([`stranger-test.md`](stranger-test.md)). The 19:00 playtest is its warm-up run |
| exec §4 Thu 20:00 "build #1 fails twice for engine reasons: 5.8.4 via copy" | Still true, but it now falls on the stranger test: with no launching build the gate cannot run (R12) |

## 2. Risk register

Trigger column: **Early** is a check that warns; **Hard** is the time the action fires. "Source" tags are in the risk text:
gdd, exec, win (win-plan), rec (jam-recovery). Rows marked **Proposal** add a trigger the older plans lack.

### 2.1 Feel and teaching (the stranger test)

| ID | Risk | Early sign | Trigger (PT) | Action | Owner |
|---|---|---|---|---|---|
| R1 | The cut reads as lag, a glitch or a teleport (gdd §9 c; onboarding §3 rule 2) | Owner calls it "stutter" in a hand run; the inset and the landing differ in a step shot; the determinism test is red | Early: Thu 09:00 and 14:00 owner hand runs. Hard: Thu 20:00 stranger test, item (c) | Fix the cause first: hit-stop, the one black frame, timecode jump, inset equals landing. If a stranger fails (c): **Jump Cut without preview**, decided by Thu 21:00 (gdd §9) | A fixes, O decides |
| R2 | The hold preview is too slow or wrong on the Legion: one low-res SceneCapture runs while held (gdd §3, §8; win perf list) | **Proposal:** under 45 fps during a hold on the Legion; the capture trails the world; wrong hazards in the inset | Early: Thu 17:00 first Legion run (fps log while held). Hard: Thu 20:00; recheck on build #2 Fri 16:00 | Lower the capture size and update rate; Medium scalability; Lumen and VSM off. **Proposal:** if a hold still drops under 30 fps: no preview, the same fallback as R1 | A, O confirms |
| R3 | Strangers do not learn the verb: prompt unseen, goal unclear (gdd §2, §9 a and b) | A tester holds and never releases; never reads the prompt; cannot say the goal by 0:30 | Early: Thu 19:30 warm-up run. Hard: Thu 20:00. (a) fail means no preview; (b) fail alone means tune and retest Fri 10:00 | Tune prompt timing and size, the board and the MustCut card on the DataAsset. Do not add text walls (onboarding §1) | A tunes, O decides |
| R4 | The car does not feel good (gdd §9) | Owner would not keep driving in a hand run; testers answer no to "would you keep playing" | Early: Thu 09:00 hand run; Thu 12:00 `greybox_gate.py check`. Hard: Thu 20:00, decided Thu 21:00 | **Rolling!** on the same scene clock, set pieces and replay. No concept switch after Thu 21:00 | O decides, H records |
| R5 | Plumbing or the greybox loop is not proven (gdd §9 Thu 01:00; exec §4 Thu 01:00 and Thu 12:00) | At 01:00: build does not package, car off the spline, no stunt, hold/cut/cancel missing on one input, determinism test red | Hard: Thu 01:00 (plumbing only, cannot kill the concept); Thu 12:00 `greybox_gate.py check` | 01:00 miss: fix plumbing first, no new features. 12:00 miss: stop adding stunts, keep to Scene 1 plus cut, crash and economy, apply §10 from the top | A, H tells O |
| R6 | Too many crashes or film starvation: gate (d) fails, or the economy soft-locks (gdd §4) | More than 3 crashes in hand runs on S1-3 or S1-6; film sits at 0 with no easy stunt after it | Early: Thu 14:00 hand run. Hard: Thu 20:00 item (d); retest Fri 10:00 | Tune windows, slack, the three-crash safe lane and crash handling on the DataAsset. Keep the easy stunt after the zero point | A |
| R29 | Two strangers cannot be found (gdd §9) | Fewer than two confirmed | Early: ask three on Wed. Hard: Thu 18:00 confirmed | One stranger counts. The owner's run never counts ([`stranger-test.md`](stranger-test.md) §2) | O |

### 2.2 Schedule and scope

| ID | Risk | Early sign | Trigger (PT) | Action | Owner |
|---|---|---|---|---|---|
| R7 | Scene 1 and the cut moment are not at final quality by Fri 19:00 (gdd §9 AAA; exec §4 Fri 19:00) | Fri 14:00: Scene 1 not played start to wrap in PIE; build #2 late | Early: Fri 14:00. Hard: Fri 19:00 (owner plays build #2 on the Legion pad: menus, pause, restart, quit) | Apply §10 from the top. Keep the feel budget order: cut moment, car feel, crash and take two, audio | A, O |
| R8 | Day 3 runs late (win: scope creep, High; gdd §10) | Sat 10:00: open items exceed hours left; Scene 3 not playable in greybox | Hard: Sat 10:00 scope check. Freeze Sat 22:00; nothing new starts after 21:30 | Cut in the GDD order: 1 extra replay angles, 2 Scene 3 (ship two scenes with wrap clips, deleted scenes, stars), 3 the end-card pair, 4 Critic text, 5 the Director's Cut take, 6 saturation steps. After 22:00 an unfinished feature is cut, not finished. Never-cut list stands (§10) | O, H |
| R9 | Content volume: 25 stunts on three sets, each a curve-data job on the one `Stunt` class (**Proposal**) | Scene 2 (9 stunts) not playable by Fri 22:00; Scene 3 (10) not by Sat 10:00 | Fri 22:00; Sat 10:00 | Reuse hazard shapes with new curves; cut Scene 3 first (§10 item 2) | A |
| R10 | C++ lands only on jam night and Live Coding is not on the Linux editor (gdd §8) | A change needs an editor restart; a compile error blocks the Blueprint work | Hard: Thu 01:00 plumbing; any later C++ fix | Batch C++ edits. Every tunable is a UPROPERTY or on the DataAsset. After Thu, agents change data and Blueprints, not C++, unless a bug forces it | A |

### 2.3 Build and engine

| ID | Risk | Early sign | Trigger (PT) | Action | Owner |
|---|---|---|---|---|---|
| R11 | Stunt determinism fails, or Tick, a Timeline or physics leaks into a `Stunt` child (gdd §8) | The evaluate-at-`T`-and-`T+Δ`-twice test is red; the replay differs from the live run | Hard: before every package (Thu 01:00, build #1 Thu 16:00, Fri 16:00, Sat 22:00, Sun 13:00) | No package until green. Move the hazard to curve data. Never loosen the test | A |
| R12 | No launching Windows build, or an engine problem (win: no build path; exec §4 Wed 15:00, Thu 17:00, Thu 20:00; rec E7-E10) | Throwaway package fails; build #1 fails to launch or crashes on Windows | Wed 15:00 fork (5.9 default, 5.8.4 fallback per AGENTS.md; confirm the throwaway package result). Early: Thu 17:00 build #1 launches **and** plays on the pad. Hard: Thu 19:30 no launching build; Thu 20:00 two engine failures | Per rec E7: 5.8.4 via a copy (costly). **Proposal:** run the stranger test on the newest build that launches; if none by 19:30, the Thu 21:00 default is Jump Cut without preview, confirmed by O and a Fable agent | A, O, H |
| R13 | The Legion pad is not seen, or the glyphs are wrong (exec §4 pad rows; gdd §2) | A stick or button does not register in the packaged build; a pad shows SPACE | Hard: Thu 01:00 mappings bound; Thu 17:00 core loop on the pad alone | Fix the pad mode before any new feature. Never ship without the pad | A, O (Windows setting) |
| R14 | Editor crash, hang or slow MCP (win: MCP serial; rec E1-E3) | MCP calls time out; `launch-editor.sh` exits 8 or 9; no `UnrealEditor` process | Any time. Two failed relaunches in a row | Copy `Saved/Logs` and `Saved/Crashes` to `stages/04_ship/output/crash-logs/<stamp>/`, relaunch, use `mx.py` over plain HTTP. After two failures: file-only work until the owner looks | A |
| R15 | The run recorder or replay is not deterministic, so the wrap clip cannot be built (gdd §6, §10) | The replay shows poses the live run did not | Early: Fri 15:00. Hard: Fri 19:00 | **Proposal:** the wrap clip falls back to an authored pass (fixed cameras, the ghost car on its authored line) instead of a recording of the run. The Scene 1 wrap clip and the reel are never-cut. Cut extra angles first | A |
| R16 | First-run hitches and shader stutter on judges' PCs (gdd §8) | Stutter in the first minute on a `-clearPSODriverCache` run; the PSO cache is missing | Early: Fri 16:00 build #2 (the first cold-start test). Hard: Sat 22:00 build #3; Sun 13:00 final | Bundle the PSO cache from one QA run; title-screen prewarm with the loading reel card; cut Niagara counts | A |
| R17 | Weak GPUs, or a zip over 1 GB (gdd §8; win perf list; rec E12) | Legion under 60 fps at 1080p in the busiest stunt; a ship log over 800 MB (**Proposal** threshold) | Hard: Sat 15:00 Legion perf pass (exec §1); every ship | Default scalability Medium. Smaller textures, drop unused cooked content. butler may replace the zip above 1 GB | A |

### 2.4 Content, art and audio

| ID | Risk | Early sign | Trigger (PT) | Action | Owner |
|---|---|---|---|---|---|
| R18 | Art is mismatched or unreadable in black and white (win: AI meshes mismatched; style guide §2, §4) | In a greyscale screenshot the hazard, car and mark do not separate by value | Early: Thu 13:00 master material check; every new stunt. Hard: Fri 13:00 asset swap | One master material per look (`M_Set`, `M_Car`) with `MI_` children. Keep the primitive where a swap fails the greyscale test. Nothing sourced is the first thing a judge sees | A |
| R19 | No usable CC0 track (README item 19; concepts §5) | No candidate with a CC0 1.0 page that loops cleanly | Early: Thu 18:00 first track in. Hard: Fri 12:00 | Option B: a MetaSound funk loop (3-5 h), judged by ear. Option C (cloud AI music) only after the owner reads that provider's terms, logged. A CC0 track goes in `sourced-assets.csv` | A picks, O listens |
| R20 | MetaSound authoring through MCP or Python is unproven (**Proposal**, UNVERIFIED) | The first stinger is not playing 60 min after work on it starts | Hard: Thu 11:00 check | Use a CC0 effect (Kenney) with a ledger line for that cue (exec §4 drop list item 6). Keep the cue list in section 4 small until one works | A |
| R21 | Audio missing or wrong, and an agent cannot hear it (win: a silent moment reads as unfinished; exec Sat 11:00) | A cue in section 4 has no asset or never fires; the owner hears clipping, a hole or a pop | Hard: Thu 19:00 owner ear check; Fri 19:00 Scene 1 sound final; Sat 11:00 "every action has a sound" | The cue-fire log and the owner's ears (section 4.4). Cut stretch rows first. SFX on every action is never cut | A, O |
| R22 | A white flash or fast flicker sneaks in (gdd §3; onboarding §5) | Any white or near-white frame in a step shot; the hold ring blinks | Hard: before every package | One black splice frame only. Grain bursts never raise brightness. The photosensitivity card stays at boot | A |
| R23 | A paid or cloud asset provider is down, out of credit, or its terms are not reviewed (rec S4, S5) | `gen_asset.py --providers-check` shows it unset; 402 or 429; cloud rows jump in `asset-pipeline-log.csv` | Any generation batch; Thu 12:00 first batch | Switch provider. Local generation only as a last resort (local AI is off for the jam). Hero car and props fall back to primitives | A |

### 2.5 Contest, rules and delivery

| ID | Risk | Early sign | Trigger (PT) | Action | Owner |
|---|---|---|---|---|---|
| R24 | Pre-jam content, a disqualifier (Rule 7(h); AGENTS.md) | A project, level, asset, sound or track exists before the window | Hard: Wed 21:00 | Words, storyboards and labelled pictures only until then. The project is created at 21:00 in `~/Projects/megajam-game`; the one-pager is committed at 21:00. `contest_guard.py` stays on | A, H |
| R25 | Third-party IP, real or film cars, or a bad licence (Rules 8, 15(d); gdd §5, §7) | A name, livery, logo or silhouette echoes a real car or film; a font or sound with an unlisted licence | Hard: before every package; Sat 22:00 credits list; Sun 09:00 | Rename or redraw. Every sourced item and font is in `sourced-assets.csv` at import. Banned: Hunyuan3D, Qwen-Image 2.1, 4x-UltraSharp | A, O |
| R26 | The rules change (win: Rules change) | The Box PDF differs from the digest in `RULES.md` | Hard: Sun 09:00 re-read (win-plan: Nov 10 and Nov 15 morning); daily 11:00 livestream skim | Update `RULES.md`; H adjusts the plan | O, H |
| R27 | Insurance upload missed (win; rec T4) | Sat 23:30: the build is not processed on itch | Hard: Sat 23:30 | `legion_ship.py --from-step 3` or `4` with `--target`, flagged, owner awake. Retry before sleeping; else Sun 08:30 | A flags, O |
| R28 | The final build fails its gates (exec §4 Sun 13:00-14:30; rec T7) | Agent or visual gate fails; the full pad-only run on the Legion fails | Hard: Sun 13:00-14:30; Sun 16:00 uploaded; 16:30 submitted; `jam_clock.py` 16:59 PACKAGE, 17:44 FINAL, 17:59 EXPIRED | Keep the insurance build, do not replace it. After 16:00 stop building. The owner clicks Submit (Rule 17) | O |
| R30 | Video capture fails (rec T5; gdd §8) | Black frames, no file, or the hold not visible before cuts | Early: Sat 19:00 rough cut. Hard: Sun 14:00-14:30 | Display-capture fallback; the N4 raw clips; any 30-60 s of real 1080p play. Gameplay in the first 5 s, end on the title card | A, O |
| R31 | A dev log night is missed (Glass Box; gdd §10 never-cut) | No entry by 23:00 | Each night 23:00-00:00; Sun 15:00 final | `gen_devlog.py` draft; the owner posts | A drafts, O posts |
| R32 | Owner away or asleep when needed; fatigue (rec T8; win: sleep 6 h) | An ask unanswered | Nightly 01:00-08:30 | Agents work and merge on `jam-integration`, push to the pretest page only, never the real page, no night fast-forward of `master` | A |
| R33 | The loop stalls, burns restarts, or work is lost (AGENTS.md runbook; rec S2, S3, D1) | `proj list` idle while the window is open; over 20 restarts in a night; last commit older than 30 min | Check each loop turn; commit every 30 min or slice | AGENTS.md manual fallback steps 1-6; write a blocker line; restore from git (rec D1-D4) | H, A |

## 3. Trigger clock (in time order)

| When (PT) | Check or fire | Risks |
|---|---|---|
| Wed 21:00 | Window opens: nothing before this existed. Three testers asked today (Wed) | R24, R29 |
| Thu 01:00 | Plumbing gate; pad and KB/M mappings bound; C++ landed | R5, R10, R11, R13 |
| Thu 09:00 | Owner hand run: cut and car feel | R1, R4 |
| Thu 11:00 | First MetaSound stinger plays | R20 |
| Thu 12:00 | `greybox_gate.py check`; first generation batch | R5, R23 |
| Thu 13:00 | Master material and greyscale check | R18 |
| Thu 14:00 | Owner hand run: crashes, film | R1, R6 |
| Thu 16:00-17:00 | Build #1 packaged; launches and plays on the pad; fps in a hold | R2, R11, R12, R13 |
| Thu 18:00 | First CC0 track in; two testers confirmed | R19, R29 |
| Thu 19:00-19:30 | Owner ear check; build frozen; warm-up run | R3, R21 |
| **Thu 20:00** | **Stranger test** | R1, R3, R4, R6 |
| **Thu 21:00** | **Fallback decided, never later** | R1-R4, R12 |
| Fri 10:00 | Retest if only (b) or (d) failed | R3, R6 |
| Fri 12:00 | Music final (CC0 or MetaSound loop) | R19 |
| Fri 13:00 | Asset swap batch | R18 |
| Fri 14:00 | Scene 1 start to wrap in PIE | R7 |
| Fri 15:00 | Replay deterministic | R15 |
| Fri 16:00 | Build #2; cold-start PSO test; recheck the hold on the Legion | R2, R16 |
| **Fri 19:00** | **AAA gate:** owner plays build #2 on the pad; Scene 1 sound final | R7, R21 |
| Fri 22:00 | Scene 2 playable | R9 |
| **Sat 10:00** | **Scope check** (§10); Scene 3 playable | R8, R9 |
| Sat 11:00 | Audio pass: every action has a sound | R21 |
| Sat 15:00 | Legion perf pass | R17 |
| Sat 19:00 | Rough video cut exists | R30 |
| **Sat 22:00** | **Feature freeze;** build #3; credits list; IP check | R8, R11, R16, R25 |
| Sat 23:30 | Insurance upload processed | R27 |
| Sun 09:00 | Rules re-read; tools-used list | R25, R26 |
| Sun 12:00-13:00 | Fix freeze; final build | R11, R16 |
| Sun 13:00-14:30 | Final gates; video | R28, R30 |
| Sun 15:00-17:59 | Dev log final; uploaded 16:00; submitted 16:30; clock 16:59, 17:44, 17:59 | R28, R31 |

## 4. Audio

GDD §7 is the rule; [`style-guide.md`](style-guide.md) §8 is the mood; [`hud-ui-spec.md`](hud-ui-spec.md) names the
`S_UI_*` hooks; [`onboarding.md`](onboarding.md) §3 sets feedback timing. **Owner's pick (README item 19):** one CC0
track picked after 21:00 and listed in the sourced-assets ledger, with MetaSound stingers and the low-pass. Nothing is
made or downloaded before 21:00. No voice and no dialogue (gdd §5): "CUT!" is text plus the clapper.

### 4.1 Rules

- **Music runs on real time and never seeks.** One persistent music player outlives every level, retry and crash. A cut
  adds a stinger over it, a crash adds the clapper over it, the hold low-passes it. It is never restarted or slowed.
- **Sound never carries a rule alone** (gdd §4): every cue that matters also shows a word or a number.
- **Naming:** `S_` prefix for every audio asset (`CLAUDE.md`). A MetaSound source takes the same `S_` name as its cue.
  Names already used in the style guide or the HUD spec are plain; new names are marked **Proposal**.
- **Buses (Proposal):** Master with Music, SFX and UI submixes. The pause menu's volume control moves Master (gdd §8).
  Peaks under -3 dBFS and at most 16 voices at once on the Legion (win perf list); both are starting values the owner
  tunes by ear.
- **Time dilation (Proposal):** audio ignores the 0.3x hold. The one exception is the engine loop, which follows the
  car's speed and so drops in pitch while held.
- **Source key:** **M** = MetaSound built in the jam (original; note it in the dev log). **C** = a CC0 file, needs a
  ledger line at import (`scripts/sourced_assets.py`), Kenney or a CC0 1.0 page only, never "royalty free" or NC.
  **G** = cloud-generated: not planned; only after the owner reads that provider's terms, logged in
  `asset-pipeline-log.csv` (local generation is off). Where two letters appear, the first is the plan, the second the
  fallback.
- **Priority:** **Thu** = a stub in the stranger-test build (the feel budget's first three items: cut moment, car feel,
  crash and take two). **Fri** = final for Scene 1 by the Fri 19:00 gate; Scenes 2-3 reuse it and are checked at the
  Sat 11:00 audio pass. **Stretch** = after the gates, cut first.

### 4.2 Cue table

| Cue | Trigger | Source | Loop / one-shot | Priority |
|---|---|---|---|---|
| `S_Music_Main` **Proposal** | Starts once, at the title or the first scene, runs on real time through title, play, pause, replays and Special Features. Never restarts on a crash, cut, retry or scene change. The loop point is crossfaded, never a seek on an event | C (one CC0 track, picked after 21:00); M loop if none fits by Fri 12:00 | loop | Thu stub, Fri final |
| (mix) Music low-pass | Hold starts: 150 ms ramp to a low cutoff (about 1 kHz, a starting value). Release, cancel or auto-cancel: back in 60 ms. Pause: **Proposal** keep the music running, low-passed | M (submix filter) | n/a | Thu |
| `S_ProjectorWhir` | In with the hold's 150 ms ease; out on release, cancel or auto-cancel. Also under the wrap clip, the deleted-scene clip, the loading reel and the reel's title slate | M: filtered noise with a slow flutter at about 24 per second | loop | Thu |
| `S_InsetOpen` | The landing inset opens (hold plus 100 ms); part of the whir start | M | one-shot | Fri |
| `S_Splice_Click` | Release: at the one black splice frame, after the 60-80 ms hit-stop. Reused for `S_UI_TimecodeJump` and for every cut in the replays | M | one-shot | Thu |
| `S_Tape_Stop` **Proposal** | At the black frame: a short pitch-down whine (about 0.3 s, tuned by ear) over the music | M | one-shot | Thu |
| `S_Tape_Start` **Proposal** | At the landing, with the grain burst and the timecode jump: a pitch-up whoop; the whir fades out | M | one-shot | Fri (Thu may skip it) |
| `S_Cancel` | B pressed, or the 1.5 s auto-cancel; also a release after the cut window closed. A soft tick with the whir out | M | one-shot | Thu |
| `S_Lane_Tick` **Proposal** | A landing-lane change during the hold: a soft tick (onboarding §3) | M | one-shot | Fri |
| `S_RingTick` | The hold ring enters its last 0.3 s | M | one-shot | Fri |
| `S_DryClick` | A press at 0 film: the "NO FILM" stamp | M | one-shot | Thu |
| `S_Engine_Loop` **Proposal** | While driving: pitch and level from the speed curve f(T). RT adds a short pitch bump on a pad (cosmetic, with the small FOV kick). Follows the car's slow-down in the hold | M: a saw and noise mix with an RPM input | loop | Thu |
| `S_Tyre_Chirp` **Proposal** | A lane change; louder on a late or tight one (storyboards board 3) | M: band-passed noise squeal | one-shot | Fri |
| `S_Crash_Crunch` **Proposal** | Impact, at the start of the 120 ms hit-stop. The SFX bus dips for the black and "hush" (music keeps running) | M, or C if the owner hears it thin | one-shot | Thu |
| `S_Crash_Tumble` **Proposal** | The canned flip, 120-520 ms after impact | M, or C | one-shot | Fri |
| `S_Clapper` | The clapper slam "CUT! TAKE n" at 520 ms after impact | M: a wood crack from a noise burst and a resonant filter; or C | one-shot | Thu |
| `S_Clapper_Soft` | The scene board's stick closes at the start of every scene and retry; each "DELETED SCENE" slate. The same asset as `S_Clapper` at lower gain | M | one-shot | Thu stub, Fri final |
| `S_Whoosh_Wide` | Closest approach of a kept shot at the WIDE tier; short | M: a filtered noise sweep, one graph with a tier input | one-shot | Thu |
| `S_Whoosh_Close` | The same at CLOSE!; longer and louder | M | one-shot | Thu |
| `S_Whoosh_Perfect` | The same at PERFECT!; longest, adds a bright tick (style guide §8) | M | one-shot | Fri |
| `S_Stamp` | PERFECT!'s stamp thump, with the 2-frame shake (off when shake is off) | M | one-shot | Fri |
| `S_UI_FilmSpend` | A cut spends film: the last cell flashes and empties (120 ms) | M: a film-punch click | one-shot | Thu |
| `S_UI_FilmGain` | Film gained: one tick per cell filling, 80 ms apart, pitch rising | M | one-shot per cell | Thu |
| `S_UI_FilmEmpty` | The strip reaches 0 | M: a dull low tick | one-shot | Fri |
| `S_UI_TimecodeJump` | The timecode digits jump on a cut | Shares `S_Splice_Click`, no extra asset (hud-ui-spec) | one-shot | Thu |
| `S_Haz_Twang` **Proposal** | Telegraph start (2.5 s before collision-on), 3D at the hazard: S1-1 rope | M | one-shot | Thu |
| `S_Haz_Horn` **Proposal** | S1-2 Prop Truck, S2-1 Alley Truck, with the headlights | M | one-shot | Thu |
| `S_Haz_Creak` **Proposal** | Buckling and groaning: S1-4 water tower, S2-2 crane, S2-4 scaffold, S3-4 bridge, S3-7 pipe rack | M | one-shot | Fri |
| `S_Haz_Rumble` **Proposal** | Falling and rolling: facades, barrels, pipes, the Scene 1 tower fall. Rises to collision-on | M: low filtered noise | one-shot | Fri |
| `S_Haz_Hiss` **Proposal** | S3-3 pipes, S3-5 air brakes | M | one-shot | Stretch |
| `S_Haz_Bell` **Proposal** | S2-9 level crossing bell, from 3 s out | M | loop until the train passes | Stretch |
| `S_Haz_Fire` **Proposal** | Burners, flare jets, the fire wall, the gas holder | M | one-shot | Stretch |
| `S_PencilScratch` | The Director's Note slides in (200 ms) and its underline draws (300 ms) | M: filtered noise scratch | one-shot | Fri |
| `S_UI_SlateTick` | The take number flips (200 ms). Also each menu move (style guide §8: typewriter ticks) | M | one-shot | Fri |
| `S_UI_Select` **Proposal** | A menu confirm or resume: a typewriter return ding | M | one-shot | Fri |
| `S_UI_Star` **Proposal** | Each star lands on the scene card; pitch rises per star | M | one-shot | Fri |
| `S_Swell` **Proposal** | Three seconds before a set piece, with the +6 m/s surge (fun-plan T 32; S1-6) | M: a riser | one-shot | Fri |
| `S_Wrap_Stinger` **Proposal** | "THAT'S A WRAP"; music keeps running. A short brass-style hit (instrument direction only) | M: stacked detuned saws with a brass envelope, about 1.5 s | one-shot | Fri |
| `S_Amb_Backlot`, `S_Amb_Street`, `S_Amb_Depot` **Proposal** | A quiet bed for each scene | M | loop | Stretch |

**Reuse, no new asset:** the wrap clip and the final reel use `S_Splice_Click` at each replay cut and `S_ProjectorWhir`
under the letterbox; the DELETED SCENE clip uses `S_Clapper_Soft` and `S_Crash_Crunch` on the ghost car's crash. The boot
and photosensitivity cards are silent. The loading reel reuses the whir.

### 4.3 Order of work

1. **Thu, before 14:00:** the three cut-moment cues (`S_Splice_Click`, `S_Tape_Stop`, the low-pass), `S_ProjectorWhir`,
   `S_Engine_Loop`, crash and clapper, the whoosh at two tiers, the film cues, the DRY click, the first two hazard
   cues, the music stub. First MetaSound proves R20.
2. **Thu 18:00:** the CC0 track, placed and looped.
3. **Fri by 19:00:** everything marked Fri at final level for Scene 1.
4. **Sat 11:00:** the audio pass over Scenes 2-3: the `S_Haz_*` family reused with new pitches. Stretch rows only after
   the gates and only if ahead.

### 4.4 How it gets checked (an agent cannot hear)

- **Fire log:** each cue logs a line when it plays. A step-shot or agent-playtest run must show the expected cue for each
  event in the table (hold gives `S_ProjectorWhir`, release gives `S_Splice_Click`, a crash gives `S_Crash_Crunch` then
  `S_Clapper`). **Proposal:** one automation test fails the package if any `S_` name in the table has no asset.
- **Owner ear check** on the Legion speakers, at Thu 19:00, Fri 19:00, Sat 11:00 and Sun 13:00: the cut sounds like one
  edit (click, tape stop, tape start, no gap, no pop); the music is low-passed in the hold, not slowed; the loop point
  has no click; the loudest moment (crash, clapper and music together) does not clip; the whir never covers the music.
- **Licence check:** every `C` source and the music track have a `sourced-assets.csv` line before the Sat 22:00 credits
  list (R25).

## 5. Open decisions from this file (all Proposals; none changes the GDD)

- **P1** Trigger times the older plans lack: Fri 14:00 Scene 1 in PIE, Fri 15:00 replay deterministic, Fri 22:00 Scene 2
  playable, Sat 10:00 Scene 3 playable (R7, R9, R15). Move them if the day plan moves.
- **P2** R12: with no launching build by 19:30 Thu, default to Jump Cut without preview.
- **P3** R15: an authored canned pass replaces the recorded wrap clip if the run recorder is not deterministic.
- **P4** Audio: the new `S_` names in 4.2, the bus layout, the 16-voice and -3 dBFS starting values, audio ignores the
  hold's 0.3x except the engine loop, pause keeps the music running low-passed.
- **P5** R20: MetaSound authoring through MCP or Python is unverified; Kenney CC0 with a ledger line is the named fallback.
- **P6** The fire-log test that fails a package when a cue in 4.2 has no asset.
- **For the hub:** add the index lines for `stranger-test.md` and `risk-and-audio.md` in the README table and
  `_config/CANON.md` (writers do not edit those files).

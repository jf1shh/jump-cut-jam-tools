# JUMP CUT: game design document (locked)

**Locked 2026-11-11 13:31 PT** by the owner ("Yes, lock it", relayed by hub 97), with Fable's final change list
(`superagent-sandbox/reports/Jump Cut red-team verdict.md`, section "Final change list for PR #176", items 1-29). This
file is the single source of truth for the picked concept. Where it is silent, the one-pager
[`jump-cut-concept.md`](jump-cut-concept.md) stands; where they differ, this file wins. Ideas and scores:
[`directors-cut-ideas.md`](directors-cut-ideas.md).

Pre-jam planning text only (Rule 7(h)). **Nothing below exists before Wed Nov 11 21:00 PT**: no HUD shell, no hit-stop
component, no camera helper, no C++ class, no asset.

## 1. Decision and framing

- **Title:** JUMP CUT (itch.io checked 11-11: no game by that name; alternate "Cut to the Chase"). Tagline (title
  screen + itch page): "Includes deleted scenes." (owner 2026-11-11; replaces "Your run. Your edit. Your director's cut.")
- **Pick:** Jump Cut 29/35 (leader), Rolling! 27/35 (runner-up and fallback), Cheat the Angle 26/35.
- **The stunt is the shot.** One authored `Stunt` type: hazard timing as a pure function of scene time `T`, a drivable
  line, an execution tier (easy / two-hop / timed gap), a shot value, a near-miss band, and a `MustCut` flag. There
  are no separate gold marks.
- **Theme in play:** your first run of a scene is the **Studio Cut** (you cut what you cannot do). The **Director's
  Cut take** (section 6) restores the deleted scenes. The deleted-scenes reel is core.
- **Core verb:** hold to look, release to cut to the next mark. **Loop:** title, Scene 1 to 3 on a studio backlot,
  each ending on a wrap with its Director's Cut clip, then the DVD Special Features end screen.
- **AAA** (owner word) = Scene 1 and the cut moment at final quality by Fri Nov 13 19:00. Day 1 feel budget order:
  cut moment, car feel, crash and take two, audio pass. **Addictive** = a judge restarts Scene 1 or takes the
  Director's Cut take once. Nothing is built for a second session.

## 2. Controls (each device plays the whole game alone; Enhanced Input from the first greybox)

| Action | Gamepad | Keyboard / mouse |
|---|---|---|
| Lane (during a hold: sets the **landing** lane; the live car keeps its lane) | Left stick or d-pad | A/D or arrows |
| Hold to look, release to cut | **A / Cross** | **Space** or left mouse |
| Cancel the look | **B / Circle** | **Shift** or right mouse |
| Engine rev (cosmetic only: sound + tiny FOV kick) | RT | none |
| Pause | Start | Esc |

LT is unused. **First minute:** the Scene 1 clapperboard carries one goal line, "Drive the stunts. Cut the ones you
can't. Film runs out." Then the first prompt sits on stunt 1 until done once: "Hold A to look. Let go to cut. B to
keep driving." (keys shown on KB/M). The first stunt is a free crash. A judge must know the goal inside 30 s.

## 3. Look and cut rules

- **Hold:** time eases to 0.3x over 150 ms; music is low-passed (not slowed); a full black-and-white workprint overlay
  with timecode; projector whir. **Looking is free.** Cap 1.5 s real time, then it **auto-cancels** (never auto-cuts).
  No cooldown.
- **The hold shows the landing only:** the next mark (one), at most ~5 s ahead, framed in an inset from one low-res
  SceneCapture that runs only while held, with the hazards near the landing drawn at the arrival time. No hazard ghosts
  at three times, no multi-mark choice. The drive line is read live from the stunt's telegraph (facade tipping, truck
  nosing in) at 0.3x.
- **Release = cut to the next mark:** locked camera, 60-80 ms hit-stop, **one black splice frame** (no white flash;
  add a photosensitivity card anyway), splice click, 5% punch-in, grain burst, timecode jump, tape-stop stinger. The
  cut window closes when the car reaches the stunt's collision-on line.
- **Marks:** exactly one per stunt, 2-3 s past the stunt in a clear zone. The mark after stunt N is the landing for
  cutting N and the restart point for N+1. A landing never puts a hazard inside 2 s.

## 4. Film economy (the one table; every number is a UPROPERTY on one DataAsset, no recompile to tune)

| Rule | Value |
|---|---|
| Reel size | 6 |
| Film at scene start | 3 |
| Cut | -1 film |
| `MustCut` stunt (shown as a "DIRECTOR'S NOTE: cut" slate) | costs 0. Scene 1 has one; Scene 3 has one long one |
| Kept shot: Wide / Close / Perfect | +1 / +1 and a bonus star point / +2 |
| At 0 film | cut button dead, "NO FILM" stamp; every non-MustCut stunt is drivable; the stunt after any likely zero point is tier "easy" |
| Most cuts in a row from a fresh scene | 3, so at least every other stunt is driven; all-cut is impossible in every scene |
| Crash | costs a **take**, never film; takes cost stars (5 stars needs 0-1 takes; formula on the scene card) |
| Stunts per scene | Scene 1 = 6, Scene 2 = 9, Scene 3 = 10 |

- **Crash:** 120 ms hit-stop, canned flip, clapper slam "CUT! TAKE n", hard cut to black, back at the previous mark
  (2-5 s back) with film at that mark's value; impact to control in under 1 s. Because film is never lost to a crash
  and MustCut is free, the 0-film + MustCut soft-lock cannot happen. After three crashes on the same stunt, the next
  hold highlights the safe lane (no name, no badge, no star penalty beyond the takes already counted).
- **Execution tiers:** about a third of each scene's stunts (all of Scene 3's non-MustCut stunts) need two lane hops
  inside ~0.6 s or a timed gap. Per-scene speed curves as f(T), with a surge before a set piece.
- **Near-miss tiers** (Wide / Close / Perfect) come from closest approach, with a stamp and a whoosh. Every tier, the
  film count and "NO FILM" show as text or a number as well as colour and sound (never colour or sound alone). Stars
  per scene from shots kept, near-miss quality and takes.
- **Not in the game:** streak multiplier, personal-best SaveGame, beat splice, critic style line. Saves stay out of
  scope.

## 5. Out of scope

Multiplayer, saves, online leaderboard, humanoid actors or dialogue, a level editor, settings beyond pause (volume,
screen-shake off), restart and Quit, a web build, Android (dropped, D-008). Owner ideas 2026-11-11 (split-screen co-op, a mod kit
for custom cars and stunt tracks, modifiers, photo mode) are triaged in the prejam README "Parked" list. **No real or film cars, car brands, characters or look-alikes** (e.g. Bond
cars, KITT): Rules 8 and 15(d) disqualify any third-party IP or trademark except the Unreal Engine logo. Movie homage
stays at the genre level.

## 6. Theme payoff inside the judge window

- **At every scene's wrap** (Scene 1 first, about minute 1.5): a skippable **10-15 s "Director's Cut of Scene N"**
  auto-plays: the deterministic replay with one camera change per cut, then one DELETED SCENE clip (3 s: a ghost car
  drives into the hazard on its authored danger lane, canned crash).
- **"Director's Cut take"** on the scene card: replay the scene with your cut stunts restored and their marks off, for
  extra stars. Optional; one flag per stunt; about 2-3 h of work.
- The final replay after Scene 3 is capped at 30 s of highlights; the Deleted Scenes reel at 3 clips.
- **End screen:** a DVD "Special Features" menu: Play the Director's Cut, Deleted Scenes, Critic's Review (stars only),
  Credits (the agents listed as crew, plus the real jam cut-list card). Stretch only (1 h, bottom of the list): two end
  cards, "Studio Cut" if the finale was cut and never restored, "Director's Cut" if it was driven or restored.

## 7. Look, audio, assets

- Every scene starts at ~50% saturation; full black-and-white is the **hold-only** look; kept shots step saturation up
  from that floor (cheap post blend, last on the cut list). Letterbox in replays only. Each hazard has its own key
  light; each scene gets one unique silhouette piece and its own light colour. One master material per look (`M_Set`
  with `MI_` children, `M_Car`).
- **Music runs on real time and never seeks.** One CC0 track listed in the sourced-assets ledger, or a MetaSound loop
  (no local music generation: local AI is off). Hold = low-pass; cut = tape-stop/start stinger; crash = clapper. SFX
  on every action: engine loop pitched from the speed curve, splice, whir, whoosh, wrap stinger, UI ticks.
- **Hero car**: an AI 3D model made in the jam from the hero-car concept (Tripo or Meshy, paid plans only; whichever
  result is better ships), with the wheels split so they spin and steer, recoloured to the cream look. Owner decision
  2026-11-12: "we should use tripo or mesh to generate the car its the star of the game it needs to be perfect". It is
  a visual mesh swap in `DA_Car_Number7` only; collision and handling stay as they are. Not a licensed kit: sourced
  assets are not reviewed or scored (Rule 15(c)) and the car is on screen all the time. Superseded: "built from
  primitives or a modelling-tool box model". Paid 3D credits go only to what the camera sees most (owner 2026-11-12);
  scenery and props come from the free CC0 packs (Kenney, Poly Haven) or Fab free claims, each with a
  sourced-assets.csv row. Concept sheets and title cards from the cloud image tools, logged per the ledger.

## 8. Build path and engineering rules

- **Live Coding is not available on the Linux editor** (verified 2026-11-11). All C++ classes (scene clock, `Stunt`
  base, car pawn, cut component, run recorder) land on jam night with every tunable as a UPROPERTY or on the
  DataAsset. After that, agents change data and Blueprints, not C++, unless a bug forces a restart cycle.
- **Content is data, so the game is mod-ready** (owner 2026-11-11: "built with modding in mind"). Code never
  hard-references a specific car, scene, stunt preset or modifier. Each is a data asset (PrimaryDataAsset) the game
  finds by type (one Asset Manager entry per type, so the cook keeps unreferenced assets): a car = mesh, livery and numbers; a scene = its level plus its ordered stunt list and values; a
  modifier = overrides on the tuning DataAsset and the film-look post. Same jam-night cost, and a post-jam mod kit can
  add cars and stunt tracks without new code. Not in the jam: loading player mods at runtime.
- The owner tunes feel and input by hand on the DataAsset. MCP calls are serial and slow (5-15 min a response), so the
  lead uses them for placement and wiring only.
- Hazards are curve data on the one C++ `Stunt` class; **Tick, Timelines and physics are banned in children.** One
  automated test evaluates every stunt at `T` and `T + Δ` twice and compares poses; it runs before every package.
- Package a Windows build on the Legion on jam night (throwaway, clean stage, no `-NoCleanStage`) and daily after.
  Bundle a PSO cache from one QA run plus a title-screen prewarm that spawns every Niagara system and material once.
  Call `DisableAllScreenMessages` at startup; grep for print-to-screen before packaging. **Plain UMG with explicit
  focus, not Common UI.**
- **Build config:** Development with "For Distribution" off (D-009). Test the first run with `-clearPSODriverCache`
  and show a short "loading reel" card while the prewarm runs. Default scalability Medium (judges may have weak GPUs).
  Pause menu gets volume plus a screen-shake off switch. Any web build must be Shipping, not Development (kickoff
  stream); none is planned.
- **Video:** continuous takes, timecode and the hold visible before each cut, gameplay in the first 5 s, end on the
  title card. Tools-used list for partner prizes (Hyper3D cash pool, NVIDIA RTX award): only tools really used.

## 9. Gates and fallbacks (PT)

| When | Gate | If it fails |
|---|---|---|
| Thu Nov 12 01:00 | **Plumbing only:** project packages on the Legion; car on the spline; one stunt; hold/cut/cancel on both inputs; determinism test green | Fix plumbing; this gate cannot kill the concept |
| Thu Nov 12 20:00 | **The real gate**, build #1 on the Legion gamepad, screen-recorded: two people who have never seen the game play the Scene 1 greybox (6 stunts, cubes allowed, cut juice and economy in) for 3 min each with only the on-screen prompt. **PASS = all four:** (a) each lands at least one cut inside 60 s; (b) each drives at least one stunt on purpose with film above 0; (c) asked "what happened when you let go?", neither says lag, glitch, bug or teleport; (d) each finishes Scene 1 with 3 crashes or fewer. At least one stranger if two cannot be found; the owner's run never counts; the recording is reviewed with a Fable agent before the call | See fallbacks below |
| Thu Nov 12 21:00 | **Fallback decided, never later** | Fail (a) or (c): **Jump Cut without preview** (press = instant cut to the next mark, same juice, marks, economy, replay). Fail "the car does not feel good" (owner plus both testers would not keep driving): **Rolling!** on the same scene clock, set pieces and replay. Fail only (b) or (d): tune the DataAsset, retest Fri 10:00 |
| Fri Nov 13 19:00 | AAA: Scene 1 and the cut moment at final quality; build #2 played by the owner on the Legion gamepad | Cut per section 10 |
| Sat Nov 14 10:00 | Scope check only (applies section 10); **no concept switch after Thu 21:00** | - |
| Sat 22:00 / 23:30 | Feature freeze; build #3; insurance upload | `PLAN.md` |
| Sun Nov 15 | Fixes to 12:00, final build 13:00, video 14:00, dev log 15:00, uploaded 16:00, **owner submits by 16:30** (deadline 17:59) | Keep the insurance build |

## 10. Scope cut order and never-cut

**Cut first to last when Day 3 runs late:** 1. extra replay angles (keep one change per cut); 2. Scene 3 (ship two
scenes with the wrap clips, deleted scenes and stars); 3. the Studio/Director end-card pair; 4. Critic card text (stars
only); 5. the Director's Cut take (the wrap clip and reel still carry the restore reading); 6. saturation steps (keep
the static 50% floor).

**Never cut:** the hold/cut/cancel verb; one mark per stunt; lanes; "Cut, take two" restart under 1 s; the Scene 1 wrap
clip; the deleted-scenes reel (3 clips); the near-miss stamp; stars per scene; the film economy table; both input
methods; pause and Quit; a daily packaged Windows build with PSO cache; real-time music plus SFX on every action; the
video; the dev log. A finished, fun game beats an ambitious broken one.

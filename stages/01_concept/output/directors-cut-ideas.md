# "Director's Cut": eight game ideas, scores and a top 3

2026-11-11, written about 12:00-13:00 PT, after the kickoff reveal (theme announced about 11:28 PT) and before the
contest window opens at 21:00 PT. **Planning text only (Rule 7(h)):** no game code, assets, levels or Unreal project
changes exist for any of these ideas. Working titles only; names are not checked for clashes yet.

Inputs: `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `stages/00_prep/references/jam-execution-plan.md`,
`_config/reference/canon/jam-design-cheatsheet.md`, `_config/reference/templates/scoring-rubric.md`, the kickoff notes
and rolling captions (read, not copied; paraphrased below). The five pre-jam shortlist concepts
(`../references/game-concept-shortlist.md`) were built for a connection/growth theme; none of their core decisions
change under "Director's Cut", so they are cosmetic fits and are dropped (section 5).

Picked concept and day plan: [`jump-cut-concept.md`](jump-cut-concept.md).

## 1. How the hosts framed the theme (paraphrase)

- It is about **your vision**: the specific edits you make and the final version you sign off on.
- Every developer has a feature that got cut: the mechanic scoped out at 2 a.m., the shelved idea. The jam is
  the place to finally build it.
- If you work with AI agents, **you are directing them too**: set the vision, hand out the work, and decide what
  goes in and what stays out.
- They asked for ambition, steered by deliberate choices.

Also from the stream (rules and tips, paraphrased): judges score 1-5 on ambition and innovation, a fresh and clever
take on the theme, fun, gameplay, visuals, level design and progression, and audio. Submit a 30-60 s gameplay video
that shows play in the first 5 seconds; a dev log link (optional, required for the Glass Box modifier); a tools-used
list (optional, needed for partner prizes such as the Hyper3D cash pool and the NVIDIA RTX award). Web builds made with
the 5.9 MegaJam Preview must be Shipping builds. Deadline Nov 15, 5:59 PM PT. Test-build on day two; keep notes as you
go.

## 2. Readings, literal to sideways

1. A film director shooting a movie scene. *(crowd)*
2. An extended cut of a film: restored deleted scenes, an alternate ending. *(crowd)*
3. "Cut!" as a command that stops the action.
4. Editing: removing frames changes what happened. A jump cut skips time.
5. Takes: shoot it again; the best take goes in the final film.
6. Camera work: what is in frame is the scene; sets are only built for the angle that sees them.
7. Directing a cast that does not always obey: actors, extras, or AI agents (the hosts' own hint).
8. Cut content: a game made of the features that were cut (the hosts' own hint).
9. The final cut as arrangement: the order of clips decides cause and effect.
10. A literal blade cut by a "director" character (pun). *(crowd)*

Readings 1, 2 and 10 are where most entries will land. Every idea below makes the theme **the rule of the core verb**,
not a skin (cheat sheet section 1 test: "you <verb> because <theme>").

## 3. The ideas

Shared constraints for all of them: solo developer plus AI agents, 4 days, UE 5.9 Preview (5.8.4 fallback), Windows
package built on the Legion, keyboard/mouse **and** the Legion gamepad must each play the whole game, stylized
low-poly, Teen rating, no third-party IP, **no local AI during the jam** (cloud tools only, through the repo adapters,
once the owner has set keys). UE feature names below are from our 5.8/5.9 notes
(`_config/reference/engine-reference/unreal/`); check each node or API in 5.9 before relying on it.

### 3.1 Jump Cut (verb: cut time)

A stunt car drives a movie-set course on rails while timed hazards fire around it (swinging lights, crossing
trucks, collapsing scaffolds, fireballs). **Hold** the cut button to see a ghost preview of the scene a moment ahead;
the longer you hold, the further ahead it looks. **Release** to make a jump cut: the car leaves the frames in between
and reappears ahead, so it passes through whatever was there. Every second you cut costs film stock; "money shots"
(golden marks on the road) only count if you drive through them uncut, and driving them refills film. Get hit and the
director yells "Cut, take two" and you restart from the last slate. At the end the game plays back your run as an
edited film, with a camera change at each of your cuts: your director's cut. **Theme use:** the cut is the core verb,
and the one decision you make over and over is the hosts' own line, what goes in and what stays out. **Clever take:**
film editing used as a dodge; the replay is a real edit of your own run, and the soundtrack jump-cuts with you.
**Scope risk: low to medium.** Every hazard is a pure function of scene time, so the preview and the jump are exact and
cheap; the hero is a rigid car (no rig, no animation); one course reused across three scenes. Risk is that the cut
must feel like a film cut, not a teleport glitch. **UE 5.9:** Enhanced Input (analog trigger for cut length, plus a
keyboard/mouse mapping), Common UI (menus that work with mouse and gamepad focus), spline movement, CineCamera actors
for the replay angles, post-process (film grain, letterbox, black-and-white that gains colour as you keep money
shots), Niagara (cut flash, sparks), MetaSound (splice click, music that seeks forward on each cut; seek support to be
checked), Sequencer only for the title card. **Perk tools:** Meshy or Hyper3D Rodin (via fal or direct) for the car
and set props; GPT, Grok or fal FLUX images for concept sheets, posters and title cards; PBRGen for set materials;
Claude for agent work. All need their keys and terms dates first.

### 3.2 Take Two (verb: act, then replay)

Each scene needs several roles at once: someone hits the switch, someone holds the door, someone makes the jump.
You play a 15-second take, then play the next take alongside your earlier takes, which replay as ghost actors. The
scene succeeds when every beat lands in one combined shot; the end plays all takes together as the final film.
**Theme use:** takes, and the final cut built from them. **Clever take:** you are your own cast; the director's cut is
literally every take layered into one. **Scope risk: medium.** Recording and replaying takes is easy for transforms,
hard when ghosts push physics objects (replays drift); clone-take puzzles are a known jam genre, so ambition scores
lower. Hero should be a toy figure or a ball, not a rigged human. **UE 5.9:** take recording in C++ (logic-heavy, per
`CLAUDE.md`), Niagara ghost trails, post-process, Enhanced Input. **Perk tools:** Meshy/Rodin props, image tools for
the look, PBRGen; Rokoko only if a figure needs mocap and its terms are checked.

### 3.3 Rolling! (verb: frame the shot)

You are the camera, not the hero. A scripted action scene plays out on a studio lot (a toy monster, a car chase, an
explosion chain). You fly a camera rig and keep the star moments in frame and in focus to fill a coverage meter;
miss a big moment and it is gone from the film. The end screen plays the footage from your camera as the finished
trailer. **Theme use:** you direct the photography, and your framing is the cut. **Clever take:** the player makes the
movie they are watching. **Scope risk: medium.** Set pieces must be authored and timed (content-heavy), and scoring
"good framing" must be easy to read; replaying the camera feed is cheap if the scene is a function of time.
**UE 5.9:** CineCamera with depth of field, Sequencer or time-driven set pieces, SceneCapture for a viewfinder,
post-process, Niagara for the explosions, Enhanced Input (two sticks map well to a camera). **Perk tools:** Meshy/Rodin
for the set and monster, image tools, PBRGen.

### 3.4 Cheat the Angle (verb: cut between camera angles)

A stunt ball rolls through a film studio where every set is a facade built for one camera angle. The shoulder buttons
cut between shots (wide, close, low); only the flats built for the current shot are solid. Cut mid-air to land on a
platform that exists only in the next shot. **Theme use:** editing between shots, and the film-set trick that a set
only exists for its camera. **Clever take:** the edit is your jump; the backstage reveal of flat facades and crew
lights is the visual joke. **Scope risk: medium.** Three solid-states per level triples level design work, and the
player must always see which flats are live; dimension-switch platformers exist, so the film framing carries the
novelty. **UE 5.9:** camera blends, collision profiles switched per shot, Lumen Lite, post-process, Enhanced Input.
**Perk tools:** Meshy/Rodin for props, PBRGen for flats, image tools.

### 3.5 On Cue (verb: cue the cast)

You are the director in the chair. Little actors (wind-up toy robots) stand on their marks, a script ticker scrolls
the beats, and you cue each actor at the right moment ("Action", "Jump", "Fall") so the scene matches the script.
Actors improvise when cued badly. **Theme use:** directing, and the hosts' point that we direct our AI agents too.
**Clever take:** the game mirrors how it was made (an owner directing agents), which also feeds the Glass Box dev
log. **Scope risk: high.** Many actor behaviours and animations, readable improvisation, and a rhythm-style scoring
system all at once. **UE 5.9:** StateTree for actor behaviour, Niagara, MetaSound, Common UI. **Perk tools:** Meshy or
Rodin for actors, Rokoko (terms unchecked) only if animation is needed.

### 3.6 Cutting Room Floor (verb: splice a cut feature back in)

The game is the "director's cut" of a fictional game. Film strips on the cutting-room floor each hold a cut feature
(double jump, colour, music, an enemy type, a boss). Splicing one in changes the game; some make it easier, some
harder, and before the last run you choose which ones make your cut. **Theme use:** the hosts' exact framing, cut
features restored. **Clever take:** the strips can be our own real cut list from this jam, with a one-line commentary
each, so the dev log and the game tell the same story. **Scope risk: high.** A base game that is fun on its own plus
every feature as real work; the more strips, the more risk. **UE 5.9:** depends on the base game; Common UI for the
splice screen, post-process for the colour strip. **Perk tools:** image tools for strip art, Meshy/Rodin, PBRGen.

### 3.7 Final Cut (verb: arrange clips)

A heist plays out from the clips you place on a timeline: each clip card is an action ("run", "duck", "grab",
"wait"). Press play, watch the take, re-edit when it fails. **Theme use:** editing order decides cause and effect.
**Clever take:** you are the editor, not the actor. **Scope risk: low to medium.** Small systems, but it is a
plan-then-watch puzzle, which the owner's toolkit brief rules out ("quick, replayable, skill-based, not a clever-aha
puzzle"), and watch-and-retry loops struggle on fun. **UE 5.9:** Common UI drag on a timeline (needs gamepad focus
too), a simple action runner, Sequencer-like scrubbing. **Perk tools:** image tools for the clip cards, Meshy/Rodin.

### 3.8 Stunt Double (verb: perform the stunt)

The director calls the stunt list; you perform it with a ragdoll stunt performer; the best take goes in the film.
**Theme use:** literal film-set reading. **Clever take:** weak; most entries with a film set will look like this.
**Scope risk: high.** A humanoid hero, ragdoll tuning and animation are the jam's most common sinks (the plan's cut
list already drops animated characters). **UE 5.9:** physics animation, Chaos, Unreal Animation Framework (new in 5.9,
unproven for us). **Perk tools:** Meshy/Rodin, Rokoko (terms unchecked).

## 4. Scores

### 4.1 The task's five criteria (1-5 each; paper estimates, not proof of fun)

Scope safety = 5 means smallest risk in 4 days. Pipeline fit = how well it suits what the mocks proved: UE 5.9 on the
desktop, one lead MCP caller, a Windows package built on the Legion, gamepad plus keyboard/mouse, cloud 3D props.

| # | Idea | Theme fit | Fun | Scope safety | Visual hook | Pipeline fit | Total /25 |
|---|---|---|---|---|---|---|---|
| 3.1 | Jump Cut | 5 | 4 | 4 | 4 | 5 | **22** |
| 3.3 | Rolling! | 5 | 3 | 3 | 5 | 4 | **20** |
| 3.4 | Cheat the Angle | 4 | 4 | 3 | 4 | 4 | **19** |
| 3.2 | Take Two | 4 | 4 | 3 | 3 | 4 | 18 |
| 3.7 | Final Cut | 5 | 2 | 4 | 3 | 4 | 18 |
| 3.5 | On Cue | 5 | 3 | 2 | 4 | 3 | 17 |
| 3.6 | Cutting Room Floor | 5 | 3 | 2 | 3 | 3 | 16 |
| 3.8 | Stunt Double | 3 | 3 | 2 | 3 | 2 | 13 |

Short reasons for the close calls: Jump Cut's fun is a timing-and-prediction skill that works with grey cubes,
and its time-function hazards make the build small. Rolling! has the best visual hook, but a camera-only verb risks
feeling passive. Cheat the Angle is fun and readable on paper, but triples level layout work. Take Two loses on
replay drift and a familiar genre. Final Cut is a strong theme fit with a weak loop for our brief.

### 4.2 The repo rubric for the top 3 (`scoring-rubric.md`, Rule 9's seven rows)

| Row | Jump Cut | Rolling! | Cheat the Angle |
|---|---|---|---|
| Ambition and Innovation | 4: editing as a dodge, with a time preview | 4: the player is the camera | 3: known switch mechanic, fresh skin |
| Use of Contest Theme | 5: the cut is the core verb | 5: framing is the cut | 4: cutting between shots |
| Fun Factor (paper guess) | 4: hold, read, release works in greybox | 3: may feel passive | 4: mid-air cuts are a skill |
| Gameplay | 4: cut plus money shots that pull the other way | 3: one verb, scored | 4: cut plus platforming |
| Visuals | 4: film set, cut flashes, colour returns | 5: set-piece spectacle | 4: facades and backstage reveal |
| Level Design | 4: teach, test, twist over three scenes | 3: set pieces, little player route | 4: teach by shot, then combine |
| Audio | 4: music jump-cuts with the player | 4: score follows the action | 3: music plus SFX |
| **Total /35** | **29** | **27** | **26** |
| Core verb playable in greybox within 12 h? | yes | yes (camera only; set pieces later) | yes (one room) |

Decision rule (highest total with Fun Factor and Gameplay both 3+): **Jump Cut** leads, **Rolling!** is the
runner-up. Rolling! is also the cheapest fallback: it reuses Jump Cut's scene clock, set pieces and replay, and only
swaps the verb (fly the camera instead of cutting time).

## 5. Pre-jam shortlist, checked against the theme

| Shortlist concept | Does "Director's Cut" change its repeated decision? | Verdict |
|---|---|---|
| Root Circuit | No; reclaiming roots for power has no cut, take or framing rule | cosmetic, drop |
| Living Grapple | Only as a relabel (routes as "takes") | cosmetic, drop |
| Bloom Brigade | Companions could be a "cast", but the formation decision does not change | cosmetic, drop |
| The Last Signal | Relay placement has no edit rule | cosmetic, drop |
| Overgrowth Delivery | Delivery order could be "scene order", a relabel only | cosmetic, drop |

What carries over from prep: the greybox-first rule, the build and ship pipeline, the playtest gates, the juice
recipe, and the object-not-humanoid hero advice. None of the shortlist's game content does.

## 6. Top 3, plainly

1. **Jump Cut**: hold to preview the future, let go to cut; the cut skips danger but costs film, and the shots you
   keep uncut make your final film. Plan: [`jump-cut-concept.md`](jump-cut-concept.md).
2. **Rolling!**: you are the camera in a scripted action scene; what you frame is the movie.
3. **Cheat the Angle**: cut between camera angles; only the set pieces built for the current shot are solid.

**Locked 2026-11-11 13:31 PT:** the owner confirmed Jump Cut with Fable's final change list; the locked design is [`gdd.md`](gdd.md).

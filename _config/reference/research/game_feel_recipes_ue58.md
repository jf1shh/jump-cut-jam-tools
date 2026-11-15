# Game feel and juice recipes for UE 5.8: what to build, with which nodes, and when

Research date: 2026-10-29. Method: read the four house docs first, then roughly 14 web searches and 6 page
fetches (Epic 5.8 docs, Epic Blueprint API pages, one practitioner write-up, two GDC talk summaries). One
agent, no multi-vote verification. The **Basis** column says where each row comes from: Epic doc, Epic staff
post, user report, third-party, or inference. Nothing was run in the editor, so every number is a starting
point to tune, not a measured result.

**Status: research notes only.** No gameplay, levels or art are built or implied by this note; nothing here
may be built before the contest window opens (Rule 7(h)). Rule 7(h) allows only AI tools, agent configs, MCP
settings, prompt libraries and scripts before the window. The knowledge base already treats a hit-stop
component as gray and forbidden (`_config/reference/knowledge-base.md`, open question 6), so this note treats every
Blueprint recipe below as an in-window build.

**Takeaway.** Five items give the most Fun Factor per minute: (1) hit-stop via per-actor Custom Time Dilation
with a 0.04-0.1 s restore timer, (2) one Perlin camera shake asset fired with a Scale that follows hit
strength, (3) randomized-pitch impact sounds, (4) a Niagara burst from a built-in template spawned at the hit
point, (5) a squash-and-stretch pulse on the thing that was hit or collected. Controller rumble is the sixth
and is nearly free, but it is the one most likely to silently fail on the handheld. The biggest trap is
timing: the restore timer for a hit-stop runs on world time, so a global slowdown stretches it. Use per-actor
dilation and keep the timer positive. All of this is Blueprint-only and uses engine classes that exist in 5.8
docs. Two items could not be confirmed for 5.8 and are flagged: the "Legacy" camera shake class name and
whether camera shakes slow down under global time dilation.

## 1. Hit-stop and time dilation

### Findings

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| `Set Global Time Dilation` (Gameplay Statics) takes one float; 1.0 is normal. The 5.8 page does not say if the value is clamped. | high | Epic doc | [Epic BP API](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Utilities/Time/SetGlobalTimeDilation) |
| Each actor also has Custom Time Dilation (`Set Custom Time Dilation` node); effective speed is global x custom. Hit-stop on only the target keeps the player and camera moving. | medium | user report | [Unreal Answers](https://answers.unrealengine.com/questions/364161/view.html), [practitioner](https://uhiyama-lab.com/en/notes/ue/game-feel-hit-feedback/) |
| A worked hit-stop: dummy Custom Time Dilation 0.05, global stays 1, restore via `Set Timer by Event` of 0.07 s, looping off. "UE5", minor version not stated. | medium | third-party | [uhiyama-lab](https://uhiyama-lab.com/en/notes/ue/game-feel-hit-feedback/) |
| The restore timer is NOT slowed by an actor's Custom Time Dilation, but IS slowed by global dilation and pausing. A timer time of 0 or less clears it, so keep it positive. | medium | third-party + user report | same page; [Unreal Answers](https://answers.unrealengine.com/questions/51425/view.html) |
| Global dilation cannot be set to exactly 0; use a tiny value such as 0.0001 for a full freeze. | low | user report | [Unreal Answers](https://answers.unrealengine.com/questions/857995/view.html) (snippet only) |
| Timeline components have `Set Ignore Time Dilation` (bool), so a UI or flash timeline can keep real-time speed during a global slowdown. Epic's page gives no caveats. | medium | Epic doc | [Epic BP API](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Components/Timeline/SetIgnoreTimeDilation) |
| Some effects ignore dilation (a forum report says beam emitters do). | low | user report | Unreal Answers thread, snippet only |
| Tuning source for "good" values: Vlambeer's "Sleep" is a micro-pause on a successful hit. The talk summary gives no numbers. | medium | third-party | [RPG Playground summary](https://rpgplayground.com/research-making-a-juicy-game/) |
| Starting values already in our docs: global 0.05-0.1 for 50-100 ms. The one worked example above used 0.05 for 70 ms. | medium | third-party | `ue_fast_build_assets_shipping.md` s4; uhiyama-lab |

### Recipe A: hit-stop (about 15 min)

- **Player gets:** a tiny freeze on contact that makes hits feel heavy.
- **Nodes:** on hit, `Set Custom Time Dilation` (target actor and attacker, 0.05) then `Set Timer by Event`
  (0.07 s, Looping off) whose event sets both back to 1.0. Store the old value in a variable first.
- **Feel values (starting, tune by hand):** 0.04 s for light hits, 0.07-0.1 s for heavy, 0.15 s for boss or
  finisher. Source: the single worked example above plus our docs; ranges beyond 0.07 are inference.
- **Global variant:** `Set Global Time Dilation` 0.05-0.1 for kill-cam or boss-death moments only. The
  restore timer then runs slowed, so either give it a shorter time or drive it from a Timeline with
  `Set Ignore Time Dilation` on (inference from the two facts above).
- **Risk:** a stuck dilation value if a second hit lands mid-freeze. Guard with a "hit-stopping" bool or use
  the timer handle to clear and reset. Physics under dilation can misbehave ([forum thread](https://forums.unrealengine.com/t/time-dilation-breaks-physics/360537), snippet only), so test with ragdolls/physics props.
- **Pre-window?** No (gray under 7(h)). Build in window.

## 2. Camera shake (5.8)

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Create a Blueprint from `CameraShakeBase`; choose a **Root Shake Pattern**: Perlin Noise (rumbles, near explosions), Wave Oscillator (smooth sine, e.g. boat), Sequence (plays a Camera Animation Sequence asset), Composite (layer several via Child Patterns). | high | Epic doc (labelled 5.8) | [Epic camera shakes](https://dev.epicgames.com/documentation/en-us/unreal-engine/camera-shakes-in-unreal-engine) |
| Perlin and Wave expose per-axis Amplitude/Frequency for Location, Rotation, FOV, plus Amplitude/Frequency Multipliers; Timing has Duration (0 or less = forever) and Blend In/Out. | high | Epic doc | same |
| `Single Instance` on the base restarts the shake instead of stacking copies. | high | Epic doc | same |
| `Start Camera Shake` takes Shake, Scale, Play Space (Camera Local, World, User Defined); target is a Player Controller or Camera Shake Source Component. | high | Epic doc | same |
| `Camera Shake Source` actor/component plays a shake with inner/outer radius falloff (Quadratic or Linear), with Auto Start. Good for explosions the player is near, not hit-on-player. | high | Epic doc | same |
| The 5.8 page never mentions the Legacy/Matinee shake. A "legacy" class existed as `UMatineeCameraShake` in 4.27. Whether it is now a differently named legacy class in 5.8 is not confirmed. Avoid it. | medium | Epic doc (absence) + 4.27 API | [4.27 API](https://docs.unrealengine.com/4.27/en-US/API/Plugins/GameplayCameras/index.html) |
| Worked hit shake: Perlin, Single Instance on, Duration 0.15, Blend In 0.02, Blend Out 0.08, Rotation Pitch amp 1.0 at freq 25, everything else 0; fire with Scale 0.5, Camera Local. | medium | third-party | [uhiyama-lab](https://uhiyama-lab.com/en/notes/ue/game-feel-hit-feedback/) |
| Whether a shake runs in slow motion under global time dilation is not documented. Inference: probably, since it updates per frame on world time. | low | inference | search found no source |

### Recipe B: camera shake kit (about 20 min for three assets)

- **Player gets:** weight on hits, landings and explosions.
- **Build:** three `CameraShakeBase` Blueprints, all Perlin, all Single Instance on. Small: Duration 0.15,
  pitch amp ~1, freq ~25 (the worked example). Medium: Duration 0.3, add roll and small location amp.
  Big: Duration 0.6-0.8, location + rotation + FOV, Blend Out 0.3. Medium and Big values are inference.
- **Fire:** `Get Player Controller` then `Start Camera Shake` with Scale = hit strength (0.25 to 1.5), Play
  Space Camera Local. One Blueprint function `Juice_Hit(strength)` that calls shake, hit-stop and rumble
  together keeps tuning in one place.
- **Vlambeer's point:** direction matters (kick the camera along the hit direction); and the camera should
  smooth-follow. Source gives the idea, no values ([summary](https://rpgplayground.com/research-making-a-juicy-game/)).
- **Cost/risk:** low. Risk is overdoing it: add a "Screen shake" slider in settings (also an accessibility need). Sequence shakes need a Camera Animation asset, which is more work; skip for a jam.
- **Pre-window?** No. These are gameplay assets. Only a one-page tuning table could be prepared.

## 3. Squash and stretch, easing, score pop-ups

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| "Juice it or lose it" lists: color, tweening/easing, squeeze and stretch on events, wobble on bounce, particles, screenshake, sound, screen flash. | medium | third-party (summary) | [RPG Playground](https://rpgplayground.com/research-making-a-juicy-game/) |
| Blueprint `Ease` (Kismet Math) interpolates A to B by Alpha using an easing enum plus a BlendExp (default 2.0). Enum includes Linear, Step, Sinusoidal, Ease, Expo, Circular In/Out/InOut. No Elastic or Back. | medium | Epic doc (4.26 page + 5.x enum page; snippets only) | [Ease](https://docs.unrealengine.com/4.26/en-US/API/Runtime/Engine/Kismet/UKismetMathLibrary/Ease/index.html), [EEasingFunc](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/EEasingFunc__Type) |
| Missing easings (Elastic, Back/overshoot) are a known gap; a float curve asset in a Timeline can draw any shape. | medium | user report | [forum request](https://forums.unrealengine.com/t/feature-request-implement-complete-set-of-easing-functions/474519) |

### Recipe C: squash-and-stretch pulse (about 15 min)

- **Player gets:** objects visibly react to being hit, collected, or landed on.
- **Nodes:** Timeline (one float track, drawn as 0 to 1 with a bump) driving `Set Actor Scale 3D` or
  `Set Relative Scale 3D` on the mesh: scale = Lerp(1, 1.3, track) on XY and Lerp(1, 0.75, track) on Z for
  squash; invert for stretch. Length 0.15-0.25 s. Values are inference, standard practice.
- **Use a Timeline over `Ease`** when you want overshoot: draw a curve that goes past 1 and settles.
  Use `Ease` (Expo Out or Sinusoidal InOut) for UI slides, since it needs no asset.
- **Time dilation interaction:** if the timeline plays during a hit-stop, it freezes with the actor. Fine
  for the hit target; for UI use `Set Ignore Time Dilation`.
- **Pre-window?** No (it is a gameplay Blueprint). A reusable Blueprint Function Library is gray under 7(h).

### Recipe D: score pop-ups and floating text (about 20 min)

- **Player gets:** numbers that confirm the hit and reward big hits.
- **Nodes (inference, standard UE):** a small Widget Blueprint with a text block and a fade/rise
  animation, shown through a Widget Component on a spawned actor (World space, Screen), or `Add to
  Viewport` at a projected position. Destroy after 0.8 s. Scale font with damage. Use the Ease or a Timeline
  for a pop-in (scale 0 to 1.2 to 1).
- **Risk:** many simultaneous widgets cost frame time; cap at ~20 (inference).
- **Pre-window?** No.

## 4. Niagara bursts

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| `Spawn System at Location` (Niagara) takes system, location, rotation, scale, Auto Destroy, Auto Activate, Pooling Method. | high | Epic doc | [Epic BP API](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Niagara/SpawnSystematLocation) |
| For a one-shot burst: remove the Spawn Rate module, add Spawn Burst Instantaneous; a non-looping system cleans itself up. | medium | third-party | [uhiyama-lab Niagara](https://uhiyama-lab.com/en/notes/ue/niagara-vfx-basics/) |
| Known bug: a Global-Space Spawn Burst Instantaneous can fire at the component's old position if reactivated after a move. Spawn a fresh system per hit instead of reusing a moving component. | low | Epic bug tracker (snippet) | [UE-355672](https://issues.unrealengine.com/issue/UE-355672) |
| Exact built-in template names (e.g. "Directional Burst") were NOT confirmed from any doc. Check the New Niagara System dialog in the 5.8 editor. | n/a | gap | the Epic Niagara quick start page loaded empty |

### Recipe E: hit burst (about 20-30 min per effect)

- **Player gets:** sparks, dust or confetti where contact happens; the largest visual jump for the least work.
- **Build:** New Niagara System from a built-in burst-style template, set color to the game palette, short
  lifetime (0.2-0.5 s, inference), 10-40 particles; `Spawn System at Location` at the impact point with Auto
  Destroy on. Make three: hit, kill, pickup. Add a lit flash sprite for 1-2 frames.
- **Cost/risk:** low, but Niagara cost climbs with sprite count and translucency; the handheld GPU is the
  limit, so keep under ~100 live particles per burst (inference).
- **Pre-window?** No. VFX are art (Rule 7(h)).

## 5. Impact sounds (MetaSound)

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| The MetaSound Wave Player has a Pitch Shift input in semitones. A `Random Float` node feeding it gives per-trigger pitch variation. | medium | Epic doc + third-party | [Epic node reference](https://dev.epicgames.com/documentation/unreal-engine/metasound-function-nodes-reference-guide-in-unreal-engine), [itch.io devlog](https://itch.io/devlog/755763/metasounds-and-how-they-can-be-used-in-unreal.amp) |
| A game-audio guide suggests about +-2 semitones pitch and +-2 dB volume; if you can hear the shift as a shift, it is too much. The devlog used -1 to +10 for UI buttons, which is wide. | low | third-party | search result summary, original not opened |
| `Random Get` nodes can avoid repeating the last pick, so a bank of 3-5 hits does not repeat. | medium | Epic doc (snippet) | MetaSound reference above |
| MetaSound Templates are Experimental; the SFX Generator is already our primary SFX source. | high | Epic doc via our KB | `ue_fast_build_assets_shipping.md`, KB l.360 |

### Recipe F: hit sound (about 15 min once, then reuse)

- **Player gets:** hits that never sound identical.
- **Build:** one MetaSound Source with a Trigger input, `Random Float` (-1.5 to +1.5 semitones, inference
  from the +-2 guidance) into Wave Player Pitch Shift, another Random Float on Volume (0.85-1.0), and
  `Random Get` across 3-5 variants. Add an intensity float input so heavy hits pitch down and play louder.
  Play with `Spawn Sound 2D` or at location.
- **Layer rule:** every big hit gets three layers: a low thump, a mid crack, a high detail tick (inference,
  standard practice; Vlambeer's "more bass" supports the low layer).
- **Pre-window?** No (audio is content). A written parameter list is fine.

## 6. Screen flash and post-process pulse

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Screen flash is on the "Juice it or lose it" list. No 5.8 doc was found for a specific node recipe. | medium | third-party | [RPG Playground](https://rpgplayground.com/research-making-a-juicy-game/) |
| No source checked covered the post-process route, so the nodes below are standard-UE inference to be verified. | n/a | gap | none |

### Recipe G: flash and pulse (about 15 min)

- **Player gets:** a white or red flash on big hits and a brief vignette or chromatic pulse on damage.
- **Nodes (inference):** simplest and cheapest is a full-screen white Image in the HUD widget with opacity
  animated 0.4 to 0 over 0.1 s (no material work). For a post-process pulse: a PostProcessVolume (Infinite
  Extent) with a Material Parameter Collection scalar read by a post-process material; set it via `Set
  Scalar Parameter Value` and drive it with a Timeline.
- **Risk:** flashing is a photosensitivity problem. Keep it brief, small area at low contrast, and add an
  option to turn it off (inference, accessibility practice).
- **Pre-window?** No.

## 7. Controller rumble and handheld play

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| `Force Feedback Effect` asset: channels, each picks any of Left Large/Left Small/Right Large/Right Small motors, with a curve of intensity over time; values above 0 vibrate. Duration comes from the last key. | high | Epic doc (labelled 5.8) | [Epic force feedback](https://dev.epicgames.com/documentation/en-us/unreal-engine/force-feedback-in-unreal-engine) |
| Play with `Client Play Force Feedback` on the local Player Controller (Looping and Tag are node pins; a second effect with the same Tag stops the first). `Spawn Force Feedback at Location/Attached` adds distance falloff. | high | Epic doc | same |
| Per Device Overrides let you set different feedback per platform. DualSense trigger and audio-haptic options exist; audio-based vibration is Experimental and DualSense-only. The page does not cover Windows, Steam Deck or handhelds. | high | Epic doc | same |
| `Play Dynamic Force Feedback` is a separate path with no asset; it must be updated procedurally. | medium | user report | [Unreal Answers](https://answers.unrealengine.com/questions/468320/view.html) |
| User reports of force feedback working in the editor but not in packaged builds, and of Steam Input dropping rumble until it is forced off for the game. Anecdotes about other titles. | low | user report | [Unreal Answers](https://answers.unrealengine.com/questions/766460/view.html), [Steam thread](https://steamcommunity.com/app/353370/discussions/0/1644295067080841754) |
| Legion Go S on Windows: no source found about UE rumble. The original Legion Go has reports of controllers appearing as DInput not XInput. These are about the first model. | low | user report | [Lenovo forum](https://gaming.lenovo.com/legion-go/post/x-input-connection-not-working-with-legion-go-controllers-TRMaSlZ4cJ7SQJ1) |

### Recipe H: rumble (about 10 min)

- **Build:** three Force Feedback Effect assets (tap: one key 0.6 over 0.1 s on Left Small + Right Small;
  thud: 1.0 on Left Large decaying over 0.25 s; rumble: 0.5 over 0.8 s). Call `Client Play Force Feedback`
  from the same `Juice_Hit(strength)` function. Give a Tag so repeated hits replace rather than stack.
  Values are inference.
- **Handheld notes:** (1) test the packaged build ON the Legion Go S, with Steam Input on and off if launched
  from Steam, and with the built-in pad versus an external Xbox pad. (2) Rumble has no on-screen proof, so
  never rely on it alone for feedback. (3) Add a vibration on/off setting. (4) The 1080p-or-lower handheld
  screen favors big hit flashes and bold shapes over fine detail (inference). (5) Controller menus:
  every button must be reachable with a pad, and a pad-first prompt set is mandatory.
- **Pre-window?** No, but the packaged-build rumble check can be done pre-window with a throwaway test
  project containing no art, if the owner allows it (see Next checks).

## Ranked list: five highest impact per minute for a 4-day solo jam

Ranked by my judgment from the evidence above; no source ranks these for jams.

| Rank | Item | Time | Why | Basis |
|---|---|---|---|---|
| 1 | Hit-stop (per-actor dilation, 0.04-0.1 s) | 15 min | Cheapest weight; Vlambeer's "Sleep" is on its core list; no art needed | third-party + inference |
| 2 | One `Juice_Hit(strength)` function that fires shake, stop, sound and rumble together | 30 min | Every later hit gets all four for free; one place to tune | inference |
| 3 | Randomized, layered impact SFX in MetaSound | 15 min | Audio is a full criterion and the cheapest to raise (our KB) | Epic doc + inference |
| 4 | Niagara burst at impact | 25 min | Biggest visual change for the time; Visuals criterion | inference |
| 5 | Squash/stretch pulse on hit target and pickups | 15 min | Makes every object feel alive; named in "Juice it or lose it" | third-party |

Add a settings toggle for shake, flash and vibration (10 min). It costs little and protects against
accessibility complaints in a game judged on feel.

## What this means for our pipeline

- Put all juice in one `Juice_Hit(strength, direction)` Blueprint function on day 1 of the window, once the
  core verb exists. Tune strength only at the call sites. The rest of the jam work stays unblocked.
- Do not write any of this before 11 Nov 9 PM PT. A pre-window deliverable that is safe: a one-page tuning
  sheet (this file) and, if wanted, a prompt for the MCP agent to build the function.
- Per `ai_asset_to_ue_handoff.md` the MetaSound SFX Generator is the audio source; add the random pitch
  graph on top of it.
- Order of work: hit-stop, shake, SFX, burst, squash, rumble, flash, pop-ups.

## Gaps

- No 5.8 page found for post-process pulse, floating text or squash-and-stretch; those recipes are standard
  practice, not sourced.
- Exact Niagara template names in 5.8 are unconfirmed (the Epic quick start page fetched empty).
- "Art of Screenshake" and "Juice it or lose it" were read only as secondhand summaries; no talk values
  (pixels, frames, durations) were found, so no numeric value here comes from the talks.
- Whether camera shakes slow under global time dilation is undocumented.
- The 5.8 name of the Legacy camera shake class was not found.
- Nothing on Legion Go S rumble under UE on Windows.
- The Gameplay Cameras 5.8 changes were in the truncated release notes (see `ue_fast_build_assets_shipping.md`
  line 205) and are not covered here.

## Next checks before Nov 11

1. Ask in the Epic forum or Discord whether a generic hit-stop component counts as "scripts" under 7(h);
   until answered, build in window (KB open question 6).
2. In a throwaway empty UE 5.8 project (no art, owner OK needed): confirm that `Start Camera Shake` slows
   under global dilation, and that the restore timer behaves as stated in section 1.
3. Same throwaway project, packaged for Windows: test rumble on the Legion Go S with and without Steam Input.
4. Open the 5.8 New Niagara System dialog and list the burst template names.
5. Write the `Juice_Hit` spec (inputs, defaults) as text so building it takes minutes.

## Caveats

- The cited Epic camera shake and force feedback pages are labelled 5.8; the Blueprint API pages for time
  dilation, Timeline and Niagara spawn were fetched from the current docs and I did not confirm their
  version label. The Ease page was 4.26.
- The worked hit-stop and shake numbers come from one third-party blog (UE5, minor version not given).
- Search results that were snippets only are marked; their claims should be tested.
- "Fun" is not measured by any source. Impact-per-minute ranking is judgment.

---
tier: community
source: _config/reference/research/game_feel_recipes_ue58.md, _config/reference/research/fast_ui_and_input_ue58.md, _config/reference/research/audio_and_music_fast_production.md, _config/reference/knowledge-base.md (juice and shell checklists)
updated: 2026-11-11
---

# Jam polish pass: what to add in which hour, cheapest first

The juice/shell/SFX checklist in `_config/reference/knowledge-base.md` ("Juice and shell checklists") turned into an
ordered pass. Each step names the existing hour in `stages/00_prep/references/jam-execution-plan.md` it goes into, so no new slots
are added. Cheapest first: if time runs out, the later steps are the ones that drop.

**Trust level:** the node names and values come from the in-repo research notes (UE 5.8 docs and practitioner
posts, 2026-10-29). None has been built or checked in UE 5.9 here, so this note is `community` tier. Check a
node name with `mx.py` or the editor's node search before relying on it. Pre-window (Rule 7(h)) none of this
may be built; it is a plan only.

## The pass

| # | Step | Hour (jam-execution-plan) | Time | Done when |
|---|---|---|---|---|
| 1 | Hit-stop on the core verb's impact | Thu 09:00 "Juice on the core verb" | 15 min | A hit visibly freezes 0.04-0.1 s |
| 2 | Camera shake kit (small, medium, big) | Thu 09:00 | 20 min | Hit, land and big event each shake differently |
| 3 | `Juice_Hit(strength)`: one function firing stop + shake + sound + rumble | Thu 09:00 | 30 min | Every hit calls only this |
| 4 | Stub SFX on every player action (one sound each, even placeholder) | Thu 09:00 "sound stub" | 20 min | No silent action |
| 5 | End screen + Restart + Quit (win and lose) | Fri 11:00 "win and lose states" | 30 min | Both ends reachable; Restart and Quit work with the gamepad |
| 6 | Randomized, layered impact SFX (MetaSound) | Sat 11:00 "Audio pass" | 15 min, then reuse | Two hits in a row never sound the same |
| 7 | Music: one track per state (menu, play, end), looped | Fri 18:00 GEN + Sat 11:00 import | 20 min import | Each state has its track; loop has no click |
| 8 | Title (game name + theme visible) and pause (resume/restart/settings/quit) | Sat 13:00 "UI: title, pause, settings, end screen" | 45 min | Both reachable with the gamepad on the Legion |
| 9 | Settings: volume sliders (master, music, SFX) + shake/flash/rumble toggle | Sat 13:00 | 30 min | Sliders change volume live; toggle turns shake off |
| 10 | Niagara burst at impact + squash/stretch pulse on targets | Sat 14:00 "Juice pass" | 25 + 15 min | Impact reads in a still frame |
| 11 | One post-process volume (grade, vignette, bloom) | Sat 09:00 "Lighting pass" | 20 min | Before/after frame looks like one palette |
| 12 | Controller rumble (Force Feedback) | Sat 14:00 | 10 min | Felt on the Legion on a hit |

**Never cut** (from the plan's cut list): the end screen, the Quit path, restart, theme on the title and in
the first minute, juice on the core verb, a sound for every action. Steps 1-5 and 8 cover those; do them even
if everything after is dropped.

## How-tos (from the repo research notes)

1. **Hit-stop** (`game_feel_recipes_ue58.md` Recipe A). On hit: `Set Custom Time Dilation` on the target and
   attacker to 0.05, then `Set Timer by Event` 0.07 s (looping off) whose event sets both back to 1.0. Light
   hits 0.04 s, heavy 0.07-0.1 s. Guard with a "hit-stopping" bool so a second hit mid-freeze does not leave
   the dilation stuck. Global `Set Global Time Dilation` only for big moments; it slows the restore timer too.
   Physics under dilation can misbehave: test with physics props.
2. **Camera shake** (Recipe B). Three Blueprints from `CameraShakeBase`, Root Shake Pattern Perlin Noise,
   Single Instance on. Small: Duration 0.15, Blend In 0.02, Blend Out 0.08, rotation pitch amplitude 1 at
   frequency 25. Medium 0.3 s with a little roll; big 0.6-0.8 s with location and FOV (these two are
   guesses to tune). Fire with `Get Player Controller` then `Start Camera Shake`, Scale 0.25-1.5, Play Space
   Camera Local. Avoid any legacy/Matinee shake class.
3. **`Juice_Hit(strength)`** (ranked list, rank 2). One Blueprint function that calls steps 1, 2, 6 and 12
   with `strength` scaling each, so tuning lives in one place.
4. **Stub SFX.** Import WAVs (the import itself took 4 s here, `jam-import-and-materials.md`), then play with
   `Spawn Sound 2D` or at location. Kenney Impact/Interface Sounds and RPG Audio are staged CC0 packs
   (`stages/02_build/output/sourced-assets-staged.csv`); log any you import with `scripts/sourced_assets.py add` in the same
   minute (`jam-sourced-assets-ledger.md`). Epic's SFX Generator MetaSound (Tech Audio Tools Content plugin)
   needs no GPU.
5. **End screen + restart** (`fast_ui_and_input_ue58.md` section 2). `EndGame(bWon)` on the GameMode: create
   `WBP_EndScreen`, set text from `bWon`, `Add to Viewport`, `Set Input Mode UI Only` with focus on Restart,
   show cursor, `Set Game Paused` true. Restart: unpause, `Remove from Parent`, `Set Input Mode Game Only`,
   hide cursor, then `Open Level` with the current level name. Every place that sets UI Only needs a matching
   undo. Make the final line readable on the lightest frame (`jam-hud-readable-text.md`). A Shipping build has
   no console, so Quit must be a button (`jam-packaging-windows.md`).
6. **Layered SFX** (Recipe F). One MetaSound Source: Trigger input, `Random Float` -1.5..+1.5 semitones into
   Wave Player pitch shift, `Random Float` 0.85-1.0 on volume, `Random Get` across 3-5 variants, an intensity
   input so heavy hits pitch down and play louder. Big hits get three layers: low thump, mid crack, high tick.
7. **Music.** Use MetaSound Sources, not Sound Cues; the Wave Player node handles loop points
   (`audio_and_music_fast_production.md` summary 4). Generated tracks are whole songs, not loops: trim and
   crossfade the loop by hand (summary 3). About 110-120 s per generated track (summary 6).
8. **Title and pause** (`fast_ui_and_input_ue58.md` section 2). The boot map is the menu map: create
   `WBP_MainMenu`, `Add to Viewport`, `Set Input Mode UI Only` with focus on Play, show cursor. Pause and
   Restart Input Actions need `trigger_when_paused`. Gamepad focus fails if buttons are not focusable, nothing
   has initial focus, or the mode is Game Only; delaying focus one tick helps. Build widgets in Python or C++,
   not by binding over MCP (`jam-agent-lint-rules.md`, widget binding).
9. **Volume sliders.** No recipe in the repo yet: the research notes name a Sound Mix bus but give no slider
   nodes. UNVERIFIED lead: one Sound Class per bus (Master, Music, SFX) and a Sound Mix with class overrides
   that the slider sets. Check in the editor before relying on it. The shake/flash/rumble toggle is a bool that
   `Juice_Hit` reads.
10. **Niagara burst** (Recipe E; MCP names in `jam-cheatsheet-niagara.md`, untested in use). Start from a
    template system with `CreateNiagaraSystem`. Never print the whole Niagara describe: it can cost about
    250,000 tokens (`jam-mcp-forum-traps.md`). Squash/stretch (Recipe C): a short scale pulse on hit.
11. **Post-process.** One unbound post-process volume: grading, vignette, bloom (knowledge-base checklist).
    Exposure first (`ue-lighting-exposure.md`).
12. **Rumble** (Recipe H). A Force Feedback effect played from `Juice_Hit`; check it on the Legion.

## Before each gate build

Play 60 s with the gamepad and tick: every action has a sound; a hit freezes and shakes; title shows the
theme; pause, restart and quit work; the end screen is readable. `visual_playtest.py` samples the end screen
and the restart too (`jam-visual-playtest-motion.md`).

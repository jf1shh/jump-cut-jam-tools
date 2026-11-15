# External strategies: reviewed against the plan (2026-10-29)

Reviews `_config/reference/research/external-strategies/{chatgpt,claude,gemini,grok}.md` against the current
plan (`AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `RULES.md`, `stages/00_prep/references/win-plan.md`,
`_config/reference/knowledge-base.md`) and the research docs already landed. Seven items below are adopted;
everything else in those four docs either duplicates existing research/decisions or is rejected
(see the end of this file).

## Adopted

1. **Data-driven room builder.** Agents write each room as a structured spec — verb, obstacle
   type, timer, door color — and a script spawns the geometry from it, rather than hand-building
   each room in the editor. Allowed under Rule 7(h) as pre-jam tooling (no gameplay/levels/art
   itself, just a generator). Makes a "two-state world toggle" mechanic (independently suggested
   in two of the four docs) cheap to build instead of doubling room-building work: build N rooms
   once, generate both states from the same spec.
   Source: `external-strategies/claude.md` §5.

2. **Automated soft-lock check.** A script that verifies the player can reach the exit from every
   spawn/checkpoint in a level, run as part of the existing QA harness (which already does
   screenshot + FPS capture per `stages/00_prep/references/win-plan.md`). Closes a concrete gap: the harness checks
   performance, not reachability.
   Source: `external-strategies/claude.md` §5.

3. **Criterion score anchors.** A short reference table defining what a 3, 4, and 5 look like for
   each of the seven scoring criteria, as our own working calibration (not Epic's — nothing
   official defines this). Two of the four docs sketched anchors independently with different
   calibrations; worth reconciling into one table so judging-criteria tradeoffs during crunch are
   made against a fixed bar instead of improvised each time.
   Sources: `external-strategies/chatgpt.md`, `external-strategies/claude.md`.

4. **Triplanar / world-aligned master materials for AI meshes.** A specific material technique to
   hide UV seams and topology artifacts on AI-generated meshes (as opposed to fixing the mesh
   itself). `_config/reference/research/ai_asset_to_ue_handoff.md` covers import/rigging/retargeting but not
   this visual fallback — add it there as a technique, not a new pipeline step.
   Source: `external-strategies/gemini.md` risk #5.

5. **Legion Go S performance budget settings.** Concrete `DefaultEngine.ini`-level settings for
   the packaged build: Forward Shading (not deferred), dynamic Lumen/VSM disabled, texture cap at
   2048×2048, a 16-concurrent-audio-channel limit, precompiled PSO caches. `stages/00_prep/references/win-plan.md`
   already names "budget draw calls" as a goal but has no concrete settings — these are the
   numbers to try first on the Legion Go S build.
   Source: `external-strategies/gemini.md` risks #2/#8/#9, §11.

6. **Audio loudness target.** Normalize generated music to roughly −16 LUFS before mixing under
   SFX and dialogue, as a starting mix target rather than tuning by ear from nothing.
   Source: `external-strategies/claude.md` §5.

7. **Open gap: no speech/narrator audio path.** The asset pipeline currently covers image → 3D →
   video/upscale and music, but nothing for spoken lines (narrator, announcer, barks). Flagging
   this as a known gap, not committing to build it — only worth closing if a chosen mechanic
   actually needs a voice.
   Source: `external-strategies/claude.md` §4 (flagged there as a guess, not a strong recommendation).

## Rejected / do not follow

- **"Develop exclusively on a native Windows 11 host during the jam."** Contradicts the
  already-made decision (`AGENTS.md`, `stages/00_prep/references/win-plan.md`): develop on CachyOS with the Linux UE
  5.8 editor + Unreal MCP + local Nexus pipeline, package Windows builds via the Legion Go S.
  Source: `external-strategies/gemini.md` risk #1. Do not follow.

- **"Drop Best Overall as the target; aim only at Solo Driver + Glass Box."** Not factually wrong,
  but a genuine strategic disagreement with `AGENTS.md`'s stated target (top 3 Best Overall,
  Unreal Engine, plus Glass Box). Left as an open question for the project owner, not adopted or
  rejected here — changing the target changes what the whole plan optimizes for.
  Source: `external-strategies/grok.md`.

- No reviewed doc assumes UEFN, a team instead of solo, or that sourced/AI-generated assets score
  points under Rule 15(c) (they don't — see `RULES.md`). All four correctly track the solo/UE5.8
  decision already made.

## Already covered — no action

Ending-first design, chapter/level select, blind-playtest instrumentation, the juice/game-feel
checklist (hit-stop, camera shake, squash/stretch), first-60-seconds structure, Glass Box dev-log
architecture, mock-jam rehearsal practice, scope-cut discipline ("ambition = depth not breadth"):
all already landed in `stages/00_prep/references/win-plan.md` or in `_config/reference/research/game_feel_recipes_ue58.md`,
`first_two_minutes_level_design.md`, `submission_page_and_video.md`. The five-archetype mechanic
tables across all four external docs substantially overlap
`_config/reference/research/mechanics_and_genre_ideas.md`'s genre analysis — no new research needed there.

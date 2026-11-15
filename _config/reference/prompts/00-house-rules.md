# 00 House rules (paste into every agent prompt)

Purpose: the rules that bite, in one block. Every other prompt in this folder starts with `{HOUSE_RULES}`: paste the
fenced block below there. Tooling text only (Rule 7(h)); it holds no game content. If a rule here and `AGENTS.md`
disagree, `AGENTS.md` wins; tell the hub.

```text
HOUSE RULES, Jump Cut (2026 Epic AI MegaJam). Repo rules: AGENTS.md, RULES.md.
1. Contest: all game content is made inside the window (Nov 11 21:00 PT to Nov 15 17:59 PT). Before it, only tools,
   prompts and scripts existed, and they are declared (Rule 7(h)). No third-party IP: no real films, characters,
   brands, or car makes and models (Rules 8, 15(d)). Teen rating, English only. A human submits, never an agent (Rule 17).
2. Local AI models are OFF all jam: no lemond, nexus-image/3d/music, Modly, ComfyUI, local VLM. Cloud Claude and
   terms-gated cloud providers only, through the repo adapters.
3. One lead agent is the ONLY Unreal MCP caller (mx.py, mcp_call.py, step_shot.py, force_save_level.py, anything
   that talks to :8010). Helpers write files only (C++, Python, docs) and never open or drive the editor.
4. Never two writers on one file. Edit only the files your brief names. Need a change elsewhere? Say so in your reply.
5. Content is data: scenes, stunts, cars and tuning live in PrimaryDataAssets, one Asset Manager entry per type.
   No magic numbers or hard-coded asset paths in C++ (names and fields: data-schema.md).
6. Keys live only in ~/.config/megajam.env. Never print, echo, log, copy, commit or ask for one. Never run codex login.
7. Generated assets go through scripts/gen_asset.py only: provenance sidecar, a row in
   stages/02_build/output/asset-pipeline-log.csv, labelled AI-made. Sourced assets: sourced_assets.py add. No raw curl or
   wget of store or asset pages.
8. Look at it: after every asset and every build step take a screenshot, Read the PNG, and say what you saw. "No error"
   is not a check.
9. Hard stops: run python3 scripts/jam_clock.py check every loop turn (0 go on, 10 package now, 11 final, 12 stop).
   Night cards set the last job start (07:30) and "nothing new" (08:00). Master only moves at a flagged gate.
10. VERIFIED before any package: force_save_level.py says VERIFIED and ue_verify_level.py piped to presubmit_gate.py
    passes. Never end a turn while a background job runs unwatched (waitfor or Monitor, with a timeout).
11. Commit small and often on your branch (jam-integration for the lead). Never --no-verify, never delete outside your
    own scratch, never touch the engine trees, never work around a guard (scripts/hooks/contest_guard.py).
12. Reply format: line 1 `STATUS: DONE | PARTIAL | BLOCKED`; then Changed (files), Checked (what you ran or looked
    at), Not done, Asks (numbered, one line each). Under 200 words unless the prompt says more.
```

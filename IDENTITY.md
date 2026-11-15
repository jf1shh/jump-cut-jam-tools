# MegaJam — Layer 0 (where am I?)

> Solo entry to the 2026 Epic AI MegaJam (Unreal Engine 5.9 Preview, 5.8.4 fallback, Windows package, Glass Box dev log). Pre-jam this repo holds only tools, plans and research; no gameplay, levels or art before 2026-11-12 00:00 ET (Rule 7(h)).

Rules live in `AGENTS.md` (project facts, decisions, agent rules, jam-week autonomy) and `CLAUDE.md`
(naming prefixes, Blueprint vs C++). Read those; this file only maps. It restates nothing from them.
Full ICM (5 layers) since 2026-11-11 by owner decision: every document lives in `stages/` or `_config/`.

## Workspace map

```
AGENTS.md  CLAUDE.md  RULES.md  PLAN.md   # root on purpose: tools load them by name
IDENTITY.md        # Layer 0: this map
CONTEXT.md         # Layer 1: routing table, session start, stage list
_config/           # Layer 3 shared
  CANON.md         #   searchable index of every doc and data file; check first
  _index.md        #   what is in _config/
  conventions.md glossary.md voice.md article-template.md   # short re-exports and terms
  reference/       #   canon/ engine-reference/ research/ templates/ prompts/ patches/
                   #   knowledge-base.md ai-providers.md NOTICE.txt
stages/            # Layer 2 contracts; each has CONTEXT.md, references/, output/
  00_prep/         #   pre-jam plans, mock jams, audits, drills, readiness
  01_concept/      #   theme to concept pick and GDD
  02_build/        #   grey box to gate builds: assets, layout, look, rig, pipeline logs
  03_playtest/     #   QA, agent playtest, judge pass, QA logs and screenshots
  04_ship/         #   package, Legion, capture, jam clock, recovery, Diversion, itch
  05_devlog/       #   Glass Box dev log entries, builds, evidence, decisions
scripts/  tests/  config/  Config/  templates/   # code and config; scripts/hooks/contest_guard.py runs before every Bash command
.claude/agents/  .github/workflows/              # Unreal specialist subagents; CI
graft/  work/      # git-ignored: code-graph cache; generated test output
```

## Related

- Build box: Legion Go S (Windows 11), `ssh <device-host>`. Local asset tools: Nexus.
- Hub notes: `~/Projects/workflow-tools/WORKSPACE.md`.
- The UE project is `~/Projects/megajam-game` (Diversion); it gets its own Layer 0/1 at creation (`AGENTS.md`).

## Rules

- Contest facts, licensed-model limits, one-MCP-caller, GPU rule: `AGENTS.md`. Naming: `CLAUDE.md`. Rule numbers: `RULES.md`.
- Nothing from UC2, UT2004, uc2-pc or UTLegacy goes in this repo (`AGENTS.md`).
- Every new document goes into its ICM stage folder (`stages/NN_*/references` or `output/`) or `_config/`; add its row to `_config/CANON.md`. No new top-level doc folders.

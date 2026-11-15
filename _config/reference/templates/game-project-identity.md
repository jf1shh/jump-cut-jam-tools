# <GAME NAME> — Layer 0 (where am I?)

> Template for `~/Projects/megajam-game/IDENTITY.md`. Copy it there at jam start and fill the blanks.
> Rules for the whole jam live in the repo `~/Projects/megajam` (`AGENTS.md`, `CLAUDE.md`); this file only maps the UE project.

Unreal Engine 5.9 Preview (5.8.4 fallback) content project for the 2026 Epic AI MegaJam. Theme: <THEME>. Concept: <ONE LINE>.

## Map

```
IDENTITY.md      # this file
CONTEXT.md       # Layer 1: routing and session start
<Name>.uproject  # project file
Content/         # Unreal's own folder: assets, levels (L_), Blueprints (BP_)
Source/          # Unreal's own folder, only if C++ is used
Config/          # Unreal's own folder: DefaultGame.ini, DefaultEngine.ini
.mcp.json        # Unreal MCP, port 8010
```

Do not move `Content/`, `Source/` or `Config/`. Naming prefixes: `~/Projects/megajam/CLAUDE.md`.

## Rules

- One lead agent is the only Unreal MCP caller. One GPU workload at a time.
- Original art and audio, licensed models only, no third-party IP (see `~/Projects/megajam/AGENTS.md`).
- Docs for the jam (plans, findings, dev log) stay in `~/Projects/megajam/stages/`, not in this folder.

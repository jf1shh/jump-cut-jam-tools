---
tier: tested
source: stages/00_prep/references/jam-day-runbook.md
updated: 2026-11-10
---

# Unreal MCP: port and health check (tested)

Tested on 5.8.4 except the 5.9 Tip; re-test on 5.9 before relying on it.

Only items we ran in the 2026-11-04 dress rehearsal. Forum, webinar and untested items are in `jam-mcp-forum-reports`.

## Tip: UE 5.9 (2026-11-10)
- **Why:** on 5.9 the MCP port came up after about 195 s, the old ini section name logs a deprecation warning (use `[/Script/ModelContextProtocol.ModelContextProtocolSettings]`), and `describe_toolset` is gone. Observed.
- **How to check:** see `jam-ue59-upgrade`. The 8010 notes below are 5.8.4 results.

## Tip: the editor must serve MCP on port 8010, not 8000
- **Why:** the Nexus backend already holds port 8000 on this box.
- **How to check:** launch with `-ModelContextProtocolStartServer -ModelContextProtocolPort=8010`, then
  `ss -ltnp | grep :8010` shows the editor. `.mcp.json` must point at `http://127.0.0.1:8010/mcp`.

## Tip: a 405 from the endpoint means the server is up
- **Why:** MCP comes up only after the editor has fully loaded (map and shaders), which can take minutes.
- **How to check:** `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8010/mcp` prints `405`.

## Tip: our rehearsal project worked with three plugins
- **Why:** it listed only `ModelContextProtocol`, `AllToolsets` and `ModelingToolsEditorMode`, yet listed about 50 toolsets and spawned an actor.
- **How to check:** Edit > Plugins in the jam project; record the final list (see the forum note about Editor Toolsets).

## Tip: never wait on port 8010 without a timeout; relaunch only when it is free
- **Why:** a relaunched editor cannot bind 8010 while the old one (SIGTERM'd, stuck in a modal) still holds it. Mock 12 waited 3 h with no timeout while `state.json` said `working` (`mock-jam-findings-12.md:37,54,98`).
- **How to check:** `ss -ltn | grep 8010` must be empty before a relaunch. `kill -9` a stuck old editor first. Every wait has a timeout; `launch-editor.sh` exits 9 if it sees "HttpListener unable to bind".

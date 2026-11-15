---
tier: epic
source: _config/reference/knowledge-base.md
updated: 2026-11-06
---

# Unreal MCP: forum, webinar and not-yet-run items

From Epic forum threads and an Epic webinar as summarised in `_config/reference/knowledge-base.md`. Items marked UNTESTED were not run by us. Do not claim any of these works until tested.

## Tip: keep "Auto Start Server" off (UNTESTED)
- **Why:** the MCP plugin is an editor module, so a cook also loads it. With auto start on, a cook tries to bind
  the same port, logs `LogHttpListener: Error: unable to bind`, and exits 1 even though it worked
  (Epic forum topic 2735398, UE 5.8.0, no Epic reply).
- **How to check:** run one cook while the editor holds 8010 and read `echo $?` right after.

## Tip: know which MCP log errors are normal (forum reports)
| Log line | Verdict |
|---|---|
| `Call to unknown method "server/discover"` | Normal. Claude Code probes it on every connect (topic 2841847, 5.8.3). |
| `Unknown session id ... client should reinitialize` | Normal after an editor restart. |
| `Invalid MCP server URL path` | Real. The URL must end in `/mcp`. |
| `unable to bind` during a cook | Real. See auto start above. |
- **How to check:** match the line against this table before treating it as a failure.

## Tip: after an editor restart, test the reconnect before relying on it (UNTESTED)
- **Why:** forum reports disagree on whether Claude Code reconnects without a manual `/mcp`.
- **How to check:** kill the editor, relaunch, wait for 405, make one MCP call from the same session.

## Tip: check for the Editor Toolsets plugin (Epic webinar claim)
- **Why:** the speaker says that without it the agent "connects but can't do anything". The setup video names Terminal instead.
- **How to check:** Edit > Plugins in the jam project; enable Editor Toolsets if it is off.

## Tip: prompt habits for the editor agent (webinar notes)
- **Why:** exact names and small tasks avoid loops.
- **How to check:** exact asset names, one task per prompt, name the class (`BP_ThirdPersonCharacter`), ask for the plan first, save after batches, add `print` lines in generated code.

## Tip: turn on verbose MCP logging when it misbehaves (Epic docs/webinar notes, UNTESTED)
- **Why:** the `LogModelContextProtocol` category shows what the server saw.
- **How to check:** run `Log LogModelContextProtocol Verbose` in the editor console, then read the Output Log.

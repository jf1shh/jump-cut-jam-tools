---
tier: epic
source: _config/reference/knowledge-base.md
updated: 2026-11-06
---

# Unreal MCP traps from forum reports and Epic's trainer

Not run by us. Mostly UE 5.8.0 to 5.8.1 reports; re-test on 5.8.4 before relying on a fix.

## Tip: success from `set_properties` is not proof
- **Why:** `ObjectTools.set_properties` on an Input Mapping Context's `Mappings` reports success and saves
  nothing, and `get_properties` then reads the fake value back. Array size and contents cannot change in one call.
- **How to check:** author key mappings with Python (`InputMappingContext.map_key`) or by hand, then verify at
  runtime with `showdebug enhancedinput`.

## Tip: budget for `CaptureViewport` and `find_actors`
- **Why:** `CaptureViewport` needs `captureTransform` and `annotations` passed as explicit `null`, and returns
  1.5 to 2.6 million characters of base64 per call. `find_actors` cuts off at 20 results without saying so.
- **How to check:** call it inside a script and keep only the labels; count results against the expected number.

## Tip: describe only the toolset you need
- **Why:** per Epic's trainer, a materials describe can cost 2,000 to 26,000 tokens and Niagara close to 250,000.
  A truncated describe makes the agent loop.
- **How to check:** a simple material should take about a minute. Much longer means a truncated tool description.

## Tip: prefer one script over many calls
- **Why:** serial calls on the game thread are slow, and passing `list_properties` output to `get_properties` crashed 5.8.1.
- **How to check:** group multi-step edits in ProgrammaticToolset (one Python script). Save before and after batches.

## Tip: a "save content" dialog looks like a hang
- **Why:** it blocks compiling (webinar note).
- **How to check:** save after each batch of edits.

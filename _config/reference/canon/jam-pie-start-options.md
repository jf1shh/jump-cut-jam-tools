---
tier: tested
source: stages/00_prep/output/mock-jam-findings-13.md
updated: 2026-11-10
---

# Starting PIE over MCP: pass options, and capture a floating window

Tested on 5.8.4; re-test on 5.9 before relying on it.

Seen once (mock jam 13, UE 5.8.4 Linux editor, n=1).

## Trap: `StartPIE` without options fails
- **Why:** the call returns `Function "StartPIE", input param "options" is required by the function input schema
  Json, but is missing from the incoming function input params Json.`
- **How to check:** always send an `options` object with `StartPIE`.

## Tip: use the floating play mode so captures are live
- **Why:** the default in-viewport PIE gave stale, unchanged captures. `PlayMode_InEditorFloating` gave a live
  1280x720 window that `CaptureEditorImage` (900x640) shows. `CaptureViewport` only shows the editor camera, not PIE.
- **How to check:** capture twice a few seconds apart while the game moves; the two images must differ.

## Trap: `CaptureEditorImage` returns a URN on 5.9
- **Why:** on 5.9 the tool returns a resource URN, not image data, so the capture method above no longer works there (seen in mock 15, `mock-jam-findings-15.md:149-163`). *Superseded (2026-11-10):* "`CaptureEditorImage` shows the floating window"; true on 5.8.4 only.
- **How to check:** on 5.9 use `HighResShot` through `execute_console_command` (see `jam-editor-mcp-helper`) and open the PNG.

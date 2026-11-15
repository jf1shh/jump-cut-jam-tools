---
tier: community
source: stages/00_prep/output/mock-jam-findings-11.md (branch mock11-findings, Iteration 9) and scripts/hud_text_box.py
updated: 2026-11-10
---

# Readable HUD text: always a backdrop box

Status: **tried in the editor 2026-11-09 by the hub: the recipe renders; apply and splice needed the fixes above**
(white "YOU LOSE" on a dark see-through box, box behind the text; the fixes are in the helper and in this note).
The mock 11 facts below were seen on screen. The tier stays `community` (one run, in a small PIE viewport, not the
packaged 1920x1200 game). Re-check on the packaged build and fix this note the same day.
*Update (2026-11-10):* the new end-text size and colour facts in the last two tips were seen on the PACKAGED 1920x1200 build (`mock-jam-findings-11.md:64,79`), so they are stronger than the rest; they stay here until a second run repeats them.

## Tip: every end-state line (win, lose, restart hint) gets a backdrop box
- **Why:** bare HUD text takes whatever colour is behind it. In mock 11 the lose line was dark red on the scene and
  was low contrast, and the balloon covered part of it (vp_r16 frame 43). A dark, semi-transparent box behind the
  text makes any text colour readable.
- **How to check:** take a frame of the end screen and read it yourself. The line must be readable on the lightest
  and the darkest part of the scene. Use a desktop screenshot: `scripts/mx.py shot` did not work on the real editor
  on 2026-11-09 (with `pie` it asks for a Python tool the editor lacks; with `viewport` it fails "Unknown tool
  SlateInspectorToolset...Screenshot"). Fixing `mx.py` is a separate ticket.

## Tip: do not fix contrast by only changing the text colour
- **Why:** mock 11 tried it both ways. Dark red / dark green (the original) was low contrast against the scene.
  Bright orange / light green (vp_r14) washed out on the light ground and was judged worse. No single text colour
  worked on both parts of the scene.
- **How to check:** the same frame check, on the light ground.

## Tip: use the helper, which prints a paste-ready recipe
- **Why:** mock 11 had no ready way to put a box behind HUD text ("no draw-rect node spliced in time"). The helper
  builds one graph function: `HUD|DrawRect` first (so the text lands on top), then `HUD|DrawText`. It uses the
  graph DSL through the editor MCP, the path `jam-blueprint-python-vs-mcp.md` says works (headless Python cannot add
  graph nodes). It uses named pin args (`:Text :TextColor :ScreenX ...`) because positional args shift (mock 11
  gaps 28 and 31). The box size is an estimate from the text length (26 px per character, 40 px per line, times
  `--scale`, plus padding). Those numbers come from reading mock 11 frames (1920x1200): the default HUD font drew
  about 18-25 px per character and 30-40 px per line, so the box errs large. Limit: the estimate follows `--scale`
  but not the viewport. In a small PIE viewport (705x465) the default box (240x72) was about four times wider than
  the text (about 60 px) and the text sat at the left end of the box. For a small viewport pass smaller `--char-w`
  and `--line-h` (and `--screen-w/--screen-h`), and always look at the frame.
- **How to call it:**
  ```
  scripts/hud_text_box.py "YOU LOSE" --color "#ffcc00" --anchor center
  scripts/hud_text_box.py "YOU WIN" --anchor top-center --box-color "#000000" --opacity 0.7 --json
  scripts/hud_text_box.py "YOU LOSE" --apply --blueprint /Game/Slime/BP_HUD.BP_HUD
  ```
  Without `--apply` it prints the `(fn DrawEndLine () ...)` DSL and two `python3 scripts/mx.py call` commands (the
  script file is not executable): first `add_function_graph` (a new function must exist before `write_graph_dsl`,
  or it fails with "does not exist", mock 11; its parameter is `graph_name`), then `write_graph_dsl`. `--apply` runs
  both (editor up, MCP on 8010, lead agent only); if the function already exists the first call fails and the
  second still runs.
  **Splice step:** the call node is `(CallFunction|DrawEndLine)` (plain `(DrawEndLine)`, `|DrawEndLine` and
  `Class|BPHUD|DrawEndLine` all fail with "does not exist"; `find_node_types` with `type_id_filter "DrawEndLine"`
  and `context_pins []` returns it). `write_graph_dsl` on the EventGraph with
  `(event EventReceiveDrawHUD (SizeX SizeY) ...)` REPLACES that event's whole chain, so "splice" means writing the
  full event body again with `(CallFunction|DrawEndLine)` added, after the win/lose state test. Then compile.
  `--opacity` always sets the box alpha (an alpha inside `--box-color` is ignored); a text colour with alpha
  under 0.5 is rejected. Options: `--anchor` (nine screen positions), `--box-color`, `--opacity`, `--padding`, `--scale`,
  `--screen-w/--screen-h` (default 1920x1200, the Legion playtest size; coordinates are absolute pixels, so when
  checking in a PIE window pass its real size: in a 705x465 viewport the default box was off screen, and
  `--screen-w 700 --screen-h 460` put it in the middle),
  `--char-w/--line-h` to tune the estimate.
- **How to check:** `python3 -m unittest tests.test_hud_text_box`, then a frame of the real screen.

## Tip: if the recipe does not apply, fall back to `set_pin_value`
- **Why:** `write_graph_dsl` on a `(fn ...)` with `DrawText` dropped or shifted args in mock 11 (gap 28), and its
  read-back drops named args (gap 33). The recipe's pins are the AHUD `DrawRect` (`RectColor ScreenX ScreenY ScreenW
  ScreenH`) and `DrawText` (`Text TextColor ScreenX ScreenY Scale`) ones; the colour is passed as a text struct
  `(R=..,G=..,B=..,A=..)`, which rendered correctly in the hub's run. Set each pin with `find_nodes`, `get_node_infos`, `set_pin_value`.
- **How to check:** read the compiled graph back with `get_node_infos` and look at the frame.

## Tip: check the HUD on a packaged 1080p frame; fix right-edge clipping and size
- **Why:** mock 11's win text was clipped at the right edge at 1920x1200 (`Press R to play a`). Scale 3.0 to 2.2 and x 160 to 200 fixed it (`mock-jam-findings-11.md:64,79`). Mock 15's thin grey text was faint on light blue at 1080p (`mock-jam-findings-15.md:32-34`). Dark blue on the blue sky was unreadable; yellow worked (`mock-jam-findings-11.md:136,137`).
- **How to check:** read a packaged 1920x1080 frame: no clipping at the right edge, text about 2x the default scale or more, backdrop box always. A tiny PIE viewport hides all of these.

## Tip: show title and controls while progress is 0
- **Why:** the player in mock 11 was told only "WASD" and could not tell why the balloon floated (`mock-jam-findings-11.md:60,136,167`). A one-line title with the verb, the keys and the goal fixed it. It must hide on the lose screen.
- **How to check:** restart the game; the line shows at start and after restart, not on the lose frame.

---
tier: community
source: ~/Projects/superagent-sandbox/reports/stefan_3d_ai-megajam-lessons.md (lessons 1.1, 1.8, 1.9, 1.10, 2.6, 2.7, 2.10)
updated: 2026-11-09
---

# Grey box first (UNTESTED until the mock run)

All of this is a claim from videos. Nothing here was run by us yet.

## Tip: no assets until the loop can be won, lost and restarted
- **Why:** several video projects proved the core mechanic with primitives and added generated assets later; one-shot "build the game" prompts are called a dead end.
- **How to check:** `python3 ~/Projects/megajam/scripts/greybox_gate.py check --project "$UPROJECT"` exits non-zero (13) until `record --project "$UPROJECT" --won --lost --restarted` was run for that same project; only 0 means go; no expiry; `clear` resets. Prompts: `_config/reference/prompts/greybox/`.

## Tip: axis and units in mechanic prompts, numbers in a feel spec
- **Why:** "slide the door along X by 120 cm" was reported cheaper and more accurate than "open the door".
- **How to check:** in the mock run, count prompts per mechanic that needed a redo.

## Tip: HTML mock first, one Settings actor, one bay per mechanic
- **Why:** reported to cut rework and to make tuning need no new prompts.
- **How to check:** mock run records the HTML-mock rounds and the count of tuning changes without a new prompt.

## Measured result
Hours from start to a winnable grey-box loop on a made-up theme: **NOT MEASURED YET.** Part B needs the hub's editor slot.
When measured, move the measured items to a separate `tested` note (one tier per file) and fill this line.

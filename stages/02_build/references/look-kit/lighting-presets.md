# Look kit: lighting and fog presets (recipe)

Status: **recipe, UNTESTED.** From lessons 1.7 and 2.15 (superagent report). The numbers below are starting points, not measured values.
The human picks a preset by eye from side-by-side frames; the agent does not judge the look (the lesson says model vision is weak, UNTESTED).
Practice scene only, throwaway, not reusable in the entry (Rule 7(h)).

## Base (all presets)
- Sun (directional) set **before** the sky; do not rescue the look with post-process.
- Post Process Volume: infinite extent, manual exposure, light bloom, vignette, slightly lower saturation, volumetric fog on.
- One focal point per scene: the single brightest and highest-contrast area, and it is the goal or the next target.
- Set by hand or by a script that writes values. Never ask the agent to "make it look nice".

## Presets (named; values to tune in Part B)
| Name | Sun | Sky / fog | Focal light | Mood |
|---|---|---|---|---|
| `warm_day` | pitch about -35, warm white, intensity 8 lux-ish | thin light fog, density low | none needed; goal in sun | readable, friendly |
| `cool_fog` | pitch about -20, cool blue, low intensity | heavy mist, fog density high, cool tint | one warm point light on the goal | cool grade with one warm spot |
| `night` | moon-like sun, dim blue | dark sky, light fog | emissive or point light at the goal | contrast from darkness |

Each preset is one small data block (a JSON or Python dict) applied by a script. That script is not in this PR: write it in Part B only if the
recipe survives the first look.

## Check 1: clipping
Take a screenshot (desktop screenshot, not `mx.py shot`; see `_config/reference/canon/jam-hud-readable-text.md`). Count pixels:
- blown white: all channels >= 250; crushed black: all channels <= 5.
- Fail if either share is above 5 % of the frame (limit is a guess, UNTESTED).

```bash
python3 - <<'EOF'
import numpy as np
from PIL import Image
a = np.asarray(Image.open("shot.png").convert("RGB"))
print("white", float((a.min(axis=2) >= 250).mean()), "black", float((a.max(axis=2) <= 5).mean()))
EOF
```

## Check 2: focal point
Blur the frame (about 5 % of width), find the brightest cell on a 8x8 grid of luminance. It must fall inside the goal's screen box.
Also ask one question of the human, not the agent: "which single area is brightest and is it the goal?" Fail on a different cell.
(Rule of thumb from lesson 1.7: highest contrast + warm light against a cool grade, UNTESTED.)

## Part B measures
For each preset on throwaway content: screenshot, run both checks, put the numbers and a verdict in `_config/reference/canon/jam-look-kit.md`.

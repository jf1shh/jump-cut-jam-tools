# HTML mock step (HUD and each effect) and one juice effect per prompt

Claim from videos, UNTESTED here: a throwaway HTML page approved in 2-3 rounds cuts rework before the in-engine build.

## HUD mock
"Write one self-contained `mock/hud.html` (no network, no libraries). 1920x1080 canvas. Show `<elements>` with
placeholder text and numbers, clickable states for `<states>`. No art." Approve, then build UMG to match.

## Effect mock (one per effect)
"Write one self-contained `mock/fx_<name>.html`: a 5 s canvas loop of ONE effect: `<what happens>`. Put timing
(start ms, peak ms, end ms), size (px at 1080p) and colour in a visible table above the canvas." Approve in
2-3 rounds, then build the engine version from the table.

## One juice effect per prompt
One effect per prompt: hit stop, OR screen shake, OR a particle burst, OR a sound hook. Never two in one turn.
Each new effect gets a bool toggle on the Settings actor so the old version stays for A/B. Delete props that distract.

The mock files are scratch: keep them out of the entry unless made inside the contest window.

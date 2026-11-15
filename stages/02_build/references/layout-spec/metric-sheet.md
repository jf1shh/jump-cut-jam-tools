# Metric sheet (what the sketch must obey)

The machine copy is `stages/02_build/references/layout-spec/metrics.json`; `scripts/layout_spec.py` reads it. Change a number there,
not in a layout. All lengths cm. **Every number is UNTESTED** until measured in the editor (rehearsal Part B).
Give this page to the lead agent as context together with the prompt template.

| Item | Value | Where it comes from |
|---|---|---|
| Player height / capsule width | 176 / 68 | UE third-person mannequin, from memory. Videos use 180–190. |
| Walk speed | 500 cm/s | UE third-person template, from memory. Read the project's real value in Part B. |
| Door width | 120 – 400 | Our pick (capsule 68 + room to turn). |
| Door height | at least 220 | Video claim: good door about 220, gate about 270 (lesson 2.13). |
| Door sits from wall ends | at least 50 | Our pick (no door in a corner). |
| Corridor width | at least 200 | Our pick. |
| Room short side | at least 300 | Our pick. |
| Wall height | 300 default, at least 250 | Matches the old fixed room. |
| Jump gap (flat) | at most 300 | Our pick, conservative. |
| Ledge to climb by jumping | at most 120 | Our pick, below `jump_max_height_cm` 150. |
| Wall thickness | 10 | Same as the old fixed room. |
| Length / time declared in the sketch | within 5 % / 0.5 s of computed | Checker tolerance. |

Part B should replace the "from memory" and "our pick" cells with what a real run shows: capsule size and walk
speed from the character blueprint, a real jump apex and run-jump distance with the mannequin, and whether a
220 cm door feels right against the 176 cm hero.

Scale markers every sketch must show: a 500 cm scale bar and a hero capsule (the renderer draws both).

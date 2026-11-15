---
tier: epic
source: 2026 Epic AI MegaJam Official Rules PDF, 16 pages, "Last updated: November 5, 2026" (Section 9); compared with the prep stream in superagent-sandbox/reports/stefan_3d_ai-megajam-lessons.md lesson 2.1
updated: 2026-11-09
---

# Judging criteria: the prep stream's seven vs the Official Rules (Section 9)

**Official source:** the Official Rules PDF, 16 pages, change log "Last updated: November 5, 2026" (Italy removed
from the Restricted Jurisdictions, new Section 21). Public link (Box):
https://epicgames.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z. The owner re-downloaded it on 2026-11-09
(`~/Downloads/2026_Epic_AI_MegaJam_Official_Rules_EN.pdf`, SHA-256
`71457d4dc8bea132e2a45dbffcffddcd6b9c69330706595b1e5fe32e9f042603`) and a hub checked Section 9 against its text.
This note's quotes come from that text, checked again in the ticket session. The `RULES.md` digest, built from the
older v3 (14 pages, 2026-10-26), was brought to this PDF in ticket T-20261109-12. The Nov 10 re-check of the Box PDF is still pending.

What Section 9 says (short phrases from the PDF): seven criteria, each "Up to 5 points": Ambition and
Innovation, Use of Contest Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. "Ambition and Innovation
will be scored on the Submission itself." AI use disclosed is "considered for context only". A tie is
"re-scored with double weight given to Fun Factor". A Student Submission "may win either a Best Overall prize
or a Best Student Project prize, but not both".

## Claimed (stream, lesson 2.1) vs official

The stream reads seven categories out of an AI chat answer, "not from the rules text".

| Claimed category | Official criterion (Section 9) | Result |
|---|---|---|
| ambition/innovation | Ambition and Innovation | match |
| theme use | Use of Contest Theme | match |
| fun | Fun Factor | match |
| gameplay | Gameplay | match |
| visuals | Visuals | match |
| level design/progression | Level Design | match (the "and game progression" in the itch relay is not in the PDF) |
| audio | Audio | match |
| (not claimed) | tie: re-score with double weight on Fun Factor | missing from the stream |
| (not claimed) | Ambition and Innovation scored on the Submission itself | missing from the stream |
| pre-screen: must package, custom gameplay beyond a stock template, no default grid textures | Section 9 does pre-screen, but only "to ensure compliance with the Guidelines and Restrictions and with Sponsor's general standards and practices" | differs: the stock-template and grid-texture tests are not in the PDF; UNTESTED / unofficial, not scored (see `jam-agent-lint-rules`) |

## Judge pass lined up with the official list

`scripts/judge_pass.py` has one category per official criterion, same names, same order. It scores nothing
else; the stream's extra claims are labelled UNTESTED and unofficial in its prompt.

| Official criterion | Judge-pass key | Scored |
|---|---|---|
| Ambition and Innovation | `ambition_innovation` | yes, 1-5 |
| Use of Contest Theme | `contest_theme` | yes, 1-5 |
| Fun Factor | `fun_factor` | yes, 1-5 |
| Gameplay | `gameplay` | yes, 1-5 |
| Visuals | `visuals` | yes, 1-5 |
| Level Design | `level_design` | yes, 1-5 |
| Audio | `audio` | yes, 1-5 |

A test (`tests/test_judge_pass.py`, `OfficialCriteria`) fails if this table and the script's labels drift apart.

---
tier: epic
source: RULES.md
updated: 2026-11-10
---

# MegaJam rules we trip over most (digest of the Official Rules)

Rule numbers are from our `RULES.md` digest. The official PDF is now the 16-page version "Last updated:
November 5, 2026" (re-downloaded by the owner 2026-11-09; SHA-256
`71457d4dc8bea132e2a45dbffcffddcd6b9c69330706595b1e5fe32e9f042603`; link
https://epicgames.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z). The `RULES.md` digest was brought to this
PDF in ticket T-20261109-12; where they differ, the PDF wins. Judging: `jam-judging-criteria`. The Nov 10
re-check is still pending (the 2026-11-09 download does not replace it); re-check once more on Nov 15 morning.
Section numbers below are the PDF's: the one-main-prize-and-one-modifier limit is Section 13 (also Section 10);
"Rule 9" is Section 9.

## Tip: nothing but tools exists before the window opens (Rule 7(h))
- **Why:** the contest period is 2026-11-12 00:00 ET to 2026-11-15 8:59 PM ET. Before it, only AI tools, agent
  configs, MCP settings, prompt libraries and scripts may exist. Epic may ask for the git history.
- **How to check:** `git log --stat` shows no gameplay, level or art files before the window.

## Tip: a human submits (Rule 17)
- **Why:** an agent must never press submit.
- **How to check:** the submission step sits in the owner-only list in the runbook.

## Tip: submission package (Rules 1, 7, 10)
- **Why:** a packaged build that should not require extra software (Section 7(f) says "should not require",
  not "must not"), plus a 30-60 s gameplay video (in the PDF) and, for Glass Box, a dev log submitted with the
  entry (in the PDF, Section 10). The zip name `TeamName_GameName.zip` and the 1 GB limit are not in the PDF
  text (checked 2026-11-09); they come from the itch page. Keep them anyway.
- **How to check:** unzip on a clean Windows machine and launch.

## Tip: content limits (Rules 7(i), 8, 15(d))
- **Why:** teen-rated, English only, no third-party IP or trademarks except the Unreal Engine logo.
- **How to check:** nothing from UC2, UT2004, uc2-pc or UTLegacy in this repo.

## Tip: sourced assets are allowed but not scored (Rule 15(c))
- **Why:** AI-generated content is not a "sourced asset", but Fab and similar assets must be licensed and listed.
- **How to check:** keep the credits ledger current as you add anything.

## Tip: one prize and one modifier per entry (Section 13: "Limit one (1) main category prize and one (1) Modifier Prize per Submission")
- **Why:** we aim for Glass Box (best dev log).
- **How to check:** write the dev log as you go, not at the end.

## Tip: run the packaged exe once on a clean profile before submitting (our inference)
- **Why:** judges' machines will see the same firewall prompt and any engine warning text ("lighting needs to be rebuilt") that we saw in mocks 10 and 15, and Section 7(f) says the build should not need extra software. Engine overlay text costs polish. This is our reading, not Epic's wording.
- **How to check:** a frame from the clean-profile run shows only the game. Fix with the tips in `jam-legion-capture-and-video-traps` and `jam-packaging-windows`.

# Judge pass: a second agent rates the build like an Epic judge

Owner, 2026-11-08 (hub plan item 5). Runs **after** the agent playtest gate prints `GATE PASS`
(`stages/03_playtest/references/agent-playtest.md`). The playtester proves the build can be won, lost and restarted. The judge says
how good it looks to a stranger. The result goes in the owner handoff message **before the build link**.

Tool: `scripts/judge_pass.py` (tests: `tests/test_judge_pass.py`, run with `python3 -I tests/test_judge_pass.py`).

## Criteria

The seven from Official Rules Rule 9 (`RULES.md`), 1 to 5 each, whole numbers, max 35:
Ambition and Innovation, Use of Contest Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio.
Disclosed AI use is context only and must not move a score. Sourced assets are not scored.
One judge category per official criterion, same names and order. Anything the prep stream claims that Rule 9
lacks (a pre-screen, a default-texture rule) is UNTESTED and unofficial, never scored. The comparison table
is `_config/reference/canon/jam-judging-criteria.md`.

## Steps

1. Playtest gate passed, so the session folder (`$AGENT_PLAYTEST_DIR`) has its journal and frames.
   **A Legion `visual_playtest` gate folder also works** (mock 12 failure, fixed): it has `results.json` and
   frames in the folder itself, but no `journal.jsonl`, so the old packet died with "no journal.jsonl".
   Now the packet refuses a gate folder whose gate has not passed (no valid `gate.ok`; run
   `visual_playtest.py gate` first). It takes the folder's gameplay stills first and fills any spare slots with
   one frame per idle burst (found by `manifest.json`'s `burst` flag, else the `_burst_` file name), leaves
   contact sheets out, has no win/lose/restart marks, and `packet.json` says `"source_kind": "visual_playtest"`. Give `--out` a sub-folder such as
   `GATE/judge`, never the folder itself. Hand fallback if the tool still fails: pick 8-12 frames from the
   gate folder by eye, copy them into a new folder with `prompt.md` text from a working run, and have the
   judge reply in the same JSON shape; parse it with `judge_pass.py parse REPORT` (needs no packet).
2. Make the packet (also checks the itch page draft):

   ```bash
   python3 ~/Projects/megajam/scripts/judge_pass.py packet \
     --session "$AGENT_PLAYTEST_DIR" --page PATH_TO_ITCH_DRAFT --video PATH_TO_GAMEPLAY.mp4 --out "$AGENT_PLAYTEST_DIR/judge"
   ```

   The packet holds the marked win, lose and restart evidence plus a spread of other frames (default 12),
   `prompt.md`, `report-template.json`, `page-check.json`. Exit 2 means a page check failed; the packet is
   still made so the judge can see it, and the failure goes in the handoff.
3. Start a **fresh** agent session (not the playtester, not the builder). Give it `prompt.md` and the frames.
   It must not open the source, the GDD or the brief. It reads each cited PNG with Read and replies with
   one JSON object in a fence.
4. Parse and check the reply:

   ```bash
   python3 ~/Projects/megajam/scripts/judge_pass.py parse REPORT.md --packet "$AGENT_PLAYTEST_DIR/judge" --out "$AGENT_PLAYTEST_DIR/judge/scores.json" --md
   ```

   Exit 0: the `--md` block is ready to paste. Exit 2: the report broke a rule (score outside 1-5, missing
   criterion, evidence not one sentence, evidence over 40 words, cited file not in the packet, over 3 fixes).
   Send it back to the judge once. Exit 3: unreadable input.
5. Put the block in the owner handoff, above the build link. A hub or human spot-checks one or two cited
   frames, the same as for the playtest report.

## Itch page draft checks

`judge_pass.py page-check PAGE [--video FILE]` also runs alone. A page is a file or a folder (`.md`, `.txt`,
`.html`; screenshots and a video may sit beside it).

| Check | Passes when |
|---|---|
| video | a local file that `ffprobe` says is 30-60 s and at least 1920x1080 (OBS settings in `stages/04_ship/references/capture-setup.md`), or a link to YouTube/Vimeo/Twitch (length cannot be checked from a link: confirm by hand) |
| screenshots | at least 3 images (our bar, not the rules') |
| controls_text | a "controls" section that names real keys or buttons |
| credits | a credits section (paste `sourced_assets.py credits`) |
| ai_declaration | a statement on AI use |
| english_only | no non-Latin text (Rule 7(i)) |

A video file that cannot be probed fails on purpose: check it by hand, do not assume.

## What it cannot do

It rates frames, not feel. A judge model sees stills, so Fun Factor and Audio scores are guesses from the
playtester's notes and the clip; treat them as a prompt for the owner's own check, not as truth. The judge
can also be too kind: a 5 with a weak sentence of evidence is a reason to look at the frame.

# Grey-box prompt library (tooling only, UNTESTED)

Templates with blanks. They hold no game content (Rule 7(h)); fill the blanks inside the contest window.
Source: video lessons 1.1, 1.8, 1.9, 1.10, 2.6, 2.7 in the YouTube report. Every point is a claim, UNTESTED here
until the mock run in `_config/reference/canon/jam-grey-box-first.md` is measured.

Order of work:
1. Primitives only. No image, 3D or audio generation until `python3 ~/Projects/megajam/scripts/greybox_gate.py check --project "$UPROJECT"` exits 0 (any other exit code means
   stop). The session is rooted in the game project, not in megajam, so use the absolute path.
2. One mechanic per prompt: `01-mechanic-prompts.md`.
3. Feel numbers from a spec, not adjectives: `02-feel-spec-template.md`.
4. One juice effect per prompt, each mocked first: `03-html-mock-step.md`.
5. Every tunable on one Settings actor, one bay per mechanic in a test room: `04-settings-and-test-room.md`.
6. Every agent turn ends with a launched build and a screenshot (lead-agent brief line).

Numbers only from other games, never their content (Rules 8, 15(d)).

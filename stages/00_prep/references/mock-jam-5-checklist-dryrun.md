# Mock jam 5 — submission + playtest checklist dry run

Rehearsal only, not the real Sunday submission run. Run against mock jam 5's ("Last Light") actual
state as of 2026-10-29. Most submission-checklist items legitimately fail or don't apply for a mock
jam — that's expected; the point is practicing the run-through, not passing it.

## Submission checklist (win-plan.md lines 152–168)

- [x] Packaged Development build for Win64, launched on a clean-ish Windows machine (Legion Go S) with
  no extra installs
- [x] Zip under 1 GB (431.6 MB) — not named `TeamName_GameName.zip` yet, that's a real-jam-only step
- [ ] Game visibly uses the theme — N/A, mock jam has no assigned theme
- [ ] Everything in English — not checked this session
- [ ] No third-party IP/trademarks — not checked this session
- [ ] Teen-appropriate content — not checked this session
- [ ] Video (30–60s, 1080p+) — not produced, no OBS capture this session
- [ ] Dev log link — entry drafted today (`stages/05_devlog/output/2026-10-29.md`), not published to itch.io
  (mock jam has no itch.io page)
- [ ] Sourced assets listed — not audited this session
- [ ] Pre-jam declaration — N/A for a mock jam
- [x] Short AI-use disclosure — in today's dev log entry
- [ ] Entry form fields — N/A, no real entry form for a mock jam
- [ ] Human clicks Submit — N/A, nothing to submit

## Playtest checklist (_config/reference/templates/playtest-checklist.md)

- [x] Launched the actual packaged build, not the editor — yes, on the Legion Go S
- [ ] Core verb works and feels like the GDD describes — **fails**. The owner reported controls don't
  work; root cause confirmed (bare `Pawn`, no movement component — see findings doc)
- [ ] Full run possible start to end screen, no soft locks — not verified; the orb can't move, so a
  full run couldn't be attempted
- [x] Someone other than the agent played it — the owner, this session
- [x] Theme is visible in the first minute — N/A for a mock jam, but the lantern/beacon concept reads
  immediately
- [ ] Frame time holds 60fps/1080p on the weakest Windows box — not measured this session (nullrhi
  editor session, no in-engine profiling run against the Legion Go S build)
- [x] No placeholder text, debug UI, or dev-only hotkeys left visible — none reported by the owner
- [x] Runs with no extra installs on a clean-ish machine — yes, Legion Go S, confirmed by the owner's
  playtest
- [x] Broken things go on the findings/cut list, not fixed ad hoc mid-playtest — both bugs deferred to
  `stages/00_prep/output/mock-jam-findings-5.md` per the owner's explicit choice, not patched this session

## Takeaway

The dry run itself worked as intended: most submission-checklist items correctly don't apply to a mock
jam, and the playtest checklist caught a real, previously-undetected failure (core verb doesn't work)
that graph-level QA had passed clean. That's the exact gap this rehearsal exists to surface before
the real Sunday run.

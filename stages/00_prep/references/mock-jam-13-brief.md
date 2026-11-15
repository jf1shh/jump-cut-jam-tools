# Mock jam 13 brief: liquid metal balloon

> **RESERVE (owner 2026-11-07, overnight reschedule).** Mock 13 has no slot. Gap 5c moved into mock 12
> (Mon Nov 9 night). This mock runs only if an earlier night fails a gate and the owner asks for it
> (a daytime slot, or Wed); otherwise it is dropped. If 5c fails in mock 12, it is fixed by hand on Wed morning (07:00-10:30), not here.

Plan: `stages/00_prep/references/mock-jams-10-14-plan.md`. Slot: none (reserve, see the note at the top; the old Tue Nov 10 daytime slot is cancelled).
Findings file: `stages/00_prep/output/mock-jam-findings-13.md`.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`, and delete it after. No gameplay,
level, art, audio or game code from this mock may be reused in the real entry. Only tooling fixes and the
findings doc come back.

## Theme reveal (read at T+0)

> **LIQUID METAL BALLOON.** Make a game about a balloon made of mercury.

## Game idea seed

A mirror-silver blob rolls through a dark chrome lab. It can split into small beads to pass through grates
and merge back into one body. Beads must reach a pool together; lose too many beads and the blob is too
small to finish.

## Physics and material focus

Reflective metal material (high metallic, near-zero roughness, reflections of the room), merge and split
of blobs, bead count as the health bar. This is the hard one for the Legion Go S: reflections cost.
Measure it, do not guess.

## Readiness gap to prove: 5c (desktop video capture)

`stages/00_prep/references/jam-readiness-2026-11-06.md` row 5c: OBS on the Legion works (1080p60, F9 replay), but the desktop
has no tested capture path (Wayland, no `wf-recorder`). In this mock:

1. Record the 30-60 s video **on the desktop** from the editor or a standalone game window. Try, in order:
   `wf-recorder` (if the owner installed it), `spectacle` screen recording, `ffmpeg` with `kmsgrab`.
   Record which worked, the exact command, resolution (target 1920x1080 or higher) and frame rate.
2. Also record the same play on the Legion with OBS, as the main video. Compare in one line: which is
   better for the submission.
3. Run the ffmpeg two-pass `loudnorm` (-23 LUFS) on the mix before muxing, per `PLAN.md` day 4 notes, so
   that step has been run once too.
4. Check the video length is 30-60 s and the file plays.
5. Lumen / perf: take the QA harness frame-time reading on the Legion for the chrome scene. Record fps at
   1080p. Note if you had to turn reflections down and by how much.

## Pass / fail gates

- [ ] PASS 5c: a desktop capture command that produced a playable 30-60 s clip at 1080p or higher is named in
      the findings. FAIL (with the reason) if none worked; then the fallback is Legion OBS only.
- [ ] Greybox plays: reflections, merge, split visible.
- [ ] PASS visual playtest (REQUIRED before "done"): `scripts/visual_playtest.py` ran on the PACKAGED build with
      real OS input (never the game's autopilot), and every item in its `checklist.md` is PASS after you read the
      frames. Details: `stages/03_playtest/references/playtest-gate.md`.
- [ ] PASS short-clip motion check (REQUIRED, part of that gate): the run includes a ~3 s no-input burst
      mid-play, in each end state (lose, win) and after restart. Read each `contact_*.png` and keep the
      `Idle stability` item PASS: FAIL on a looping or falling camera, flicker or respawn spam. Mock 10's lose
      state looped its camera; 4 still frames passed it, the video
      (`~/Projects/megajam/work/legion-video/legion_screen.mp4`) showed it.
- [ ] Before the owner sees a build, the agent playtester plays it like a human (`stages/03_playtest/references/agent-playtest.md`,
      T-20261108-11): it must reach the WIN state by real play, lose on purpose, and restart, with frames +
      clips as evidence.
- [ ] Legion fps at 1080p recorded for the chrome scene.
- [ ] `loudnorm` two-pass ran on the mix.
- [ ] Windows package pushed to `jf1shh/megajam-pretest:win64`, processed.
- [ ] Within 10 h. Lemonade restored at ctx 32768.
- [ ] Findings in `stages/00_prep/output/mock-jam-findings-13.md`.
- [ ] `~/Projects/megajam-mock` deleted after the findings merge.

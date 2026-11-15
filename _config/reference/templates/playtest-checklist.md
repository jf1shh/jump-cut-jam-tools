# Playtest checklist

Run this on every packaged build (build #1 through the final build), not just at the end.

- [ ] Launched the actual packaged build, not the editor (catches packaging-only bugs)
- [ ] Core verb works and feels like the GDD one-pager describes
- [ ] Full run possible start to end screen, no soft locks
- [ ] Someone other than you played it (required for build #2, day 2 — do it earlier if you can)
- [ ] Asked the player the five questions in `_config/reference/canon/jam-design-cheatsheet.md` section 5 and wrote the
      answers in the fix list
- [ ] Theme is visible in the first minute (Rule 7(g))
- [ ] Frame time holds the 60 fps / 1080p budget on the weakest Windows box you have (the QA harness
      logs this; eyeball it here too)
- [ ] No placeholder text, debug UI, or dev-only hotkeys left visible
- [ ] Runs with no extra installs on a clean-ish machine (Rule 7(f)) — the Legion Go S after a fresh
      package counts
- [ ] Anything broken goes on the day's cut list or the next slice's brief, not fixed ad hoc mid-playtest

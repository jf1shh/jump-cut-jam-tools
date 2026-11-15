# Dev log entry — 2026-11-11 (Jump Cut, night 1)

## What shipped today
- A greybox Scene 1: one straight road with a sky and a ground, built from plain boxes.
- A car that drives the road by itself. You switch between lanes with left/right.
- The core move: hold to line up a shot, release to cut, cancel to back out.
- One stunt, S1-1 (a false front that falls over). It works, but it is a grey slab that falls fast and is hard to read. This is the first thing to fix.
- Gamepad and keyboard/mouse both drive the game. Package B did not start from the gamepad on the Legion, so Package B2 and B3 add raw-input fallbacks. B2 was confirmed by hand on the Legion; B3 is being tested.
- Five more greybox stunts (S1-2 to S1-6) exist as assets only. They are not tested.

Honest status: everything is greybox, no final art or sound yet.

## Note for the editor of this entry
The generator's media list (work/generated/*) is pre-jam concept art, not window content. It is left out on purpose (Rule 7(h)). Add real screenshots from the Legion packaged build instead.

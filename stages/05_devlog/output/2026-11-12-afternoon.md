# Dev log: Thursday Nov 12, afternoon. The game finds its film

<!-- Draft, kit 3. Facts from the hub checkpoint table and the lead's notes. The longer day entry is
reports/jam-page/devlog-2026-11-12.md. Replace the three [SHOT] slots with stills from the B14 capture. -->

This afternoon the game changed direction. I told the team to lean into the film-stunt side: the player has to nail the perfect shot for the director, and people love jumping cars and cool camera shots.

The first piece already works. There's a ramp jump now: the car leaves the lip at the 336-meter mark of the track and stays in the air for 1.1 seconds. A side camera cuts in for the jump and slows to 0.6x at the top. The canal corkscrew rolls the car a full 360 degrees; our first try at 270 landed it on its side.

[SHOT 1: the corkscrew from the jump camera]

The new HUD work landed in build 98, including the director's voice on the wrap card. I also approved a pacing redesign: a faster scene with a throttle, later warnings, a new TOO SAFE stamp for passes that play it safe, and a curved road for Scene 1.

[SHOT 2: the wrap card with the new HUD]

On the speed side, our handheld tester found about 3 ms of graphics work per frame that the auto-resolution system doesn't count, so frames land near 18 ms instead of the 16.7 ms that 60 fps needs; next we name it and tune for it.

Friday at 2 PM, two friends in other states will play the test build on their own PCs while I watch over a video call. They get a one-page how-to and no controls help, because the test is whether the game teaches itself.

[SHOT 3: the remote test setup or the curved road]

Saturday night, if there's time after the final Windows upload, we'll try a bonus build that plays in the browser.

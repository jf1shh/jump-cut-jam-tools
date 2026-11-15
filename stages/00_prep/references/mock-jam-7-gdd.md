# GDD one-pager — Signal Run (mock jam 7)

Mock rehearsal, not the real entry — no real contest theme exists yet, so this uses a placeholder
theme chosen only to give the pipeline something concrete to build. Goal of this jam: run every
stage of the real pipeline end to end on a **real playable level** (floor, walls, win condition) —
mock jam 6 only produced floating QA-harness scratch content, never a real level.

- **Theme tie-in:** placeholder theme "Signal" — the player relays a light signal across a dark room.
- **Core verb:** move toward the beacon.
- **Loop:** player orb spawns at one end of a walled room; moves toward a glowing beacon at the far
  end; touching the beacon ends the run in a win.
- **Win/lose states:** win = player overlaps the beacon (prints "SIGNAL DELIVERED", stops the clock).
  No lose state this jam — scope is intentionally this small to exercise the pipeline, not design depth.
- **Fun Factor bet:** not a fun-factor target — this is a tooling rehearsal, not a scored entry. The
  "fun" bar here is "every stage of the pipeline — gen, build, wire, QA, agent playtest, package,
  human playtest — runs clean on real content once."
- **Visual direction:** small glowing beacon tower + a simple rolling orb, same visual family as the
  mj6_beacon/mj6_orb assets but placed in a real room (floor + 4 walls) instead of empty space.
- **Scope cut list:** (1) no lose state, (2) no UI beyond a print/log on win, (3) no secondary
  mechanics (no projectiles, no collectibles) — if anything runs long, cut art polish first, not the
  win condition.
- **Out of scope:** multiplayer, saves, settings, title screen, audio (deferred — Nexus GPU-allowlist
  gap for audio generation is still open per mock-jam-findings-4.md).

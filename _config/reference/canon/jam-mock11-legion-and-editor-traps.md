---
tier: tested
source: stages/00_prep/output/mock-jam-findings-11.md
updated: 2026-11-10
---

# Mock jam 11: Legion capture and editor traps we hit and re-ran

Every item here was seen in mock jam 11 and checked by running again (a re-run, a restart or a repackage).
Items seen once and not re-tested are in `jam-mcp-mock11-unconfirmed-traps.md` (community tier).

## Tip: an all-black Legion capture means re-run the playtest before you suspect the build

- **Why:** one playtest (`vp_r15`) came back with all-black frames and `verify` failed on the black frame. A plain
  re-run on the same package (`vp_r16`) gave real frames and passed. The build was fine.
- **How to check:** re-run `visual_playtest.py run` on the same package once. If the frames are still black, look at the
  Legion console: a locked screen (`LockApp.exe` running) makes every capture black, and it also stops
  `legion_record.py` from starting OBS ("OBS websocket did not answer within 90s"). Unlock the Legion, then re-run.
  Only after that look at the build.
- **Seen again (mocks 14 and 15):** the lock killed the visual playtest, the agent playtest and the video in mock 11,
  mock 14 (`mock-jam-findings-14.md:17,25`, locked between 23:01 and 23:04) and mock 15 (`mock-jam-findings-15.md:127`).
  Turn the idle lock off for the whole window. Run the lock probe before every playtest or clip. Never read 47 black
  frames as a build bug. `scripts/legion_playtest.py` now probes for `LockApp.exe` first (PR 150).

## Tip: never run `systemctl --user stop 'megajam-job-*.scope'` while the editor is needed

- **Why:** the editor runs in its own `megajam-job-*` scope. Stopping the scopes killed the live editor and its MCP
  server, and the session had to start the editor again.
- **How to check:** `systemctl --user list-units 'megajam-job-*'` before stopping anything. Stop one named scope that is not
  the editor's, or wait until the editor is closed. After a restart, confirm port 8010 answers before sending MCP calls
  (the `-ModelContextProtocolStartServer -ModelContextProtocolPort=8010` flags served it; the ini pin alone did not).

## Tip: a content-only package runs as `UnrealGame.exe`; tell the playtest and the recorder

- **Why:** on the Legion the root launcher (`MockHelium.exe`) is blocked by Application Control, so the game task fails
  (`schtasks` LastResult -2147020345). The package still runs through
  `Engine\Binaries\Win64\UnrealGame.exe ..\..\..\<Game>\<Game>.uproject`. `visual_playtest.py` and `legion_record.py`
  now do this when `MJ_GAME_PROC=UnrealGame` is set, and watch and close that process instead of the game name. Never pass
  the bare game name for this case: it opens a popup ("must exist and contain a DefaultEngine.ini").
- **How to check:** `MJ_GAME_PROC=UnrealGame ./scripts/visual_playtest.py run ...`; the checklist frames should show the
  game, and `Get-Process UnrealGame` on the Legion should list it during the run. The tests cover the command that is built.

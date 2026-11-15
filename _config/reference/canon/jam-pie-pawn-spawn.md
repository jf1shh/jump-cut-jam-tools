---
tier: tested
source: stages/00_prep/output/mock-jam-findings-13.md
updated: 2026-11-10
---

# PIE spawned no pawn: place the player in the level

Tested on 5.8.4; re-test on 5.9 before relying on it.

Seen once (mock jam 13, UE 5.8.4 Linux editor, n=1). The cause of the second failure was not found.

## Trap: the GameMode `DefaultPawnClass` spawned no pawn in PIE
- **Why:** first the log said `LogGameMode: FindPlayerStart: ... NO PLAYERSTART with positive rating` because a tower
  cylinder overlapped the PlayerStart. After that was fixed there was still no pawn, and the cause was not found.
  PIE then showed an editor-like camera with no error. MCP calls and screenshots stay silent; only the log (or a
  missing BeginPlay print) reveals it.
- **Fix that worked:** place `BP_Player` in the level and set `AutoPossessPlayer=Player0`. The loop was playable
  at 22:35Z after that.
- **How to check:** after the first PIE start, read the editor log for `FindPlayerStart` and look for a BeginPlay
  print from the pawn. Keep level props off the PlayerStart.

## Tip: hide the DefaultPawn sphere in a fixed-camera grey-box
- **Why:** in mock 16 the DefaultPawn sphere showed in the play area; the game hid the pawn in BeginPlay and put the PlayerStart behind the backdrop. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** the first PIE and packaged frames show no grey sphere.

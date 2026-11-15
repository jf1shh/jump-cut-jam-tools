# Visual playtest checklist

Build: C:\Dev\megajam-mock\Packaged\SilentBlade_MockSlime.zip
Run: 9664088854ca4d2989b1ed018596c870

Look at the contact sheets (one Read each), not every PNG: contact_steps_1.png, contact_steps_2.png, contact_steps_3.png
Open a single PNG only when a tile is unclear. `Auto:` is a cheap hint, never the verdict.
Replace `Verdict: PENDING` with `Verdict: PASS` or `Verdict: FAIL - <why>` on every item.
Every step below is prefilled with the harness verdict (PASS / WARN / FAIL / AGENT). AGENT, WARN and FAIL
are unresolved: after looking, write `Verdict: PASS` or `Verdict: PASS (reviewed: <why>)`, or `Verdict: FAIL - <why>`.
A blank verdict never passes. An Auto FAIL may only be passed with `(override: <why>)`.
Then run `./scripts/visual_playtest.py gate <this folder>`; the build is not done until it exits 0.

### 1. Frames are real captures (not black, flat or undecodable)
Auto: PASS - 80 frames, all decodable with visible detail
Look at: 01_start.png, 02_idle.png, 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 19_climb2.png, 20_climb3.png, 21_climb4.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 27_pass.png, 28_exit.png, 41_restarted.png, 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 2. Real level, not the default grid or an empty room
Auto: AGENT - colour present; read the frames to judge
Look at: 01_start.png, 02_idle.png, 15_air.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 3. Player and goal objects visible and readable
Auto: AGENT - judge by reading the frames
Look at: 01_start.png, 02_idle.png, 15_air.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 4. Input visibly moves the player (frames before and after input differ)
Auto: PASS - 10/11 input steps changed the picture: 15_air.png=61.4, 16_slit.png=52.5, 17_atwall.png=47.7, 18_climb1.png=54.4, 22_run0.png=56.6, 23_run1.png=56.8, 24_run2.png=46.5, 25_run3.png=19.7, 26_slot.png=58.7, 28_exit.png=0.2, 54_squash1.png=24.8 (idle baseline 0.3, needed >= 2.0)
Look at: 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 28_exit.png, 54_squash1.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 5. Proper HUD, no debug PrintString / warning text on screen
Auto: PASS - no debug-colour text, no debug words found
Look at: 01_start.png, 02_idle.png, 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 19_climb2.png, 20_climb3.png, 21_climb4.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 27_pass.png, 28_exit.png, 41_restarted.png, 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 6. A win or lose screen is reachable
Auto: AGENT - judge by reading the last frames; the sequence must have reached a win or lose screen
Look at: 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 7. Restart works (the restarted frame is a fresh start, not the end screen)
Auto: PASS - restarted frame vs first frame differ by 3.9 (limit 12.0); vs the frame before restart 24.1 (needs >= 2.0)
Look at: 01_start.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

### 8. Idle stability: with no input the view holds still (no looping camera, falling camera or flicker)
Auto: PASS - midplay: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.4 | win: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.1 | afterrestart: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.4 | lose: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.2 | afterrestart2: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.4
Look at: contact_midplay.png, contact_win.png, contact_afterrestart.png, contact_lose.png, contact_afterrestart2.png
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

## Step review (prefilled from the harness; resolve every AGENT, WARN and FAIL)

#### Step 01: start, t=22.22s (contact_steps_1.png, tile 1; 01_start.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

#### Step 02: idle, t=23.91s (contact_steps_1.png, tile 2; 02_idle.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

#### Step 03: air, t=29.63s (contact_steps_1.png, tile 3; 15_air.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

#### Step 04: slit, t=30.96s (contact_steps_1.png, tile 4; 16_slit.png)
Auto: PASS
Verdict: PASS

#### Step 05: atwall, t=32.59s (contact_steps_1.png, tile 5; 17_atwall.png)
Auto: PASS
Verdict: PASS

#### Step 06: climb1, t=33.74s (contact_steps_1.png, tile 6; 18_climb1.png)
Auto: PASS
Verdict: PASS

#### Step 07: climb2, t=35.36s (contact_steps_1.png, tile 7; 19_climb2.png)
Auto: PASS
Verdict: PASS

#### Step 08: climb3, t=36.97s (contact_steps_1.png, tile 8; 20_climb3.png)
Auto: PASS
Verdict: PASS

#### Step 09: climb4, t=38.59s (contact_steps_2.png, tile 1; 21_climb4.png)
Auto: PASS
Verdict: PASS

#### Step 10: run0, t=39.43s (contact_steps_2.png, tile 2; 22_run0.png)
Auto: PASS
Verdict: PASS

#### Step 11: run1, t=41.18s (contact_steps_2.png, tile 3; 23_run1.png)
Auto: PASS
Verdict: PASS

#### Step 12: run2, t=42.94s (contact_steps_2.png, tile 4; 24_run2.png)
Auto: PASS
Verdict: PASS

#### Step 13: run3, t=44.7s (contact_steps_2.png, tile 5; 25_run3.png)
Auto: PASS
Verdict: PASS

#### Step 14: slot, t=47.73s (contact_steps_2.png, tile 6; 26_slot.png)
Auto: PASS
Verdict: PASS

#### Step 15: pass, t=49.85s (contact_steps_2.png, tile 7; 27_pass.png)
Auto: PASS
Verdict: PASS

#### Step 16: exit, t=52.97s (contact_steps_2.png, tile 8; 28_exit.png)
Auto: PASS
Verdict: PASS

#### Step 17: restarted, t=63.42s (contact_steps_3.png, tile 1; 41_restarted.png)
Auto: PASS
Verdict: PASS

#### Step 18: squash1, t=72.69s (contact_steps_3.png, tile 2; 54_squash1.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

#### Step 19: squash2, t=78.87s (contact_steps_3.png, tile 3; 55_squash2.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

#### Step 20: restarted2, t=88.47s (contact_steps_3.png, tile 4; 68_restarted2.png)
Auto: AGENT
Verdict: PASS (reviewed: frames read, look right; win/lose boxes readable, blob splash visible)

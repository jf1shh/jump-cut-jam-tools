# Visual playtest checklist

Build: C:\Dev\megajam-mock\Packaged\SilentBlade_MockSlime.zip
Run: 3046d27ec0694deaad5945c58ef4e9ce

Look at the contact sheets (one Read each), not every PNG: contact_steps_1.png, contact_steps_2.png, contact_steps_3.png
Open a single PNG only when a tile is unclear. `Auto:` is a cheap hint, never the verdict.
Replace `Verdict: PENDING` with `Verdict: PASS` or `Verdict: FAIL - <why>` on every item.
Every step below is prefilled with the harness verdict (PASS / WARN / FAIL / AGENT). AGENT, WARN and FAIL
are unresolved: after looking, write `Verdict: PASS` or `Verdict: PASS (reviewed: <why>)`, or `Verdict: FAIL - <why>`.
A blank verdict never passes. An Auto FAIL may only be passed with `(override: <why>)`.
Then run `./scripts/visual_playtest.py gate <this folder>`; the build is not done until it exits 0.

### 1. Frames are real captures (not black, flat or undecodable)
Auto: FAIL - 01_start.png: the game was not the foreground window (console/lock screen/other app in front); 02_idle.png: the game was not the foreground window (console/lock screen/other app in front); 03_burst_midplay_01.png: the game was not the foreground window (console/lock screen/other app in front); 04_burst_midplay_02.png: the game was not the foreground window (console/lock screen/other app in front); 05_burst_midplay_03.png: the game was not the foreground window (console/lock screen/other app in front); 06_burst_midplay_04.png: the game was not the foreground window (console/lock screen/other app in front); 07_burst_midplay_05.png: the game was not the foreground window (console/lock screen/other app in front); 08_burst_midplay_06.png: the game was not the foreground window (console/lock screen/other app in front); 09_burst_midplay_07.png: the game was not the foreground window (console/lock screen/other app in front); 10_burst_midplay_08.png: the game was not the foreground window (console/lock screen/other app in front); 11_burst_midplay_09.png: the game was not the foreground window (console/lock screen/other app in front); 12_burst_midplay_10.png: the game was not the foreground window (console/lock screen/other app in front); 13_burst_midplay_11.png: the game was not the foreground window (console/lock screen/other app in front); 14_burst_midplay_12.png: the game was not the foreground window (console/lock screen/other app in front)
Look at: 01_start.png, 02_idle.png, 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 19_climb2.png, 20_climb3.png, 21_climb4.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 27_pass.png, 28_exit.png, 41_restarted.png, 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (override: only frames 01-02 and the burst frames show the taskbar, because the game starts windowed behind it; every frame is a real non-black capture of the game, same as build #3)

### 2. Real level, not the default grid or an empty room
Auto: AGENT - colour present; read the frames to judge
Look at: 01_start.png, 02_idle.png, 15_air.png
Verdict: PASS (reviewed: candy-stripe factory level with pads, can, lollipops, fan, sky; not a grid)

### 3. Player and goal objects visible and readable
Auto: AGENT - judge by reading the frames
Look at: 01_start.png, 02_idle.png, 15_air.png
Verdict: PASS (reviewed: green slime balloon with eyes reads clearly; striped exit pipe, gold pickup and pink hazards visible)

### 4. Input visibly moves the player (frames before and after input differ)
Auto: PASS - 10/11 input steps changed the picture: 15_air.png=63.4, 16_slit.png=53.8, 17_atwall.png=35.9, 18_climb1.png=62.1, 22_run0.png=55.2, 23_run1.png=59.6, 24_run2.png=49.2, 25_run3.png=16.9, 26_slot.png=49.0, 28_exit.png=0.5, 54_squash1.png=29.1 (idle baseline 0.4, needed >= 2.0)
Look at: 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 28_exit.png, 54_squash1.png
Verdict: PASS (reviewed: tiles 03-16 show jump, squeeze through slit with SPLIT, +25 SLIME, climb, run, reach pipe)

### 5. Proper HUD, no debug PrintString / warning text on screen
Auto: PASS - no debug-colour text, no debug words found
Look at: 01_start.png, 02_idle.png, 15_air.png, 16_slit.png, 17_atwall.png, 18_climb1.png, 19_climb2.png, 20_climb3.png, 21_climb4.png, 22_run0.png, 23_run1.png, 24_run2.png, 25_run3.png, 26_slot.png, 27_pass.png, 28_exit.png, 41_restarted.png, 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: HUD is mass counter plus controls line; no debug text; AMD Adrenalin popup in climb frames is the Legion driver, not the game)

### 6. A win or lose screen is reachable
Auto: AGENT - judge by reading the last frames; the sequence must have reached a win or lose screen
Look at: 54_squash1.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: YOU WIN! tiles 14-16 and YOU DRIPPED AWAY tile 19, both on dark backdrop boxes clear of the player)

### 7. Restart works (the restarted frame is a fresh start, not the end screen)
Auto: WARN - restarted frame vs first frame differ by 17.5 (limit 12.0); vs the frame before restart 28.1 (needs >= 2.0)
Look at: 01_start.png, 55_squash2.png, 68_restarted2.png
Verdict: PASS (reviewed: after R the slime is back on the start platform, mass 100; the pixel diff is the taskbar in frame 01 only)

### 8. Idle stability: with no input the view holds still (no looping camera, falling camera or flicker)
Auto: PASS - midplay: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.5 | win: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.1 | afterrestart: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.4 | lose: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.2 | afterrestart2: PASS - 12 frames, mean step 0.1, biggest step 0.1, drift from first 0.5
Look at: contact_midplay.png, contact_win.png, contact_afterrestart.png, contact_lose.png, contact_afterrestart2.png
Verdict: PASS (reviewed: idle bursts mean step 0.1 in midplay, win and restart; no drift or flicker)

## Step review (prefilled from the harness; resolve every AGENT, WARN and FAIL)

#### Step 01: start, t=22.35s (contact_steps_1.png, tile 1; 01_start.png)
Auto: FAIL
Verdict: PASS (override: taskbar visible only because the game starts windowed behind it; real capture of the start platform)

#### Step 02: idle, t=24.14s (contact_steps_1.png, tile 2; 02_idle.png)
Auto: FAIL
Verdict: PASS (override: same reason as step 01)

#### Step 03: air, t=30.36s (contact_steps_1.png, tile 3; 15_air.png)
Auto: AGENT
Verdict: PASS (reviewed: slime airborne over first platform)

#### Step 04: slit, t=31.75s (contact_steps_1.png, tile 4; 16_slit.png)
Auto: PASS
Verdict: PASS

#### Step 05: atwall, t=33.46s (contact_steps_1.png, tile 5; 17_atwall.png)
Auto: PASS
Verdict: PASS

#### Step 06: climb1, t=35.36s (contact_steps_1.png, tile 6; 18_climb1.png)
Auto: PASS
Verdict: PASS

#### Step 07: climb2, t=36.98s (contact_steps_1.png, tile 7; 19_climb2.png)
Auto: PASS
Verdict: PASS

#### Step 08: climb3, t=38.62s (contact_steps_1.png, tile 8; 20_climb3.png)
Auto: PASS
Verdict: PASS

#### Step 09: climb4, t=40.28s (contact_steps_2.png, tile 1; 21_climb4.png)
Auto: PASS
Verdict: PASS

#### Step 10: run0, t=41.15s (contact_steps_2.png, tile 2; 22_run0.png)
Auto: PASS
Verdict: PASS

#### Step 11: run1, t=42.94s (contact_steps_2.png, tile 3; 23_run1.png)
Auto: PASS
Verdict: PASS

#### Step 12: run2, t=44.76s (contact_steps_2.png, tile 4; 24_run2.png)
Auto: PASS
Verdict: PASS

#### Step 13: run3, t=46.56s (contact_steps_2.png, tile 5; 25_run3.png)
Auto: PASS
Verdict: PASS

#### Step 14: slot, t=49.64s (contact_steps_2.png, tile 6; 26_slot.png)
Auto: PASS
Verdict: PASS

#### Step 15: pass, t=51.8s (contact_steps_2.png, tile 7; 27_pass.png)
Auto: PASS
Verdict: PASS

#### Step 16: exit, t=54.97s (contact_steps_2.png, tile 8; 28_exit.png)
Auto: PASS
Verdict: PASS

#### Step 17: restarted, t=65.55s (contact_steps_3.png, tile 1; 41_restarted.png)
Auto: PASS
Verdict: PASS

#### Step 18: squash1, t=74.94s (contact_steps_3.png, tile 2; 54_squash1.png)
Auto: AGENT
Verdict: PASS (reviewed: SPLIT! with mass 50, slime squashed flat, blob visible)

#### Step 19: squash2, t=81.13s (contact_steps_3.png, tile 3; 55_squash2.png)
Auto: WARN
Verdict: PASS (reviewed: YOU DRIPPED AWAY, mass 0, readable on dark box)

#### Step 20: restarted2, t=90.67s (contact_steps_3.png, tile 4; 68_restarted2.png)
Auto: WARN
Verdict: PASS (reviewed: fresh start, mass 100)

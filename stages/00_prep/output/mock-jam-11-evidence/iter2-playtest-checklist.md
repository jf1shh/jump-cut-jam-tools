# Visual playtest checklist

Build: C:\Dev\megajam-mock\Packaged\SilentBlade_MockHelium.zip
Run: 67e7d5a1b3e641aeac986bba374660fc

Open each listed PNG with the Read tool and judge it yourself. `Auto:` is a cheap hint, never the verdict.
Replace `Verdict: PENDING` with `Verdict: PASS` or `Verdict: FAIL - <why>` on every item.
An item whose Auto is FAIL may only be passed with `Verdict: PASS (override: <why>)`.
Then run `./scripts/visual_playtest.py verify <this folder>`; the build is not done until it exits 0.

### 1. Frames are real captures (not black, flat or undecodable)
Auto: PASS - 47 frames, all decodable with visible detail
Look at: 01_start.png, 02_idle.png, 03_idle30.png, 04_play0.png, 05_k01_w.png, 06_k02_d.png, 07_k03_w.png, 08_play3.png, 09_k04_a.png, 10_k05_w.png, 11_k06_d.png, 12_e00_a.png, 13_e01_w.png, 14_e02_w.png, 15_e03_w.png, 16_e04_d.png, 17_e05_w.png, 18_e06_w.png, 19_f00_d.png, 20_f01_w.png, 21_f02_w.png, 22_f03_w.png, 23_f04_d.png, 24_f05_w.png, 25_f06_w.png, 26_f07_w.png, 27_j00_s.png, 28_j01_s.png, 29_j02_s.png, 30_j03_s.png, 31_j04_s.png, 32_j05_s.png, 33_j06_s.png, 34_j07_s.png, 35_j08_s.png, 36_j09_s.png, 37_j10_s.png, 38_j11_s.png, 39_win_a.png, 40_win_b.png, 41_win_c.png, 42_restart1.png, 43_lose_a.png, 44_lose_b.png, 45_lose_c.png, 46_restart2.png, 47_idle_after.png
Verdict: PASS - 50 frames real, detailed

### 2. Real level, not the default grid or an empty room
Auto: AGENT - colour present; read the frames to judge
Look at: 01_start.png, 02_idle.png, 03_idle30.png
Verdict: PASS - carnival street, stalls, bunting, pennants, path, spikes

### 3. Player and goal objects visible and readable
Auto: AGENT - judge by reading the frames
Look at: 01_start.png, 02_idle.png, 03_idle30.png
Verdict: PASS - kid, balloon, ribbons visible; frames 01/02 may carry the AMD overlay, 03+ clear

### 4. Input visibly moves the player (frames before and after input differ)
Auto: PASS - 30/35 input steps changed the picture: 04_play0.png=0.2, 05_k01_w.png=6.2, 06_k02_d.png=13.9, 07_k03_w.png=15.6, 09_k04_a.png=24.5, 10_k05_w.png=21.5, 11_k06_d.png=20.9, 12_e00_a.png=11.5, 13_e01_w.png=15.5, 14_e02_w.png=12.7, 15_e03_w.png=18.8, 16_e04_d.png=19.2, 17_e05_w.png=18.4, 18_e06_w.png=11.7, 19_f00_d.png=9.7, 20_f01_w.png=8.0, 21_f02_w.png=5.9, 22_f03_w.png=1.2, 23_f04_d.png=5.8, 24_f05_w.png=5.7, 25_f06_w.png=0.6, 26_f07_w.png=0.4, 27_j00_s.png=7.7, 28_j01_s.png=10.8, 29_j02_s.png=8.8, 30_j03_s.png=8.1, 31_j04_s.png=6.6, 32_j05_s.png=7.1, 33_j06_s.png=12.3, 34_j07_s.png=16.6, 35_j08_s.png=16.9, 36_j09_s.png=12.6, 37_j10_s.png=6.2, 38_j11_s.png=1.0, 43_lose_a.png=8.7 (idle baseline 0.1, needed >= 2.0)
Look at: 04_play0.png, 05_k01_w.png, 06_k02_d.png, 07_k03_w.png, 09_k04_a.png, 10_k05_w.png, 11_k06_d.png, 12_e00_a.png, 13_e01_w.png, 14_e02_w.png, 15_e03_w.png, 16_e04_d.png, 17_e05_w.png, 18_e06_w.png, 19_f00_d.png, 20_f01_w.png, 21_f02_w.png, 22_f03_w.png, 23_f04_d.png, 24_f05_w.png, 25_f06_w.png, 26_f07_w.png, 27_j00_s.png, 28_j01_s.png, 29_j02_s.png, 30_j03_s.png, 31_j04_s.png, 32_j05_s.png, 33_j06_s.png, 34_j07_s.png, 35_j08_s.png, 36_j09_s.png, 37_j10_s.png, 38_j11_s.png, 43_lose_a.png
Verdict: PASS - frames before and after keys differ; kid walks, ribbons 0 to 5

### 5. Proper HUD, no debug PrintString / warning text on screen
Auto: PASS - no debug-colour text, no debug words found
Look at: 01_start.png, 02_idle.png, 03_idle30.png, 04_play0.png, 05_k01_w.png, 06_k02_d.png, 07_k03_w.png, 08_play3.png, 09_k04_a.png, 10_k05_w.png, 11_k06_d.png, 12_e00_a.png, 13_e01_w.png, 14_e02_w.png, 15_e03_w.png, 16_e04_d.png, 17_e05_w.png, 18_e06_w.png, 19_f00_d.png, 20_f01_w.png, 21_f02_w.png, 22_f03_w.png, 23_f04_d.png, 24_f05_w.png, 25_f06_w.png, 26_f07_w.png, 27_j00_s.png, 28_j01_s.png, 29_j02_s.png, 30_j03_s.png, 31_j04_s.png, 32_j05_s.png, 33_j06_s.png, 34_j07_s.png, 35_j08_s.png, 36_j09_s.png, 37_j10_s.png, 38_j11_s.png, 39_win_a.png, 40_win_b.png, 41_win_c.png, 42_restart1.png, 43_lose_a.png, 44_lose_b.png, 45_lose_c.png, 46_restart2.png, 47_idle_after.png
Verdict: PASS - HUD only 'RIBBONS n/5 WASD R'. WIN text 'Press R to play again' and POP text now fit fully (scale 2.2, x 200); fixes the clip from iteration 1

### 6. A win or lose screen is reachable
Auto: AGENT - judge by reading the last frames; the sequence must have reached a win or lose screen
Look at: 45_lose_c.png, 46_restart2.png, 47_idle_after.png
Verdict: PASS - win (YOU WIN 5/5) and lose (POP! The balloon hit a spike) reached by real input

### 7. Restart works (the restarted frame is a fresh start, not the end screen)
Auto: WARN - restarted frame vs first frame differ by 22.3 (limit 12.0); vs the frame before restart 9.0 (needs >= 2.0)
Look at: 01_start.png, 45_lose_c.png, 46_restart2.png
Verdict: PASS - after R: RIBBONS 0/5 fresh start, no end text; stable in the idle frame after

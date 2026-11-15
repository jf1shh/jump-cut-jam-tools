# Jump Cut: greybox layouts (a metric sheet per scene)

2026-11-11, pre-jam planning text only (Rule 7(h)): numbers, tables and ASCII sketches. No level, asset or code exists
before 21:00 PT. [`../gdd.md`](../gdd.md) wins. Stunt ids, `T` values, lanes and tiers come from
[`storyboards.md`](storyboards.md); starting numbers from [`README.md`](README.md) "Shared anchors" and "Starting
numbers"; the set look from [`style-guide.md`](style-guide.md) section 6. Anything new is **Proposal**. The format
follows `_config/reference/canon/jam-level-layout-spec.md`: numbers first, handedness stated, a metric sheet the build
must obey.

**Scope.** Where things stand along and across the road, for Scene 1 "Rehearsal", Scene 2 "The Chase" and Scene 3
"The Finale". Hazard motion curves and the stunt rows belong to `data-schema.md` (written in parallel); this sheet uses
the same ids (S1-1 ... S3-10). If a row there disagrees with a distance here, the speed curve on the DataAsset wins and
this sheet is re-derived (section 1.3). Every distance below was computed by script from the formulas in 1.3.

## 1. Shared metrics (all three scenes)

### 1.1 Axes and handedness

- **Units:** metres here; UE units are cm (X in cm = 100 x metres). One straight level per scene (Proposal names
  `L_Scene01`, `L_Scene02`, `L_Scene03`, per `CLAUDE.md` and the jam-night runbook).
- **X** runs along the track, forward = +X, the start line at X = 0. **Y** runs across: the road centre line is Y = 0.
  **Z** is up, road surface Z = 0.
- **Top view (handedness note from the layout spec):** +X is to the **right** of the page, +Y is **down** the page.
  Facing +X, +Y is the driver's right. So lane **L is the top row** (-Y), lane **R the bottom row** (+Y). UE is
  left-handed. The editor top camera that matches every sketch below is pitch -90, **yaw -90**; at yaw 0 the view looks
  rotated 90 degrees. Check the first built road against this before placing anything else.
- The car follows the spline along Y = 0 plus a lane offset (GDD section 7). `s` is the car's centre. The car is 4.2 m
  long (style guide section 5); ignore its 2.1 m nose offset when placing hazards (inside the rounding).

### 1.2 Cross-section (the same in every scene)

| Item | Y or size (m) | Note |
|---|---|---|
| Lanes L / C / R | -6..-2 / -2..+2 / +2..+6 (centres -4 / 0 / +4) | 4 m each (README). The car starts in C |
| Lane lines | at Y = +-2, dashed white, 4 m dash, 4 m gap, 0.15 m wide | Proposal: 8 m period = 2.25 dashes a second at 18 m/s, 3.25 at 26 m/s, 4 in the 32 m/s surge |
| Road edge and kerb | solid line at Y = +-6; kerb 0.15 m high | |
| Sidewalk | the 4 m from abs(Y) 6 to 10 | mark signs and the replay A and C cameras sit here |
| Building line | abs(Y) = 10 | fronts and flats stand here; hazards that fall onto the road hinge here |
| Backstage void | set flats end at abs(Y) 40; near-black beyond | fog hides the edge (style guide section 4) |
| Car in a lane | 1.9 m wide, so 1.05 m of room each side | style guide section 5; see F3 for what that means for the tiers |
| Mark strip | Y -6..+6, 0.5 m along X, flush with the road, `#FFC93C` | README "the mark"; the car's centre stops on it |
| Mark sign | board 1.0 m wide x 1.5 m tall on a post at Y +7.5, facing the road, shows the mark number | README "small clapperboard sign" |
| Clear zone at a mark | X +-15 m, except S3-9 (+-10 m, the fire trench ends 10 m before `M3-9`): nothing on the road, nothing within 2 m of it on the sidewalk | GDD section 3 "clear zone"; the 15 m and 10 m are Proposals |
| Hazard box rule | a hazard's box ends on a lane line (Y = +-2 or +-6), never inside the next lane | see flag F3 |
| Key light per hazard | one light at the piece, Z 6 m, on the side the hazard comes from, scene key colour; on at the telegraph | GDD section 7, style guide section 4 |

### 1.3 Distance from time

Hazards and the car are functions of scene time `T`. The car's distance `s(T)` is the integral of the speed curve
`f(T)`, and every stunt sits at its collision-on distance **D = s(T)**. The starting speed model (README "Starting
numbers"): base speed from `T` = 0 (no launch ramp: `T` 0 at X 0 is the car crossing the start line at base speed; the idle at the slate and any ease-in happen behind the line at X < 0, so no anchor moves), plus a step of +6 m/s for the 3 s before the set piece's
collision-on line.

| Scene | Base (m/s) | Surge window (`T`, X) | s(T) |
|---|---|---|---|
| 1 | 18 | 32 to 35 (X 576 to 648), before S1-6 | 18 T to T 32; 24 m/s to T 35; then 18 T + 18 |
| 2 | 22 | 43 to 46 (X 946 to 1030), before S2-9 | 22 T to T 43; 28 m/s to T 46; then 22 T + 18 |
| 3 | 26 | 52 to 55 (X 1352 to 1448), before S3-9 | 26 T to T 52; 32 m/s to T 55; then 26 T + 18 |

The surge adds 18 m to every position after it. A 0.5 s ease on each side of the step would pull later positions back
by about 3 m. If the curve is tuned, re-run the numbers; do not hand-edit distances.

Derived points (same rules in every scene):

| Point | Rule | Source |
|---|---|---|
| Telegraph start | s(T - 2.5): the key light snaps on and the cut window opens | storyboards "Spacing"; onboarding O2 |
| Cut window | telegraph start to D (closes at collision-on) | GDD section 3 |
| Mark k | s(T_end + 2), where T_end is `T` (a point stunt) or the end of the span (a MustCut). It is the landing for cutting stunt k and the restart for stunt k+1. Mark 0 is the start line | GDD section 3; storyboards (DataAsset default 2 s) |
| Crash restart | the previous mark: its X, lane C, scene time back to that mark's `T` | GDD section 4; lane C is a Proposal |
| Wrap line | the last stunt's mark | README decision 11 |
| Landing after a MustCut | `M1-4` (`T` 26) and `M3-4` (`T` 32) are past the end of the collapse (`T` 24, `T` 30), so the clock jumps past it. The collapse shows in the replay; the live view keeps a debris and dust tail past the span end | storyboards Board 4; the tail is a Proposal |
| Mark and stunt ids | marks are `M<scene>-<k>` (`M1-0` is the start line); stunt ids as in storyboards | Proposal |

### 1.4 Cameras (starting values, all Proposal; roles from style guide section 7)

| Camera | Where | Notes |
|---|---|---|
| Chase (play and hold) | 7 m behind the car, 3.0 m above the road, aimed at a point 12 m ahead of the car at 1.0 m (pitch about -6 degrees); FOV 80 | follows 60% of the car's lateral offset with a 0.3 s lag, so abs(Y) never passes 2.4 m; at 20 m ahead it sees 33 m across, enough for the 12 m road |
| Landing inset (SceneCapture, runs only in the hold) | 12 m before the next mark, Y 0, Z 4.5 m, pitch -14 degrees, FOV 70 | moved to the next mark when the hold starts; sees 17 m across at the mark, so the whole road plus the ghost car |
| Replay A, low side-tracking | rail at Y = +-7.5 on the side away from the hazard's origin, Z 0.6 m, 4 m behind the car, FOV 50 | keeps pace from `T` - 2.5 to `T` + 1.5 |
| Replay B, high crane wide | X = D + 20, Y = +-10 on the side away from the hazard, Z 12 m, aimed at (D - 8, 0, 1) | looks back at the car and the hazard |
| Replay C, locked-off at the mark | X = mark + 10, Y +8.5, Z 1.2 m, aimed at (mark - 8, 0, 1) | the car arrives into frame; the mark sign is out of shot |
| Wrap (locked wide) | X = wrap - 20, Y +9, Z 5 m, aimed at (wrap + 10, 0, 1), FOV 60 | the car rolls past and stops inside the run-out |

### 1.5 Road, filler and silhouettes

- **Road:** X from -40 (start lot: board, lamps, chase-cam room) to wrap + 40 (run-out). The car eases to a stop in 2 s
  from base speed, which takes 18 / 22 / 26 m, so it stops well inside the run-out.
- **Filler module (Proposal):** 40 m of road, kerbs, sidewalks, one set flat per side and one lamp stand, instanced along
  X every 40 m with the scene's `MI_Set_*`. It covers every stretch that holds no hero piece. Only hero pieces are
  built one by one.
- **Dress only what is seen:** about 250 m ahead of the car and 40 m behind (Proposal), with the scene fog low
  (style guide section 4). Silhouette pieces are the exception: each must read from the start (checked in each scene).

## 2. Scene 1 "Rehearsal" (Main Street backlot)

| Item | Value |
|---|---|
| Track | start line X 0 to wrap line X **684** (37 s). Road X -40 to 724 (764 m, 19 filler modules) |
| Speed | 18 m/s; 24 m/s from `T` 32 to 35 (X 576 to 648) |
| Start | car centre on `M1-0` at X 0, lane C; slate over the start line; chase camera at X -7 |
| Wrap | `M1-6` at X 684 (`T` 37); the car stops by X 702 |
| Look | amber `#FFB04A`; plywood fronts 8 m tall on both building lines, scaffold braces behind them (4 m deep); painted shopfronts on the sidewalks; calm and wide |

### Stunt anchors (computed)

| Stunt | `T` (s) | D: collision-on (m) | Telegraph (m) | Mark: `T` s / X m | Lanes blocked | Comes from | Box X (m) |
|---|---|---|---|---|---|---|---|
| S1-1 | 7 | 126 | 81 | 9 / 162 | C R | right | 126-134 |
| S1-2 | 12 | 216 | 171 | 14 / 252 | L C | left alley | 216-219 |
| S1-3 | 17 | 306 | 261 | 19 / 342 | L C R | right (crane) | 306-314 |
| S1-4 | 22-24 | 396 | 351 | 26 / 468 | L C R | left (tower) | 396-432 |
| S1-5 | 30 | 540 | 495 | 32 / 576 | C R | right | 540-552 |
| S1-6 | 35 | 648 | 588 | 37 / 684 | L C R | both sides | 648-660 |

Box = where the hazard's collision volume sits along X (D to D + length). The long box on S1-4 is the 2 s fall at 18 m/s.

### Pieces to place

| Stunt | Greybox piece and where (m; sizes X x Y x Z) |
|---|---|
| S1-1 | False-front panel 8 x 0.3 x 12, foot on the right building line (X 126-134, Y +10). Falls toward -Y and lies on Y -2..+10 (C, R, sidewalk). Scaffold braces behind it. Amber spot behind the panel |
| S1-2 | Prop truck 8 x 2.6 x 3, parked in a left alley (a 9 m gap in the left front row, X 213-222). It noses out and stops across L and C (Y -6..+2) at X 216-219. White headlamp cone |
| S1-3 | Crane base on the right sidewalk (X 310, Y +9), arm 14 m at Z 12. Lamp truss 8 x 0.6 x 1 hangs 0.4-1.4 m above the road and sweeps from Y +6 to Y -6 over X 306-314 (R to L). The truss's lamps are the key light |
| S1-4 | **Water tower**, 22 m tall (4 legs 10 m, tank 6 m wide x 6 m), base at X 414, Y -14, behind a 12 m gap in the left front row (X 408-420). Falls toward +Y and lies on Y -14..+8. Blocker box X 396-432, Y -6..+6. Brighter amber. Always on the skyline |
| S1-5 | Flatbed 8 x 2.5 x 1.5 at the right kerb (X 534-542, Y +7.5). Six barrels (0.9 wide x 1.2 tall) roll toward -Y over X 540-552 across R and C and stop at Y -2 |
| S1-6 | Left facade 12 x 0.3 x 12 hinged at Y -10 (lies on Y -10..+2) and right scaffold tower 12 x 4 x 12 hinged at Y +10 (lies on Y -2..+10), both over X 648-660. They overlap in C; the gap that travels L to C to R is curve data |

### Cameras and dressing

- **Chase:** the standard rig. FOV 80 widens to 88 over the surge (`T` 32 to 35, X 576 to 648) and is back by `T` 36
  (storyboards "slight FOV widen").
- **Replays:** angles as in storyboards. Cranes (Z 12) clear the 8 m fronts everywhere. Replay B for S1-4 stands at X 452
  (past the 36 m wreck zone, on the right side).
- **Start lot (X -40 to 0):** strip and sign `M1-0`, two lamp stands (X -20, Y +-9), a boom-mic stand at the left edge,
  a black flat across the road end at X -40.
- **Lead-in (X 0 to 81):** filler only. 4.5 s of free road for the lane feel, nothing to read.
- **Lamp stands:** on the sidewalk at abs(Y) 9 (in front of the 8 m fronts), every 80 m, alternating sides; bright shapes, not shadow lights.
- **Wrap lot (X 684 to 724):** camera crane base at X 664 (Y +9) for the wrap shot, a plywood backlot wall 60 m wide x 10
  m tall at X 726 to close the road.
- **Silhouette:** the tower (22 m at 414 m from the start line) is about 3 degrees tall from X 0. Rim-light it and keep
  the fog thin enough that it reads.

### Top view (20 m per character; +X right, +Y down)

```
        0    100  200  300  400  500  600  700
        |    |    |    |    |    |    |    |
Y-10  ############2########444##########66#######
Y -4  ............2....3...444..........66.......
Y  0  ........1...2....3...444.....5....66.......
Y +4  ........1........3...444.....5....66.......
Y+10  ########1########3###########5####66#######
surge                               ~~~~~
marks   0       1   2    3     4    5     6
```

## 3. Scene 2 "The Chase" (day-for-night city street)

| Item | Value |
|---|---|
| Track | start line X 0 to wrap line X **1074** (48 s). Road X -40 to 1114 (1154 m, 29 filler modules) |
| Speed | 22 m/s; 28 m/s from `T` 43 to 46 (X 946 to 1030) |
| Start | car centre on `M2-0` at X 0, lane C; slate over the start line; chase camera at X -7 |
| Wrap | `M2-9` at X 1074 (`T` 48), 44 m past the crossing; the car stops by X 1096 |
| Look | steel-blue `#5B86C9` with sodium pools `#FF9A3C`; apartment flat kit on the left, shopfront flat kit on the right, flats 14 m tall; wet-looking road (a value trick); lit windows as emissive squares |

### Stunt anchors (computed)

| Stunt | `T` (s) | D: collision-on (m) | Telegraph (m) | Mark: `T` s / X m | Lanes blocked | Comes from | Box X (m) |
|---|---|---|---|---|---|---|---|
| S2-1 | 6 | 132 | 77 | 8 / 176 | C R | right alley | 132-135 |
| S2-2 | 11 | 242 | 187 | 13 / 286 | L C R | right (crane) | 242-246 |
| S2-3 | 16 | 352 | 297 | 18 / 396 | L | above L (hook) | 352-355 |
| S2-4 | 21 | 462 | 407 | 23 / 506 | L C | left | 462-468 |
| S2-5 | 26 | 572 | 517 | 28 / 616 | L C R | right | 572-584 |
| S2-6 | 31 | 682 | 627 | 33 / 726 | C R | right | 682-688 |
| S2-7 | 36 | 792 | 737 | 38 / 836 | L C | left | 792-796 |
| S2-8 | 41 | 902 | 847 | 43 / 946 | L R | above (drops) | 902-905 |
| S2-9 | 46 | 1030 | 960 | 48 / 1074 | L C R | right (train) | 1030-1037 |

### Pieces to place

| Stunt | Greybox piece and where (m; sizes X x Y x Z) |
|---|---|
| S2-1 | Truck 8 x 2.6 x 3 from a right alley (9 m gap in the right front row, X 129-138). Stops across C and R (Y -2..+6) at X 132-135. Cold headlight cone |
| S2-2 | Crane on a tracked base, right sidewalk (X 242, Y +9), boom 16 m high. Ball 2.5 wide on a 12 m cable swings in the Y-Z plane through X 242-246, from Y +6 to Y -6 (R to L), low point 1 m above the road. Orange pool on the arc |
| S2-3 | Crane hook above L (X 352, Y -4). Crate 2.5 cube hangs at Z 8, sways, drops onto L (X 352-355). Hard top light at Z 14 over the hook so the shadow grows on L |
| S2-4 | Scaffold tower 6 x 4 x 12 on the left sidewalk (X 462-468, Y -9). Falls toward +Y and lies on Y -10..+2 (L, C) |
| S2-5 | Flatbed 8 x 2.5 x 1.5 at the right kerb (X 572-580, Y +8). Five pipes (1.8 wide x 3 long) roll diagonally toward -Y and +X over X 572-584: R, then C, then L |
| S2-6 | Camera car 5 x 2 x 1.6 from a side-street gap in the right front row (X 679-685). Swerves from Y +6 into C. On a near-miss the replay C is a camera on this prop, aimed back at the hero car |
| S2-7 | Fruit cart 3 x 1.6 x 1.5 at the left kerb (X 792-796, Y -7). Rolls into L and C (to Y +1). Fruit bursts (Niagara) on a hit |
| S2-8 | Two sawhorse barricades, each 4 x 0.8 x 1.2, drop from 6 m onto L (Y -6..-2) and R (Y +2..+6) at X 902-905. C stays clear for the whole stunt, so every C pass scores the same tier (accepted: it is an easy stunt) |
| S2-9 | Rail bed across the road at X 1030-1037. Train cars 3.4 (X) x 12 (Y) x 4 move from Y +10 toward -Y; the safe gap between the last two cars sweeps R to L. Crossing lamps and bell post at X 1020 (Y +-8). **Trestle** deck 40 x 18 x 1.5 over X 1015-1055 with its underside at Z 10, legs at X 1015 and 1055 on both sidewalks (Y +-8) |

### Cameras and dressing

- **Chase:** the standard rig. It passes under the trestle (underside Z 10, camera Z 3) with room to spare. FOV 80
  widens to 88 over the surge (`T` 43 to 46, X 946 to 1030).
- **Replays:** S2-9 uses angle C only (storyboards), so no crane (Z 12) ever enters the trestle span; replay C for S2-9
  stands at X 1084, past the trestle, and looks back through the underpass at the crossing. Replay B for S2-8 stands at
  X 922, well clear of it.
- **Start lot (X -40 to 0):** strip and sign `M2-0`, soundstage floor edge, two lamp stands, a boom-mic stand at the left
  edge (the mic swings into the frame corner).
- **Filler:** apartment flat left, shopfront flat right, alternating by module; a lamp post at abs(Y) 9 every 40 m with an
  emissive sodium pool on the road (a decal, not a light).
- **Camera crane on a tracked base:** one static dressing piece at X 500, Y -12, rails along X.
- **Silhouette:** the trestle is 12 m tall, so it reads only from about X 800. Optional and cheap: one flat cutout of it
  at 3x scale at X 1250, Y -60, so it is on the horizon from the start.
- **Wrap lot (X 1074 to 1114):** the standard wrap camera (X 1054) would sit inside the trestle span, so it moves to X 1062,
  Y +10, Z 5, clear of the leg at X 1055; a flat across the road end at X 1116.

### Top view (20 m per character; +X right, +Y down)

```
        0    100  200  300  400  500  600  700  800  900  1000 1100
        |    |    |    |    |    |    |    |    |    |    |    |
Y-10  ###################3#####4###############7####################
Y -4  ..............2....3.....4....55.........7.....8.....9........
Y  0  ........1.....2..........4....55....6....7...........9........
Y +4  ........1.....2...............55....6..........8.....9........
Y+10  ########1#####2###############55####6################9########
surge                                                  ~~~~~
marks   0       1     2    3     4    5     6    7     8     9
```

## 4. Scene 3 "The Finale" (fuel depot and timber bridge)

| Item | Value |
|---|---|
| Track | start line X 0 to wrap line X **1630** (62 s). Road X -40 to 1670 (1710 m, 43 filler modules) |
| Speed | 26 m/s; 32 m/s from `T` 52 to 55 (X 1352 to 1448) |
| Start | car centre on `M3-0` at X 0, lane C; slate over the start line; chase camera at X -7 |
| Wrap | `M3-10` at X 1630 (`T` 62), 52 m past S3-10's anchor; the car stops by X 1656 |
| Look | fire red-orange `#FF5A1F`; darker and denser: tank farm and pipes on the right, drum stacks and scaffold on the left; lanes and lamps stay clear |

### Stunt anchors (computed)

| Stunt | `T` (s) | D: collision-on (m) | Telegraph (m) | Mark: `T` s / X m | Lanes blocked | Comes from | Box X (m) |
|---|---|---|---|---|---|---|---|
| S3-1 | 6 | 156 | 91 | 8 / 208 | L C R | right | 156-166 |
| S3-2 | 11 | 286 | 221 | 13 / 338 | L C R | right | 286-291 |
| S3-3 | 16 | 416 | 351 | 18 / 468 | L C R | both sides | 416-422 |
| S3-4 | 21-30 | 546 | 481 | 32 / 832 | L C R | ahead (bridge) | 546-780 |
| S3-5 | 35 | 910 | 845 | 37 / 962 | C R | right | 910-920 |
| S3-6 | 40 | 1040 | 975 | 42 / 1092 | L C R | left | 1040-1044 |
| S3-7 | 45 | 1170 | 1105 | 47 / 1222 | L C R | left | 1170-1182 |
| S3-8 | 50 | 1300 | 1235 | 52 / 1352 | L C R | in the road (pits) | 1300-1303 |
| S3-9 | 55 | 1448 | 1368 | 57 / 1500 | L C R | in the road (C) | 1448-1490 |
| S3-10 | 60 | 1578 | 1513 | 62 / 1630 | L C R | right and left | 1578-1590 |

### Pieces to place

| Stunt | Greybox piece and where (m; sizes X x Y x Z) |
|---|---|
| S3-1 | Drum stack 8 x 2 x 3 on the right sidewalk (X 150-158, Y +8..+10). Two waves of drums (0.6 wide x 0.9 tall) roll toward -Y over X 156-166 |
| S3-2 | Burning wreck 5 x 2 x 1.4 (emissive + `NS_Fireball`) slides from the right sidewalk (X 286-291, from Y +10) across the road to Y -10. Its own fire light |
| S3-3 | Pipe manifolds with flame nozzles over X 416-422: left kerb nozzles at Y -7 fire toward +Y to Y +2 (L, C), right kerb nozzles at Y +7 fire toward -Y to Y +2 (R) |
| S3-4 | **Timber bridge**, 9 spans x 26 m = X 546-780, deck Y -6.6..+6.6 with 1.2 m rail posts at Y +-6.6, no sidewalks, ten bents at X 546 + 26 i. Deck at Z 0, ravine floor at Z -22, hot orange light from below. Span k covers X 546 + 26(k-1) to 546 + 26k and falls in order. The road resumes on the far bank at X 780. Planks creak from the telegraph (X 481, 65 m before the first bent) |
| S3-5 | Tanker: tractor on the right sidewalk (X 905, Y +8), trailer 10 x 2.5 x 3 hinged at its rear at (X 910, Y +8). Swings from along X to across Y and lies on Y -2..+8 (C, R) |
| S3-6 | Crane tower on the left (X 1040, Y -12), boom 20 m at Z 14 over the road. Hook block 2.5 x 2 x 3 swings low in the Y-Z plane through X 1040-1044 across all three lanes |
| S3-7 | Pipe rack 12 x 3 x 8 on the left sidewalk (X 1170-1182, Y -10..-7). Falls in two stages: first onto L, then onto C (ends on Y -10..+2). Loose pipes roll across L, C and R over X 1170-1182 just before the rack lands (`data-schema.md` S3-7b), so all three lanes are blocked in the zone |
| S3-8 | Three burner pits 3 x 3 x 0.3, centres Y -4, 0, +4, over X 1300-1303; flames 3 m high; they ignite R to L |
| S3-9 | (D = 1448) Burning wreck 5 x 2 x 1.4 in C (X 1448-1453). Clear 16 m (0.6 s at 26 m/s). Plywood ramp in C only (Y -2..+2): foot X 1469, lip X 1475, 6 m long, rise 1.5 m. Fire trench 12 x 12 over X 1478-1490, all lanes, flames 0.6 m. Arc (spline height, no physics): 18 m of flight (0.7 s), apex 2.0 m at X 1484, landing X 1493. Mark 9 is at X 1500. Collision box X 1448-1490: the wreck, the ramp (the drivable sub-piece, C only) and the fire trench (all lanes) |
| S3-10 | **Gas holder** (silhouette), 60 wide x 50 tall, centre X 1590, Y +45 (near face at Y +15), lattice glows. The fireball grows from its near face onto R, then C. A flare stack 3 x 3 x 25 at (X 1580, Y -12) sheds debris toward +Y over L. Box X 1578-1590 |

### Cameras and dressing

- **Chase:** the standard rig. On the bridge deck (abs(Y) 6.6) the camera's abs(Y) of 2.4 never reaches the rails. FOV widens
  to 88 over the surge (`T` 52 to 55). During the S3-9 arc the camera keeps Z at 3 + 40% of the car's height, so the car
  rises against the fire instead of the camera chasing it.
- **Replay B for S3-4:** a crane on the far bank at X 800, Y +16, Z 24, pitch -12 degrees, FOV 60, aimed down the bridge,
  so all nine spans fall away toward the lens (storyboards: "the whole collapse").
- **Replay C for S3-9 (exception):** storyboards say "mid-air side shot", not the locked-off mark view. Put C at X 1484
  (the apex), Y +9, Z 2.0, aimed at (1484, 0, 3). Every other C is the standard rig.
- **Start lot (X -40 to 0):** strip and sign `M3-0`, floodlight stands, a barrel stack; black flat at X -40.
- **Filler:** tank farm on the right (tanks 12 wide x 10 tall at Y +25, every 60 m), pipes along the right building line
  (Y +11, Z 4), drum stacks and scaffold on the left. A fake burning drum (emissive + `NS_Fireball`) at abs(Y) 9 every
  120 m, never on the road.
- **Far bank (X 780 to 832):** plain road, the landing for `M3-4`; the cut-landing camera shot sees the wreck behind.
- **Silhouette:** the gas holder (50 m tall at about 1590 m) is about 1.8 degrees tall from X 0; its lattice glow and
  rim light carry it. It is the scene's strongest rim light.
- **Wrap lot (X 1630 to 1670):** wrap-camera crane base at X 1610 (Y +9), a burnt-out flat wall across the road end at
  X 1672.

### Top view (20 m per character; +X right, +Y down)

```
        0    100  200  300  400  500  600  700  800  900  1000 1100 1200 1300 1400 1500 1600
        |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |
Y-10  ######################33##############################6#####77##################AA########
Y -4  .........11.....2.....33.....4444444444444............6.....77.....8......999...AA........
Y  0  .........11.....2.....33.....4444444444444.....55.....6.....77.....8......999...AA........
Y +4  .........11.....2.....33.....4444444444444.....55.....6............8......999...AA........
Y+10  #########11#####2#####33#######################55###############################AA########
surge                                                                      ~~~~~~
marks   0         1     2      3                 4      5     6      7     8       9     A
```

Legend for all three sketches: `#` is the building line (Y -10 and Y +10 rows); a digit is a stunt (`A` = stunt 10). Its digit sits in the lane rows it blocks at its box,
and in the Y -10 or Y +10 row for the side it comes from. `~` is the surge window. In the marks row, digit k is mark k
(`0` the start line, `A` mark 10). Bridge = the long run of 4s in Scene 3. The ruler is in metres.

## 5. Checks run and flags

**Checks (script, all pass):**

1. **No landing inside 2 s of a hazard (GDD section 3):** every mark is at least 3.0 s (54-96 m) before the next
   stunt's collision-on line (4.0 s after the S1-4 MustCut).
2. **A cut lands before the next telegraph (storyboards):** every mark is 0.5 s (9-16 m) before the next telegraph; 1.5 s
   after S1-4 and 0.5 s after S3-4.
3. **Nothing overlaps:** from the end of a stunt's box to the next telegraph there are at least 36 m (S1), 43 m (S2) and
   53 m (S3) of clear road, except S3-9: its box (wreck, ramp and fire trench) ends at X 1490, 23 m before the S3-10
   telegraph at X 1513 (the landing at X 1493 is 20 m before it).
4. **Mark is at most about 5 s ahead at window open:** 4.5 s for all 23 non-MustCut stunts (3 for the two MustCuts: F1).
5. **Driving times match storyboards:** 37 s, 48 s, 62 s.
6. **The surge starts exactly on a mark in every scene** (S1 mark 5 at X 576, S2 mark 8 at X 946, S3 mark 8 at X 1352).
   So a crash on the set piece restarts the surge each time, and a cut that lands on that mark starts it on arrival.

**Flags and hub rulings (Fable gate by hub 101; nothing here changes the GDD):**

- **F1 (ruling: keep): marks for the two MustCuts are further than "about 5 s ahead" (GDD section 3).** S1-4: the mark is
  6.5 s ahead at window open (`M1-4` at `T` 26, the window opens at `T` 19.5). S3-4: the far bank `M3-4` is 13.5 s ahead
  at window open (351 m) and 11 s at the last moment (286 m), because the bridge span is 9 s long (storyboards). The 5 s is
  a readability cap on a choice; a MustCut offers none, and Board 4 already puts the landing past the wreck. The mark stays
  one formula, s(T_end + 2), with no special case. The inset camera is placed at the mark, so the distance costs nothing.
- **F2 (ruling: keep, all three first stunts): the first stunt of every scene restarts at the start line.** S1-1 goes
  back 7 s (126 m), S2-1 6 s (132 m) and S3-1 6 s (156 m); GDD section 4 says 2-5 s. S1-1 is the free crash and the
  prompt stunt. There is no extra restart point: mark 0 is the start line and the GDD has exactly one mark per stunt.
  Every other crash goes back 3 s (54-96 m), or 4 s (72 m) from S1-5 after the S1-4 MustCut.
- **F3 (ruling: keep the lane-line snap, change the band).** Hazard boxes end on a lane line, one rule for every stunt
  (lanes stay data rows; hazards are not shrunk per stunt). A 1.9 m car centred in a 4 m lane is 1.05 m from such an edge.
  With the README's CLOSE band of 1.5 m that is already CLOSE, so WIDE would be rare. Starting value on the DataAsset
  (Proposal, replaces the README's 1.5 m, which was itself a DataAsset Proposal): **CLOSE at 1.0 m or less**, PERFECT at
  0.6 m or less unchanged, both measured on the collision box. A centred car beside a lane-line edge then scores WIDE;
  CLOSE and PERFECT come from crossing late. Greybox acceptance: each stunt can score all three tiers.
- **S3-9 is a tight fit, not a flag:** the 16 m clear gap, ramp, 18 m of flight and a landing 7 m before `M3-9` all sit
  inside the 52 m from D to the mark. If the ramp costs more than 30 minutes, flatten it (storyboards): keep the wreck
  and the 16 m gap, drop the ramp and the trench; nothing else moves.

## 6. How to build it (Proposal, after 21:00 PT)

1. Lay the road spline along +X; place the filler module N times (19 / 29 / 43) and the start lot.
2. One editor Python script (the MCP has no Python tool; see the layout-spec README step 6) reads the speed curve and the
   stunt list from the DataAsset and spawns an empty `Anchor_<id>` at X = D x 100, plus `M<scene>-<k>` at each mark.
   Anchors are data-driven, so tuning the curve never means moving things by hand.
3. Place each piece in section "Pieces to place" relative to its anchor (X offset from D, Y as written).
4. Compare the top view (pitch -90, yaw -90) with the ASCII sketch, and read three anchors per scene against the
   tables (within 1 m). Then run the determinism test (GDD section 8) before any package.

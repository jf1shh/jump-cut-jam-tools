# Mechanic prompts (state axis and units)

Rule: say the motion, the axis, the unit and the input. "Make the door open" is the bad form;
the good form below is the claim from the videos (UNTESTED here). One mechanic per prompt, primitives only
(cube, sphere, cylinder; flat colour materials). End each turn with: launch the build, take a screenshot, report.

Fill `<...>` before sending. Unreal: +X forward, +Y right, +Z up, centimetres, degrees, seconds.

1. **Slide door:** "Cube `BP_Door_<n>`, size <w>x<d>x<h> cm. On `<key>` within <r> cm, slide it along <+/-axis> by <dist> cm in <t> s, ease out. Press again to close. Expose dist, t, r on the Settings actor."
2. **Pickup:** "Sphere radius <r> cm. On overlap with the player, hide it, add <n> to `<counter>`, fire the event `OnPickup`. No sound or particles yet."
3. **Lever:** "Cylinder handle, rotate <deg> degrees about <axis> in <t> s on `<key>` within <r> cm. Fire `OnLeverChanged(bool)`."
4. **Hazard zone:** "Box volume <w>x<d>x<h> cm. While the player overlaps, deal <dmg> HP per <interval> s. Player has <max> HP."
5. **Death and restart:** "At 0 HP stop input, show text `<label>`, after <t> s reload the level and reset every counter."
6. **Win condition:** "When `<counter>` reaches <n>, stop input, show text `<label>`, offer `<key>` to restart."
7. **Jump:** use the numbers from the feel spec, do not invent them: "Jump apex <h> cm, time to apex <t> s, gravity <g> cm/s^2, coyote time <c> s, jump buffer <b> s."
8. **Move:** "Max speed <v> cm/s, ground accel <a> cm/s^2, deceleration <d> cm/s^2, air control <0-1>."
9. **Camera cut:** "On `<event>` switch to camera `<name>` for <t> s, then back, with no blend."
10. **Commitment cost:** "While `<action>` runs (<t> s) the player cannot `<move/attack>`. Cancel window opens <t2> s after the hit frame." (UNTESTED lesson 2.10.)

Checks to add to the playtest: spam the action (exploit?), stuck-enemy timeout.

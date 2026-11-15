# One Settings actor and a test room (UNTESTED, lessons 2.6, 2.7)

## Settings actor prompt
"Create `BP_Settings` (one per level) holding every tunable number from the feel spec as an exposed, categorised
property with a unit in its name or tooltip. Gameplay code reads only from it. For every new feel effect add a
bool `bEnable<Effect>`. Draw range gizmos and debug lines only while the actor is selected. Never hard-code a
number in a graph."
Measure in the mock run: how many tuning changes needed no new prompt.

## Test room prompt
"Build `L_TestRoom` from this list of mechanics: `<list>`. One bay per mechanic: a labelled floor plate, the
mechanic's primitives, a reset button. Add a warp menu (`<key>`) that teleports the player to each bay."
The playtest agent walks it bay by bay and writes a bug list; group the bugs before fixing.

## End of every agent turn
Launch the build, take a screenshot, state what to look at. Name the tool for each job in the brief.
Test room and mock content are practice-only unless rebuilt inside the contest window (Rule 7(h)).

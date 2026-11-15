---
tier: community
source: ~/Projects/superagent-sandbox/reports/stefan_3d_ai-megajam-lessons.md (lessons 2.1 to 2.5), RULES.md
updated: 2026-11-10
---

# Agent lint rules, verify traps and the pre-submit gate

These claims are 5.8-era and UNTESTED on 5.9; re-test on 5.9 before relying on them.

Every claim here comes from a video and is UNTESTED in this repo unless a line says it was run. The scripts
that check them were written and unit-tested with fake actors on 2026-11-09; none has run in the real editor yet.

## Tip: lint what agents do by default (lessons 2.3)
- **Why:** videos report agents using per-frame Tick, chained Delay nodes, legacy input, raw HLSL in materials,
  and a vague target ("box on the player's head" changed the placed actor, not the Blueprint class). UNTESTED here.
- **Three fixed lines for the lead-agent brief:** (1) overlap events or timers, never Tick; (2) Enhanced Input on
  UE 5.8; (3) name the Blueprint asset path, never "the player" or "the actor".
- **How to check:** `python3 scripts/ue_verify_level.py --lint DUMP.txt` on a text dump of a Blueprint graph;
  add `--brief` to lint a brief. Rules: `event-tick`, `delay-chain` (two or more Delay nodes), `legacy-input`,
  `raw-hlsl`, `vague-target`, `tick-ask`, `widget-binding`. Exit 1 if anything is flagged. The patterns match
  node names we guess (`K2Node_InputAxisEvent`, `K2Node_Delay`); they are UNTESTED against a real dump from
  `mx.py`, so run it once on a real graph dump and fix the patterns before trusting a clean result.
- Not scriptable from text, so by hand: a trigger box that no event references.

## Tip: verify traps (lesson 2.4)
- **Stale placed actors:** a video says Blueprint edits do not reach actors already placed. Rule: after editing a
  Blueprint, delete and respawn its placed actors. `ue_verify_level.py` flags them as `stale-actor` when you pass
  the edited class paths in `MJ_CHANGED_BPS` (comma list).
- **Zero defaults:** generated features with decal size 0 or a wrong impulse flag were reported. The verify run
  flags watched numeric properties (decal size, impulse, speed, damage, health, range, radius, scale) left at 0 as
  `zero-default`.
- **No collision:** a mesh with collision off breaks play silently. Flagged as `no-collision`; if the value cannot
  be read, `unknown-collision` (never counted as fine).
- **Widget binding:** a video says the agent could not bind a widget Blueprint through MCP. Build the HUD in C++ or
  Python. The brief lint flags "bind widget". There is no level-side check; the playtest shows whether the HUD appears.
- **Unverified list:** every builder report ends with an "Unverified" list, copied into the playtest gate.
- **How to check:** run `ue_verify_level.py` in the editor and read the `VERIFY_FINDING=` lines. All editor
  property reads in it are UNTESTED against UE 5.8.4 Python.

## Tip: workers write a result file, the lead polls it (lesson 2.5)
- **Why:** a video says sub-agents finished without reporting back, some stalled unseen for hours.
- **Pattern:** each worker writes `work/results/<job-id>.json` (`{"job", "status": "done|failed", "unverified": []}`)
  as its last act. The lead polls those files (`waitfor`, not a sleep loop). No file change for N minutes: ping the
  worker; no answer: save its unfinished work, restart it alone. One job per fresh session, and every job ends
  with a test. N is not measured; pick 10 minutes as a first guess and record what you see.
- **How to check:** a mock run where one worker is killed on purpose; the lead must notice inside N minutes. NOT RUN.

## Tip: the pre-submit gate (lesson 2.1)
- **Why:** mock 10 shipped a grey checker floor. A gate costs seconds.
- **How to check:** run the verify script in the editor, save its output, then
  `python3 scripts/presubmit_gate.py LOG`. Exit 0 pass, 1 a visible actor shows a default grid or checker
  material (an unassigned material slot counts), 2 a log that is empty, has no `VERIFY_DONE`, or whose record
  count differs from `VERIFY_ACTOR_COUNT` (never a pass). Hidden actors are ignored. Material markers: WorldGridMaterial,
  DefaultMaterial, "checker", "grid" (the last can false-positive on a custom `M_GridMask`; read the line).

## What the rules really say about grid textures and screening
The video claim (Emil Nielsen's prep stream, from an AI chat answer, not from the rules): Epic staff pre-screen
entries and drop any that fail to package, add no custom gameplay beyond a template, or show default grid textures.

Checked against our rules digest (`RULES.md`, v3; `jam-rules-cheatsheet.md` is a shorter digest of the same):
- No rule mentions grid or checker textures. Nothing says a default material disqualifies an entry.
- No rule describes a pre-screen. Searching the digest for screen, disqualif, reject, pre- finds only the
  eligibility and pre-jam-work sections.
- What does exist: the entry must package and run with no extra software (Rule 7(f)); it must not be an obvious
  extension of an Epic tutorial and must have custom gameplay beyond the starter templates (Rule 7(d), (e)); and
  Visuals and Level Design are two of the seven scored criteria (Rule 9, 1 to 5 each).
- So a grid floor is a scoring risk (Visuals), not a stated rule violation. A template with no custom gameplay is
  a stated risk under 7(d)/(e). Whether Epic screens before judging is not in the digest: UNTESTED.
- Limit of this check: it read the digest, not the Box PDF. Re-read the PDF on 2026-11-10 for Rule 7 and Rule 9.

## Measured on 2026-11-09 (hub 50, real UE 5.8 editor, old mock "MockSlime", one run each, n=1)
- **Verify + gate on the old mock:** level `/Game/Maps/L_MainLevel`, 47 actors, `VERIFY_DONE`, no findings. The
  gate on the raw log first exited 2 (UE prefixes each print with `[ts][n]LogPython: `); fixed, and the raw log
  now gives `GATE_PASS actors=47 violations=0`. A pass here only shows the gate runs end to end on a real log; it
  has not yet been shown to catch a real grid floor in the editor (the tests do, with fake actors).
- **Recipe:** level comes from env, not an argument:
  `MJ_VERIFY_LEVEL=/Game/Maps/L_MainLevel timeout 120 UnrealEditor-Cmd X.uproject -ExecCmds="py scripts/ue_verify_level.py" -unattended -nosplash -stdout -FullStdOutLogOutput > LOG`,
  then `pkill -f UnrealEditor-Cmd`: the headless editor did NOT exit after the script (killed after 4 min).
  `MJ_VERIFY_QUIT=1` tries `quit_editor()`; UNTESTED.
- **Cheat-sheet timing, one flat-colour material** (wall clock of the MCP calls only, not model thinking time):
  tool names only: 28 s, 17 failed calls, did NOT finish (colour and BaseColor connect never reached);
  with the describe output: 6 s, 2 failed calls, finished. Caveat: the describe was fetched before run A and only
  its excerpts were seen, not used. One run each, so a lead, not a result.
- **Gate limits (known):** only mesh components are read, so BSP brushes, landscape and actors with no mesh
  record no materials and pass. Hidden actors are skipped.
- Cheat sheets: `jam-cheatsheet-materials` (tested), `jam-cheatsheet-niagara`, `jam-cheatsheet-pcg` (listed from
  the describe, tools not called). `mx.py toolsets` cuts its print at about 800 chars: grep the cache file instead.

# Character rig dry run: plan (T-20261109-09, YouTube report top-five item 4)

Goal: find out, by measuring, whether a rigged character is affordable in the 4-day jam. Source lessons 1.5, 1.6,
1.20, 2.20, 2.21, 2.22 of `superagent-sandbox/reports/stefan_3d_ai-megajam-lessons.md`. Every claim in those
lessons is from a video and **UNTESTED** here until a row below says MEASURED.

Decision rule from the report: about 60 minutes total is a go; around 4 hours is a no-go, and the jam uses the
no-rig fallback (separate parts on timelines).

**Rule 7(h):** practice only. The character is the coded fallback prop (`scripts/procedural_props.py`), built in a
scratch folder outside the repo. Nothing from the run is committed or imported into the entry project; the scratch
UE project is deleted by the owner after the run. Only the timing log and the lessons are kept.

## Tools

| Need | Tool | Local? | Terms |
|---|---|---|---|
| Throwaway humanoid | `procedural_props.py --only character` (our script) | yes | ours |
| Auto-rig, path A (retarget) | Blender Rigify add-on, `scripts/rig_rigify.py` | yes, CPU | Blender is GPL; Rigify ships with it. Not re-read today. |
| Rig on mannequin names, path B (no retarget) | `scripts/rig_mannequin.py` (our script) | yes, CPU | ours |
| Weight binding | Blender automatic weights, then our nearest-bone fallback | yes | n/a |
| UE side | UE 5.8 editor, third-person template, IK Rig + IK Retargeter | yes | Epic EULA, already in use |
| Stopwatch | `scripts/rig_timelog.py` | yes | ours |

**Not used, on purpose:** AccuRig, Mixamo, Meshy rigging, Auto-Rig Pro (paid), Mesh to Motion, Skin Tokens. None
is needed to answer the question. If any is tried later, read its terms first and record them in the style of
`_config/reference/canon/ai3d-options-and-licences.md`. Skin Tokens/Mesh to Motion videos also use Hunyuan3D steps: banned.

## Setup (scratch, outside the repo)

```bash
export RIG=~/.claude/jobs/3600896e/tmp/rig    # or any scratch folder outside the repo
mkdir -p $RIG
python3 ~/Projects/megajam/scripts/rig_timelog.py $RIG/timelog.jsonl start
```

(Use the worktree's `scripts/` path if the PR is not merged yet.)

## Part A: Blender side (CPU, no GPU, no editor). MEASURED 2026-11-09

```bash
# A1 rig with Rigify (path A: DEF-* bones, needs the retargeter)
blender -b -P scripts/rig_rigify.py -- $RIG
# B1 rig on the mannequin's bone names (path B: no retarget)
blender -b -P scripts/rig_mannequin.py -- $RIG --names mannequin
# optional: same bones, neutral names, to see how the retargeter's auto chain mapping copes
blender -b -P scripts/rig_mannequin.py -- $RIG --names generic
```

Each prints one `RIG...`/`RIGIFY...` line with bones, vertices, `auto_missed` (vertices Blender's automatic
weights could not reach), `unweighted` (must be 0), `cover_core/arms/legs/head` (vertices per body group) and
`align_max_m` (largest distance from a bone's midpoint to the centre of the vertices it owns; limit 0.15 x height)
and seconds. If a group holds too little the script prints `COVERAGE FAIL: ...` and exits 3; if a bone sits too far
from its vertices it prints `ALIGNMENT FAIL: ...` and exits 4. Neither writes an FBX: that is a NO-GO result for
that path, not something to work around by hand.

Facing rule for `rig_mannequin.py`: `--input-facing` says which way the INPUT faces (default +X, like the prop);
any other input is refused ("input refused ... --input-facing") unless you pass `--input-facing -Y` (or +Y / -X),
which turns it to +X first. `--face` says which way the rigged mesh faces in the FBX (default -Y); mesh and bones
are turned together BEFORE binding, never after. `rig_rigify.py` has no `--input-facing`: its input must face +X.
Feet must be on z=0. `--input` replaces any rig the file already has. Results are in
`_config/reference/canon/jam-character-rig-path.md`. The FBX files land in `$RIG`: `character_rigify.fbx`,
`character_mannequin.fbx`, `character_generic.fbx` (leaf bones off, deform bones only, forward -Y, up Z).

Known limits, found by looking, not assumed: the character is made of loose boxes, so Blender's heat weights fail
on every vertex and the radius-based nearest-bone fallback does the skinning (rigid, no smooth armpits). The
mannequin layout has no fingers, twist or IK helper bones. For Rigify, only the trunk, limb, hand and foot metarig
bones are fitted to the layout (knee and elbow nudged 1% of height so the limb IK has a bend direction); face,
finger and breast bones are switched off for deform. Whether Unreal accepts these skeletons, and which way the FBX
faces in Unreal (forward -Y, up Z export), is UNTESTED.

Time sinks seen while building this, for the next round: the Blender FBX re-import changes axes, so a Blender
re-import cannot show Unreal's view of facing; `blender -b` exits 0 on failure (the scripts now force a real code);
glTF imports use quaternion rotation, where setting `rotation_euler` silently does nothing. Hand-run steps still
left: the scratch project, Content Browser import, IK Rig and Retargeter set-up (all GUI), and each timelog mark.

## Part B: Unreal side. RUN 2026-11-10 (n=1): NO-GO, results in `_config/reference/canon/jam-character-rig-path.md`

Preconditions: hub grants the editor slot; `gpu-preflight` clear. Facts from the hub's real UE 5.8 runs (2026-11-09):
the editor's MCP has **no arbitrary-Python tool** and no known IK Rig / IK Retargeter tool; a watch-folder FBX import
is proven only for wav; no Third Person project exists on disk and MockSlime has no mannequin. So:

- **Scratch project (who/where):** the hub or owner creates it by hand: Epic Launcher or editor "New Project" >
  Games > Third Person, Blueprint, no starter content, name `RigScratch`, in `~/Projects/rig-scratch/`
  (outside the repo and outside the entry project; owner deletes it after the run). Not created by this ticket.
  Creating it counts as step S0 on the timelog.
- **IK steps A3-A5 and A7 are GUI-only:** no MCP IK tool is known (UNTESTED: grep `scripts/mx.py toolsets --grep
  "IK|Retarget|Skeletal|Anim"` once in the live editor and use a tool if one exists). The person at the editor does
  them by hand in the Content Browser and IK Retargeter windows; the agent times and logs them.
- **Import (A2, B2) is GUI-first:** skeletal FBX import with skeleton assignment through the watch folder is
  UNPROVEN. Use the Content Browser Import dialog. A headless import task (`UnrealEditor-Cmd PROJECT -ExecCmds=
  "py /abs/script.py"`, editor CLOSED, under `timeout`, output lines prefixed `LogPython: `) is the alternative, but
  no script for it exists yet; writing one is a follow-up, not part of this ticket.
- **Screenshots:** use `spectacle`, not `mx.py shot` (the hub found the latter unreliable for this).
- The editor is started with `scripts/launch-editor.sh` (MCP port 8010, own memory scope); stop it when finished.

Mark each step as you finish it: `python3 scripts/rig_timelog.py $RIG/timelog.jsonl mark "STEP" --note "..."`.
Use `--at` to back-date. Print the table with `... table`. Write what breaks into the note at once.

### Path A: Rigify FBX, retarget the stock animations (lessons 1.5, 2.20 compared)

| Step | Action | Check |
|---|---|---|
| A1 | `rig_rigify.py` (Part A) | `unweighted=0` |
| A2 | Import `character_rigify.fbx` into the scratch project: Content Browser Import dialog (by hand), **Skeletal Mesh**, generate a **new** skeleton, Import Animations off | SK mesh shows; scale about 180 cm next to the mannequin; bones near 1x scale (video says a Mixamo rig came in huge: UNTESTED here) |
| A3 | Right-click the new Skeletal Mesh: Create > IK Rig; set the retarget root (pelvis `DEF-spine`) and add the leg, arm, spine, head chains | chains turn green |
| A4 | Open the stock mannequin IK Rig (template ships `IK_Mannequin`; if absent, create one the same way on SK_Mannequin) | exists |
| A5 | Create > IK Retargeter, source = mannequin IK Rig, target = our IK Rig; run **Auto Map Chains** and fix any that are red; match the pose (A-pose vs the mannequin) | preview animates and the feet stay down |
| A6 | Export the stock clips (idle, walk, run, jump) with the retargeter's Export Selected Animations (Python alternative from Epic docs: `IKRetargetBatchOperation.duplicate_and_retarget`, UNTESTED) | new animation assets play on our mesh |
| A7 | Third-person template: set the character Blueprint's mesh to ours, point the AnimBP at the retargeted skeleton or use Retarget Pose From Mesh (the video's live-retarget variant, UNTESTED) | play in editor: walk, run, jump look right |

### Path B: rig on the mannequin's bone names, no retarget (lesson 2.20)

| Step | Action | Check |
|---|---|---|
| B1 | `rig_mannequin.py --names mannequin` (Part A) | `unweighted=0`, 26 bones |
| B2 | Import `character_mannequin.fbx` as Skeletal Mesh and **assign the existing mannequin skeleton** (SK_Mannequin_Skeleton), Import Animations off | no "hierarchy does not match" error. UNTESTED whether UE accepts our reduced skeleton (no fingers/twist/IK bones) on the full one |
| B3 | Set the template Blueprint mesh to ours, play | stock animation plays with no distortion; if limbs twist or the body lies down, bone roll or facing is wrong (the FBX uses forward -Y, up Z: UNTESTED) |

### Wrap-up

| Step | Action |
|---|---|
| W1 | Run `rig_timelog.py ... table`; paste it into `_config/reference/canon/jam-character-rig-path.md`. |
| W2 | List what broke (error text, fix, minutes lost). |
| W3 | One line: `GO` or `NO-GO` for a rigged character in the jam. Rule: total time for the path you would actually use, repeated once with the lessons applied, under 60 minutes = GO (that figure is the report's, it is our decision to keep it). Path B is the shortcut to compare against path A. |
| W4 | Update the front matter `updated:`, `_config/CANON.md` row, re-run `python3 -m unittest tests.test_canon`. |

## What is out of scope

Weight painting (armpit fixes are in the videos, UNTESTED), cloth or tail physics, text-to-motion (lesson 1.20,
low priority unless this passes), ragdoll (lesson 2.22), cloud riggers. For the no-rig fallback (separate parts on
timelines), see lesson 2.22; its helper is not part of this ticket.

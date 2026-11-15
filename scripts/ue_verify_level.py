"""Verify a level's saved contents by loading it fresh, listing actors, and flagging known agent traps.

Two ways to run it:

* In the editor (headless runtime, same invocation pattern as ue_build_level.py): loads the level, prints the
  old VERIFY_* lines, then one `VERIFY_ACTOR_JSON={...}` line per actor and `VERIFY_FINDING=...` lines.
  The level comes from ENV, not an argument (-ExecCmds="py script" takes none): MJ_VERIFY_LEVEL (default
  /Game/MockJam7/L_MockJam7), MJ_CHANGED_BPS (comma list of edited Blueprint paths, any of '/Game/BP_X',
  '/Game/BP_X.BP_X', '/Game/BP_X.BP_X_C'), MJ_VERIFY_QUIT=1 (try to quit the editor when done; the headless
  editor does not exit by itself, so wrap the run in `timeout` and pkill it, as qa_harness.py documents).
  Save the log; UE prefixes each print with "[ts][n]LogPython: " and presubmit_gate.py accepts that.
* Off the editor (plain python3): `ue_verify_level.py --lint FILE [--brief]` lints a text dump of a Blueprint
  graph (or, with --brief, a lead-agent brief) for what agents do by default. Exit 1 if anything is flagged.

Every editor property read below is UNTESTED against the real UE 5.8.4 Python API (written 2026-11-09 without
an editor run). Each read is wrapped: an unreadable value becomes None and is reported as "unknown", never as
"fine". The pure functions are tested in tests/test_ue_verify_level.py with fake actors only.
"""

import json
import os
import re
import sys

try:
    import unreal
except ImportError:  # off-editor: only the pure functions and the --lint CLI work
    unreal = None

LEVEL_PATH = os.environ.get("MJ_VERIFY_LEVEL", "/Game/MockJam7/L_MockJam7")

# Engine default surfaces. Lowercase substrings of a material path. UNTESTED names: WorldGridMaterial is the
# grid the editor shows on a mesh with no material; "checker" and "grid" catch template and engine checker textures.
DEFAULT_MATERIAL_MARKERS = ("worldgridmaterial", "enginematerials/defaultmaterial", "checker", "grid")

# Numeric properties where 0 is almost never the intended value (the "zero default" trap).
ZERO_WATCH = ("decalsize", "decal_size", "impulse", "speed", "damage", "health", "range", "radius", "scale")


UNASSIGNED = "(unassigned slot: engine default grid)"  # contains "grid", so it matches the markers


def is_default_material(path):
    """True if a material path looks like an engine default grid or a checker."""
    low = (path or "").lower()
    return any(m in low for m in DEFAULT_MATERIAL_MARKERS)


def default_material_hits(rec):
    """Material paths of one actor record that are default grid or checker. [] if none."""
    return [m for m in rec.get("materials") or [] if is_default_material(m)]


def stale_candidates(records, changed_bps):
    """Placed actors whose Blueprint class was edited after they were placed: delete and respawn them."""
    changed = {_pkg(c) for c in changed_bps if c and c.strip()}
    return [r["label"] for r in records if r.get("bp") and _pkg(r["bp"]) in changed]


def _pkg(path):
    """'/Game/BP_Door.BP_Door_C', '/Game/BP_Door.BP_Door' and '/Game/BP_Door' all become '/Game/BP_Door'."""
    return path.strip().split(".", 1)[0]


def zero_defaults(rec):
    """Names of watched numeric properties left at exactly 0 on a Blueprint actor."""
    props = rec.get("numeric") or {}
    return sorted(k for k, v in props.items()
                  if v == 0 and not isinstance(v, bool) and any(w in k.lower() for w in ZERO_WATCH))


def collision_missing(rec):
    """True only if collision was read and is off on a gameplay mesh. None (unknown) is not a pass."""
    return rec.get("gameplay") and rec.get("collision") is False


def findings(records, changed_bps=()):
    """Every flagged problem as (rule, label, detail). Unknown reads are reported as 'unknown-*'."""
    out = []
    for lab in stale_candidates(records, changed_bps):
        out.append(("stale-actor", lab, "Blueprint edited since placement: delete and respawn"))
    for r in records:
        lab = r["label"]
        for m in default_material_hits(r):
            out.append(("default-material", lab, m))
        if r.get("gameplay") and r.get("collision") is None:
            out.append(("unknown-collision", lab, "collision not readable; check by hand"))
        if collision_missing(r):
            out.append(("no-collision", lab, "gameplay mesh has collision off"))
        for k in zero_defaults(r):
            out.append(("zero-default", lab, k))
    return out


# --- lint of what agents do by default (text dumps and briefs) ---------------------------------------------

GRAPH_RULES = (
    ("event-tick", re.compile(r"event\s*tick|EventTick|ReceiveTick", re.I),
     "per-frame Tick: use overlap events or a timer"),
    ("legacy-input", re.compile(r"K2Node_InputAxis|K2Node_InputAction\b|K2Node_InputKey|InputAxis\s|GetInputAxisValue", re.I),
     "legacy input: use Enhanced Input on UE 5.8"),
    ("raw-hlsl", re.compile(r"\bCustom\s*HLSL|MaterialExpressionCustom\b", re.I),
     "raw HLSL node: use material nodes unless told"),
)
# UE has no K2Node_Delay class: an exported Delay node is a K2Node_CallFunction with MemberName="Delay"
# (or "RetriggerableDelay"). The plain-text forms are for hand-written dumps.
DELAY_RE = re.compile(r'MemberName="(?:Retriggerable)?Delay"|K2Node_Delay\b|\bDelay\b\s*\(|^\s*Delay\b',
                      re.I | re.M)

BRIEF_RULES = (
    ("vague-target", re.compile(r"\bthe player\b|\bthe actor\b|\bthe box\b|\bthat actor\b", re.I),
     "name the Blueprint asset path, never 'the player' or 'the actor'"),
    ("widget-binding", re.compile(r"bind(ing)?\s+(the\s+)?(widget|wbp_)", re.I),
     "widget binding through MCP failed in a video claim (UNTESTED here): build the HUD in C++ or Python"),
    ("tick-ask", re.compile(r"\bevery frame\b|\bon tick\b|\bevent tick\b", re.I),
     "ask for overlap events or a timer, not per-frame checks"),
)


def lint_text(text, brief=False):
    """Flag agent defaults in a graph dump (or a brief). Returns [(rule, line_no, detail)]."""
    out = []
    rules = BRIEF_RULES if brief else GRAPH_RULES
    for i, line in enumerate(text.splitlines(), 1):
        for name, rx, why in rules:
            if rx.search(line):
                out.append((name, i, why))
    if not brief:
        delays = [m.start() for m in DELAY_RE.finditer(text)]
        if len(delays) >= 2:
            out.append(("delay-chain", text.count("\n", 0, delays[1]) + 1,
                        f"{len(delays)} Delay nodes: use a Timeline or timer"))
    return out


# --- editor side ---------------------------------------------------------------------------------------------

def _try(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def actor_record(actor):
    """Plain dict for one editor actor. All reads wrapped; None means unknown."""
    rec = {"label": _try(actor.get_actor_label, "?"), "class": _try(lambda: actor.get_class().get_name()),
           "visible": not _try(actor.is_temporarily_hidden_in_editor, False), "materials": [],
           "bp": "", "numeric": {}, "gameplay": False, "collision": None}
    kind = getattr(unreal, "MeshComponent", unreal.StaticMeshComponent)
    comps = _try(lambda: list(actor.get_components_by_class(kind)))
    if comps is None:  # older API shape: only the first component
        first = _try(lambda: actor.get_component_by_class(unreal.StaticMeshComponent))
        comps = [first] if first is not None else []
    colls = []
    for comp in comps:
        # A component that is not visible or is hidden in game (editor visualiser cube) renders nothing in play:
        # skip it. An unreadable value counts as visible, so the check fails safe.
        if _try(lambda c=comp: c.is_visible()) is False or _try(lambda c=comp: c.get_editor_property("hidden_in_game")) is True:
            continue
        rec["gameplay"] = True
        for m in _try(comp.get_materials, []) or []:
            # An unassigned slot (None) renders the engine default grid: record it as a default hit.
            rec["materials"].append(UNASSIGNED if m is None else m.get_path_name())
        ce = _try(comp.get_collision_enabled)
        colls.append(None if ce is None else "NO_COLLISION" not in str(ce).upper())
    if colls:
        # The actor blocks if any of its meshes does (a decorative no-collision shell beside a solid body is fine).
        rec["collision"] = True if True in colls else (None if None in colls else False)
    cls_path = _try(lambda: actor.get_class().get_path_name(), "") or ""
    if cls_path.startswith("/Game/"):
        rec["bp"] = cls_path
        for name in _try(lambda: [p for p in dir(actor) if not p.startswith("_")], []):
            if any(w in name.lower() for w in ZERO_WATCH):
                v = _try(lambda n=name: actor.get_editor_property(n))
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    rec["numeric"][name] = v
    return rec


def main():
    level_subsys = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor_subsys = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actor_subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    level_subsys.load_level(LEVEL_PATH)
    world = editor_subsys.get_editor_world()
    print(f"VERIFY_WORLD={world.get_path_name()}")

    actors = actor_subsys.get_all_level_actors()
    labels = sorted(a.get_actor_label() for a in actors)
    print(f"VERIFY_ACTOR_COUNT={len(labels)}")
    for label in labels:
        print(f"VERIFY_ACTOR={label}")
    records = [actor_record(a) for a in actors]
    for r in records:
        print("VERIFY_ACTOR_JSON=" + json.dumps(r, sort_keys=True))
    changed = os.environ.get("MJ_CHANGED_BPS", "").split(",")
    for rule, label, detail in findings(records, changed):
        print(f"VERIFY_FINDING={rule}|{label}|{detail}")
    print("VERIFY_DONE")
    # UnrealEditor-Cmd with -ExecCmds="py ..." does not exit when the script ends (seen 2026-11-09: it idled
    # until killed). Opt-in quit; UNTESTED whether quit_editor works in this mode (qa_harness.py notes none did).
    if os.environ.get("MJ_VERIFY_QUIT") == "1":
        _try(lambda: unreal.SystemLibrary.quit_editor())


def cli(argv):
    if len(argv) >= 2 and argv[0] == "--lint":
        brief = "--brief" in argv[2:]
        with open(argv[1], encoding="utf-8", errors="replace") as fh:
            hits = lint_text(fh.read(), brief=brief)
        for rule, line, why in hits:
            print(f"LINT {rule} line {line}: {why}")
        print(f"LINT_DONE findings={len(hits)}")
        return 1 if hits else 0
    print("usage: ue_verify_level.py --lint FILE [--brief]   (in the editor it runs the level check)", file=sys.stderr)
    return 2


if unreal is not None:
    main()
elif __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))

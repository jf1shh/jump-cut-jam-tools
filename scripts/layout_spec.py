#!/usr/bin/env python3
"""Layout spec: check a top-down layout against the metric sheet, draw it, turn it into a build plan.

Usage:
    layout_spec.py check  LAYOUT [--metrics FILE]          # exit 0 clean, 1 findings, 2 bad input
    layout_spec.py render LAYOUT -o OUT.svg [--metrics F]  # top-down SVG with scale bar, hero marker, path labels
    layout_spec.py build  LAYOUT -o PLAN.json [--metrics F]  # runs check first; plan feeds ue_build_level.py --plan

LAYOUT is a .json file, or an .svg/.html file that embeds the same JSON in
<script type="application/layout+json" id="layout-spec">...</script> (render writes that tag).
Docs: stages/02_build/references/layout-spec/README.md. Rule 7(h): practice only, level paths must be under /Game/Mock*.

Coordinates: cm, the same numbers as UE X/Y. UE is left-handed: in the top view +X points right and +Y points
DOWN the page (+Y is the walker's right when facing +X). The SVG is drawn that way, so it is not mirrored against
the built level. A room is a rectangle given by its centre (x, y) and size (w along X, h along Y). Door sides:
N = low-Y side (top of the sketch), S = high-Y side, W = low-X side, E = high-X side.
"""

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

DEFAULT_METRICS = Path(__file__).resolve().parent.parent / "stages" / "02_build" / "references" / "layout-spec" / "metrics.json"
PLAN_FORMAT = "megajam-layout-plan/1"
LEVEL_PREFIX = "/Game/Mock"
SIDES = ("N", "E", "S", "W")
EMBED_RE = re.compile(r'<script[^>]*id="layout-spec"[^>]*>(.*?)</script>', re.S)
EPS = 0.5
ENDPOINT_TOL = 25.0  # the "main" path must start at `start` and end at `objective` within this many cm


class LayoutError(Exception):
    """Input file unreadable or not shaped like a layout (exit 2)."""


def load_metrics(path=None):
    try:
        data = json.loads(Path(path or DEFAULT_METRICS).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise LayoutError(f"cannot read metrics: {e}")
    return {k: v for k, v in data.items() if not k.startswith("_") and k != "source"}


def load_layout(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise LayoutError(f"cannot read layout: {e}")
    if Path(path).suffix.lower() in (".svg", ".html", ".htm"):
        m = EMBED_RE.search(text)
        if not m:
            raise LayoutError("no <script id=\"layout-spec\"> block in the file")
        text = html.unescape(m.group(1)).replace("<\\/", "</")
    try:
        data = json.loads(text)
    except ValueError as e:
        raise LayoutError(f"layout is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise LayoutError("layout must be a JSON object")
    return normalize(data)


# ---- geometry -------------------------------------------------------------------------------

def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def room_rect(r):
    return (r["x"] - r["w"] / 2, r["y"] - r["h"] / 2, r["x"] + r["w"] / 2, r["y"] + r["h"] / 2)


def side_geom(r, side):
    """(axis, line coordinate, lo, hi) of a room side; axis 'x' means the wall runs along X."""
    x0, y0, x1, y1 = room_rect(r)
    if side == "N":  # top of the sketch = low y (UE top view: +X right, +Y down)
        return "x", y0, x0, x1
    if side == "S":
        return "x", y1, x0, x1
    if side == "E":
        return "y", x1, y0, y1
    return "y", x0, y0, y1  # W


def door_world(layout, door):
    """(axis, line, lo, hi) of the door's gap in world coordinates."""
    room = next(r for r in layout["rooms"] if r["id"] == door["room"])
    axis, line, lo, hi = side_geom(room, door["side"])
    centre = (lo + hi) / 2 + door["offset"]
    return axis, line, centre - door["width"] / 2, centre + door["width"] / 2


def point_in_room(p, r):
    x0, y0, x1, y1 = room_rect(r)
    return x0 - EPS <= p[0] <= x1 + EPS and y0 - EPS <= p[1] <= y1 + EPS


def in_any_room(p, rooms):
    return any(point_in_room(p, r) for r in rooms)


def path_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def path_samples(points, step=50.0):
    for a, b in zip(points, points[1:]):
        n = max(1, int(math.dist(a, b) // step))
        for i in range(n + 1):
            t = i / n
            yield (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def shared_wall_length(a, b):
    """Length of the wall two touching (non-overlapping) rooms share; 0 if they do not touch."""
    ax0, ay0, ax1, ay1 = room_rect(a)
    bx0, by0, bx1, by1 = room_rect(b)
    y_ov = min(ay1, by1) - max(ay0, by0)
    x_ov = min(ax1, bx1) - max(ax0, bx0)
    if (abs(ax1 - bx0) <= EPS or abs(bx1 - ax0) <= EPS) and y_ov > 0:
        return y_ov
    if (abs(ay1 - by0) <= EPS or abs(by1 - ay0) <= EPS) and x_ov > 0:
        return x_ov
    return 0.0


def overlap_area(a, b):
    ax0, ay0, ax1, ay1 = room_rect(a)
    bx0, by0, bx1, by1 = room_rect(b)
    return max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))


# ---- checks ---------------------------------------------------------------------------------

LIST_KEYS = ("doors", "paths", "gaps", "ledges")


def normalize(layout):
    """Copy where a JSON null for an optional list/object (LLMs write null for 'empty') means empty."""
    out = dict(layout)
    for k in LIST_KEYS:
        if out.get(k) is None:
            out.pop(k, None)
    if out.get("targets") is None:
        out.pop("targets", None)
    return out


def check_layout(layout, metrics):
    """Return a list of finding strings (empty means the layout obeys the metric sheet)."""
    f = []
    m = metrics
    layout = normalize(layout)
    shape = _check_shape(layout, f)
    if not shape:
        return f
    rooms = layout["rooms"]
    ids = [r["id"] for r in rooms]
    for r in rooms:
        short = min(r["w"], r["h"])
        corridor = r.get("kind") == "corridor"
        if corridor and short < m["corridor_min_width_cm"]:
            f.append(f"corridor {r['id']}: width {short:g} cm < min {m['corridor_min_width_cm']} cm")
        if not corridor and short < m["room_min_side_cm"]:
            f.append(f"room {r['id']}: short side {short:g} cm < min {m['room_min_side_cm']} cm")
        ht = r.get("height", m["wall_height_default_cm"])
        if not _num(ht) or ht < m["wall_height_min_cm"]:
            f.append(f"room {r['id']}: wall height {ht} < min {m['wall_height_min_cm']} cm")
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            if overlap_area(a, b) > EPS:
                f.append(f"rooms {a['id']} and {b['id']} overlap (they may only touch)")
            elif shared_wall_length(a, b) > EPS and \
                    a.get("height", m["wall_height_default_cm"]) != b.get("height", m["wall_height_default_cm"]):
                f.append(f"rooms {a['id']} and {b['id']} share a wall but have different heights "
                         f"(give both the same 'height')")
    adjacency = {i: set() for i in ids}
    for d in layout.get("doors", []):
        _check_door(layout, d, m, ids, adjacency, f)
    gaps_world = [door_world(layout, d) for d in layout.get("doors", [])]
    for p in layout.get("paths", []):
        _check_path(p, rooms, gaps_world, m, f)
    for g in layout.get("gaps", []):
        if not _num(g.get("width")) or g["width"] > m["max_gap_cm"]:
            f.append(f"gap {g.get('id', '?')}: width {g.get('width')} cm > max {m['max_gap_cm']} cm")
    for g in layout.get("ledges", []):
        if not _num(g.get("height")) or g["height"] > m["max_ledge_cm"]:
            f.append(f"ledge {g.get('id', '?')}: height {g.get('height')} cm > max {m['max_ledge_cm']} cm")
    _check_points_and_targets(layout, rooms, adjacency, m, f)
    return f


def _check_shape(layout, f):
    ok = True
    lp = layout.get("level_path")
    if not isinstance(lp, str) or not lp.startswith(LEVEL_PREFIX):
        f.append(f"level_path must start with {LEVEL_PREFIX} (practice levels only, Rule 7(h)); got {lp!r}")
    if layout.get("units", "cm") != "cm":
        f.append("units must be cm")
    rooms = layout.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        f.append("rooms: need a non-empty list")
        return False
    seen = set()
    for i, r in enumerate(rooms):
        if not isinstance(r, dict) or not all(_num(r.get(k)) for k in ("x", "y", "w", "h")) \
                or not isinstance(r.get("id"), str) or r["w"] <= 0 or r["h"] <= 0:
            f.append(f"rooms[{i}]: need string id and numbers x, y, w>0, h>0")
            ok = False
        elif r["id"] in seen:
            f.append(f"rooms[{i}]: duplicate id {r['id']}")
            ok = False
        else:
            seen.add(r["id"])
    for key in ("start", "objective"):
        p = layout.get(key)
        if not isinstance(p, dict) or not _num(p.get("x")) or not _num(p.get("y")):
            f.append(f"{key}: need numbers x and y")
            ok = False
    for k in LIST_KEYS:
        v = layout.get(k, [])
        if not isinstance(v, list) or (k in ("gaps", "ledges") and not all(isinstance(e, dict) for e in v)):
            f.append(f"{k}: must be a list{' of objects' if k in ('gaps', 'ledges') else ''} (or null)")
            return False
    tg = layout.get("targets", {})
    if not isinstance(tg, dict):
        f.append("targets: must be an object (or null)")
        return False
    mw = tg.get("main_walk_time_s")
    if mw is not None and not (isinstance(mw, list) and len(mw) == 2 and all(_num(v) for v in mw)):
        f.append("targets.main_walk_time_s must be [min_s, max_s] (two numbers)")
        ok = False
    for i, d in enumerate(layout.get("doors", [])):
        if not isinstance(d, dict) or d.get("side") not in SIDES or d.get("room") not in seen \
                or not isinstance(d.get("to"), str) \
                or not all(_num(d.get(k)) for k in ("offset", "width", "height")):
            f.append(f"doors[{i}]: need room (known id), side N/E/S/W, 'to' (the room on the other side; "
                     f"a door onto nothing is not allowed), numbers offset, width, height")
            ok = False
    for i, p in enumerate(layout.get("paths", [])):
        pts = p.get("points") if isinstance(p, dict) else None
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not isinstance(pts, list) or len(pts) < 2 \
                or not all(isinstance(q, list) and len(q) == 2 and all(_num(c) for c in q) for q in pts):
            f.append(f"paths[{i}]: need string id and points [[x,y],...] (2 or more)")
            ok = False
    return ok


def _check_door(layout, d, m, ids, adjacency, f):
    name = d.get("id", f"{d['room']}/{d['side']}")
    room = next(r for r in layout["rooms"] if r["id"] == d["room"])
    if d["width"] < m["door_min_width_cm"] or d["width"] > m["door_max_width_cm"]:
        f.append(f"door {name}: width {d['width']:g} cm outside {m['door_min_width_cm']}-{m['door_max_width_cm']} cm")
    if d["height"] < m["door_min_height_cm"]:
        f.append(f"door {name}: height {d['height']:g} cm < min {m['door_min_height_cm']} cm")
    ht = room.get("height", m["wall_height_default_cm"])
    if _num(ht) and d["height"] > ht:
        f.append(f"door {name}: height {d['height']:g} cm taller than the wall ({ht} cm)")
    axis, line, lo, hi = side_geom(room, d["side"])
    dax, dline, dlo, dhi = door_world(layout, d)
    margin = m["door_edge_margin_cm"]
    if dlo < lo + margin - EPS or dhi > hi - margin + EPS:
        f.append(f"door {name}: gap must stay {margin} cm inside the wall ends")
    other = d["to"]
    if other not in ids:
        f.append(f"door {name}: 'to' room {other!r} does not exist")
        return
    nb = next(r for r in layout["rooms"] if r["id"] == other)
    nht = nb.get("height", m["wall_height_default_cm"])
    if _num(nht) and d["height"] > nht:
        f.append(f"door {name}: height {d['height']:g} cm taller than the wall of room {other} ({nht} cm)")
    opp = {"N": "S", "S": "N", "E": "W", "W": "E"}[d["side"]]
    naxis, nline, nlo, nhi = side_geom(nb, opp)
    if abs(nline - line) > EPS or not (nlo - EPS <= dlo and dhi <= nhi + EPS):
        f.append(f"door {name}: rooms {d['room']} and {other} do not share the wall where the door sits")
        return
    if dlo < nlo + margin - EPS or dhi > nhi - margin + EPS:
        f.append(f"door {name}: gap must stay {margin} cm inside the wall ends of room {other} too")
    adjacency[d["room"]].add(other)
    adjacency[other].add(d["room"])


def first_wall_violation(points, rooms, door_gaps, step=25.0):
    """First place a path crosses or touches a room wall outside every door gap, or None."""
    samples = list(path_samples([tuple(q) for q in points], step))
    for r in rooms:
        for side in SIDES:
            axis, line, lo, hi = side_geom(r, side)
            gaps = [(g[2], g[3]) for g in door_gaps if g[0] == axis and abs(g[1] - line) <= EPS]
            i = 1 if axis == "x" else 0  # a wall running along x sits at y == line (and vice versa)
            j = 1 - i
            for p, q in zip(samples, samples[1:]):
                sp, sq = p[i] - line, q[i] - line
                if abs(sp) <= EPS or abs(sq) <= EPS or sp * sq < 0:
                    if abs(sp) <= EPS:
                        c = p[j]
                    elif abs(sq) <= EPS:
                        c = q[j]
                    else:
                        c = p[j] + (q[j] - p[j]) * (-sp / (sq - sp))
                    if lo - EPS <= c <= hi + EPS and not any(g0 - EPS <= c <= g1 + EPS for g0, g1 in gaps):
                        return (p[0], p[1]) if abs(sp) <= EPS or sp * sq < 0 else (q[0], q[1])
    return None


def _check_path(p, rooms, door_gaps, m, f):
    pts = p["points"]
    length = path_length(pts)
    speed = m["walk_speed_cm_s"]
    if "length_cm" in p:
        tol = max(1.0, length * m["length_tolerance_pct"] / 100)
        if not _num(p["length_cm"]) or abs(p["length_cm"] - length) > tol:
            f.append(f"path {p['id']}: declared length {p['length_cm']} cm, computed {length:.0f} cm")
    if "walk_time_s" in p:
        t = length / speed
        if not _num(p["walk_time_s"]) or abs(p["walk_time_s"] - t) > m["time_tolerance_s"]:
            f.append(f"path {p['id']}: declared walk time {p['walk_time_s']} s, computed {t:.1f} s at {speed} cm/s")
    bad = next((q for q in path_samples([tuple(q) for q in pts]) if not in_any_room(q, rooms)), None)
    if bad:
        f.append(f"path {p['id']}: leaves every room near ({bad[0]:.0f}, {bad[1]:.0f})")
    else:
        hit = first_wall_violation(pts, rooms, door_gaps)
        if hit:
            f.append(f"path {p['id']}: crosses or touches a wall near ({hit[0]:.0f}, {hit[1]:.0f}) "
                     f"where there is no door gap")


def wall_segments(layout):
    """Solid wall pieces as (axis, line, a, b): every room side minus the door gaps."""
    gaps = [door_world(layout, d) for d in layout.get("doors", [])]
    segs = []
    for r in layout["rooms"]:
        for side in SIDES:
            axis, line, lo, hi = side_geom(r, side)
            here = [(g[2], g[3]) for g in gaps if g[0] == axis and abs(g[1] - line) <= EPS]
            segs += [(axis, line, a, b) for a, b in _subtract(lo, hi, here)]
    return segs


def wall_distance(layout, x, y):
    """Distance in cm from (x, y) to the nearest solid wall centre line."""
    best = math.inf
    for axis, line, a, b in wall_segments(layout):
        px, py = (x, y) if axis == "x" else (y, x)  # px runs along the wall, py across it
        best = min(best, math.hypot(max(a - px, 0.0, px - b), py - line))
    return best


def clearance_needed(metrics):
    return metrics["player_capsule_radius_cm"] + metrics["wall_thickness_cm"] / 2


def room_of(p, rooms):
    return next((r["id"] for r in rooms if point_in_room((p["x"], p["y"]), r)), None)


def _check_points_and_targets(layout, rooms, adjacency, m, f):
    start_room = room_of(layout["start"], rooms)
    obj_room = room_of(layout["objective"], rooms)
    need = clearance_needed(m)
    for key, rid in (("start", start_room), ("objective", obj_room)):
        if rid is None:
            f.append(f"{key} is not inside any room")
        else:
            d = wall_distance(layout, layout[key]["x"], layout[key]["y"])
            if d < need - EPS:
                f.append(f"{key} is {d:.0f} cm from a wall; the player capsule needs at least {need:g} cm")
    if start_room and obj_room:
        seen, todo = {start_room}, [start_room]
        while todo:
            for n in adjacency[todo.pop()]:
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        if obj_room not in seen:
            f.append(f"objective room {obj_room} cannot be reached from start room {start_room} through the doors")
    tgt = layout.get("targets", {}).get("main_walk_time_s")
    main = next((p for p in layout.get("paths", []) if p["id"] == "main"), None)
    if main is not None:
        for label, pt, want in (("first", main["points"][0], layout["start"]),
                                ("last", main["points"][-1], layout["objective"])):
            if math.dist(pt, (want["x"], want["y"])) > ENDPOINT_TOL:
                what = "start" if label == "first" else "objective"
                f.append(f"path main: {label} point {pt} is more than {ENDPOINT_TOL:g} cm from the {what}")
    if tgt is not None:
        if main is None:
            f.append("targets.main_walk_time_s is set but there is no path with id 'main'")
        else:
            t = path_length(main["points"]) / m["walk_speed_cm_s"]
            if not tgt[0] <= t <= tgt[1]:
                f.append(f"main path walk time {t:.1f} s outside target {tgt[0]}-{tgt[1]} s")


# ---- build plan -----------------------------------------------------------------------------

def _cube(label, cx, cy, cz, sx_cm, sy_cm, sz_cm):
    r = lambda v: round(v, 3)
    return {"label": label, "loc": [r(cx), r(cy), r(cz)], "scale": [r(sx_cm / 100), r(sy_cm / 100), r(sz_cm / 100)]}


def _subtract(lo, hi, gaps):
    """Pieces of [lo, hi] left after removing the (g0, g1) gaps."""
    pieces, cur = [], lo
    for g0, g1 in sorted(gaps):
        g0, g1 = max(g0, lo), min(g1, hi)
        if g1 <= g0:
            continue
        if g0 > cur + EPS:
            pieces.append((cur, g0))
        cur = max(cur, g1)
    if hi > cur + EPS:
        pieces.append((cur, hi))
    return pieces


def build_plan(layout, metrics):
    """Plain-data plan (floors and walls as cubes in UE units) for ue_build_level.py --plan."""
    t = metrics["wall_thickness_cm"]
    doors = [door_world(layout, d) + (d["height"],) for d in layout.get("doors", [])]
    cubes, seen, covered = [], set(), {}

    def add(c):
        key = (tuple(c["loc"]), tuple(c["scale"]))
        if key not in seen:
            seen.add(key)
            cubes.append(c)

    for r in layout["rooms"]:
        wall_h = r.get("height", metrics["wall_height_default_cm"])
        add(_cube(f"Floor_{r['id']}", r["x"], r["y"], -5.0, r["w"], r["h"], 10.0))
        for side in SIDES:
            axis, line, lo, hi = side_geom(r, side)
            here = [d for d in doors if d[0] == axis and abs(d[1] - line) <= EPS]
            pieces = _subtract(lo, hi, [(d[2], d[3]) for d in here])
            done = covered.setdefault((axis, round(line)), [])
            fresh = [p for a, b in pieces for p in _subtract(a, b, done)]  # no two walls on the same span
            done.extend(pieces)
            for n, (a, b) in enumerate(fresh):
                c = (a + b) / 2
                if axis == "x":
                    add(_cube(f"Wall_{r['id']}_{side}{n}", c, line, wall_h / 2, b - a, t, wall_h))
                else:
                    add(_cube(f"Wall_{r['id']}_{side}{n}", line, c, wall_h / 2, t, b - a, wall_h))
            for n, d in enumerate(here):  # lintel over each door gap
                if d[4] < wall_h - EPS and d[2] >= lo - EPS and d[3] <= hi + EPS:
                    c, lh = (d[2] + d[3]) / 2, wall_h - d[4]
                    z = d[4] + lh / 2
                    if axis == "x":
                        add(_cube(f"Lintel_{r['id']}_{side}{n}", c, line, z, d[3] - d[2], t, lh))
                    else:
                        add(_cube(f"Lintel_{r['id']}_{side}{n}", line, c, z, t, d[3] - d[2], lh))
    s, o = layout["start"], layout["objective"]
    need = clearance_needed(metrics)
    orb = [s["x"], s["y"], 0.0]  # decorative PlayerOrb: first spot near the start that is inside a room and clear of walls
    for dx, dy in ((150, 150), (150, -150), (-150, 150), (-150, -150), (150, 0), (-150, 0), (0, 150), (0, -150)):
        x, y = s["x"] + dx, s["y"] + dy
        if room_of({"x": x, "y": y}, layout["rooms"]) == room_of(s, layout["rooms"]) \
                and wall_distance(layout, x, y) >= need:
            orb = [x, y, 0.0]
            break
    return {
        "format": PLAN_FORMAT,
        "name": layout.get("name", ""),
        "level_path": layout["level_path"],
        "cubes": cubes,
        "player_start": [s["x"], s["y"], 50.0],
        "objective": [o["x"], o["y"], 0.0],
        "orb": orb,
        "walk_speed_cm_s": metrics["walk_speed_cm_s"],
        "not_built": [f"{k}:{g.get('id', '?')}" for k in ("gaps", "ledges") for g in layout.get(k, [])],
    }


MIN_SVG_W = 420  # px; the axis note is about 370 px at 11 px font


# ---- render ---------------------------------------------------------------------------------

def render_svg(layout, metrics, scale=0.2, pad=150):
    """Top-down SVG, 1 px = 5 cm by default. North is up. Embeds the layout JSON for round trips."""
    rects = [room_rect(r) for r in layout["rooms"]]
    minx, miny = min(r[0] for r in rects) - pad, min(r[1] for r in rects) - pad
    maxx, maxy = max(r[2] for r in rects) + pad, max(r[3] for r in rects) + pad
    X = lambda x: (x - minx) * scale
    Y = lambda y: (y - miny) * scale  # +Y points DOWN the page, as in UE's top view (X right)
    h = Y(maxy)
    w = max(X(maxx), MIN_SVG_W)  # wide enough for the axis note below
    speed = metrics["walk_speed_cm_s"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h + 40:.0f}" '
           f'viewBox="0 0 {w:.0f} {h + 40:.0f}" font-family="sans-serif" font-size="11">',
           f'<rect width="100%" height="100%" fill="#fff"/>']
    for r in layout["rooms"]:
        x0, y0, x1, y1 = room_rect(r)
        fill = "#e8eef7" if r.get("kind") != "corridor" else "#f3efe0"
        out.append(f'<rect x="{X(x0):.1f}" y="{Y(y0):.1f}" width="{(x1 - x0) * scale:.1f}" '
                   f'height="{(y1 - y0) * scale:.1f}" fill="{fill}" stroke="#333" stroke-width="2"/>')
        out.append(f'<text x="{X(x0) + 4:.1f}" y="{Y(y0) + 13:.1f}">{html.escape(r["id"])} '
                   f'{r["w"]:g}x{r["h"]:g} cm</text>')
    for d in layout.get("doors", []):
        axis, line, lo, hi = door_world(layout, d)
        x1_, y1_, x2_, y2_ = ((X(lo), Y(line), X(hi), Y(line)) if axis == "x"
                              else (X(line), Y(hi), X(line), Y(lo)))
        out.append(f'<line x1="{x1_:.1f}" y1="{y1_:.1f}" x2="{x2_:.1f}" y2="{y2_:.1f}" '
                   f'stroke="#c33" stroke-width="5"/>')
    for p in layout.get("paths", []):
        pts = p["points"]
        length = path_length(pts)
        d = " ".join(f"{X(q[0]):.1f},{Y(q[1]):.1f}" for q in pts)
        out.append(f'<polyline points="{d}" fill="none" stroke="#2a7" stroke-width="3" stroke-dasharray="8 4"/>')
        mx, my = pts[len(pts) // 2]
        out.append(f'<text x="{X(mx) + 6:.1f}" y="{Y(my) - 6:.1f}" fill="#185">{html.escape(p["id"])}: '
                   f'{length:.0f} cm, {length / speed:.1f} s</text>')
    for key, colour in (("start", "#06c"), ("objective", "#c60")):
        p = layout[key]
        out.append(f'<circle cx="{X(p["x"]):.1f}" cy="{Y(p["y"]):.1f}" r="7" fill="{colour}"/>'
                   f'<text x="{X(p["x"]) + 10:.1f}" y="{Y(p["y"]) + 4:.1f}">{key}</text>')
    # scale bar (500 cm) and hero marker (player height as a circle of that diameter's footprint: capsule)
    by = h + 20
    out.append(f'<line x1="10" y1="{by:.0f}" x2="{10 + 500 * scale:.0f}" y2="{by:.0f}" stroke="#000" stroke-width="3"/>'
               f'<text x="{10 + 500 * scale + 8:.0f}" y="{by + 4:.0f}">scale bar 500 cm; hero capsule '
               f'{metrics["player_capsule_radius_cm"] * 2} cm wide, {metrics["player_height_cm"]} cm tall</text>')
    out.append(f'<circle cx="{w - 30:.0f}" cy="{by:.0f}" r="{metrics["player_capsule_radius_cm"] * scale:.1f}" '
               f'fill="#06c" opacity="0.6"/><text x="{w - 70:.0f}" y="{by - 12:.0f}">hero</text>')
    out.append(f'<text x="4" y="14">+X right, +Y down (UE top view; +Y is the walker\'s right facing +X)</text>')
    blob = json.dumps(layout, indent=1).replace("</", "<\\/")
    out.append(f'<script type="application/layout+json" id="layout-spec">{html.escape(blob, quote=False)}</script>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---- CLI ------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "render", "build"):
        p = sub.add_parser(name)
        p.add_argument("layout")
        p.add_argument("--metrics")
        if name != "check":
            p.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        layout, metrics = load_layout(args.layout), load_metrics(args.metrics)
    except LayoutError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    findings = check_layout(layout, metrics)
    if args.cmd == "check" or findings:
        for line in findings:
            print(f"FAIL {line}")
        print(f"LAYOUT_CHECK {'FAIL' if findings else 'OK'} findings={len(findings)}")
        if findings or args.cmd == "check":
            return 1 if findings else 0
    if args.cmd == "render":
        Path(args.out).write_text(render_svg(layout, metrics), encoding="utf-8")
    else:
        Path(args.out).write_text(json.dumps(build_plan(layout, metrics), indent=1) + "\n", encoding="utf-8")
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

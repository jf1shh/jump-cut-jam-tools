#!/usr/bin/env python3
"""Judge pass: a second agent rates the packaged build like an Epic MegaJam judge (T-20261108-14).

Runs AFTER the agent playtest gate passes. Protocol: stages/03_playtest/references/judge-pass.md.

  judge_pass.py packet --session DIR --page PAGE [--video FILE] [--out DIR] [--max-frames N]
        Builds OUT/: packet.json, frames/ (copies of the playtest evidence + a spread of other frames),
        prompt.md (rubric prompt for the judge agent), report-template.json, page-check.json.
  judge_pass.py parse REPORT [--packet OUT] [--out FILE] [--md]
        Reads the judge's report (raw JSON, or JSON inside a ``` fence), checks it, prints normalized JSON
        (or --md: the block for the owner handoff, which goes BEFORE the build link).
  judge_pass.py page-check PAGE [--video FILE]
        Only the itch page draft checks.

Exit codes: 0 ok, 2 the report or the page failed its checks, 3 usage error / unreadable input.
Scores are the seven criteria of Official Rules Rule 9 (see RULES.md), integers 1-5. The judge reads only
the packet, never the source. No network, no GPU; the judge itself is another agent session.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

CRITERIA = ("ambition_innovation", "contest_theme", "fun_factor", "gameplay", "visuals", "level_design", "audio")
LABELS = {
    "ambition_innovation": "Ambition and Innovation",
    "contest_theme": "Use of Contest Theme",
    "fun_factor": "Fun Factor",
    "gameplay": "Gameplay",
    "visuals": "Visuals",
    "level_design": "Level Design",
    "audio": "Audio",
}
MILESTONES = ("win", "lose", "restart")
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
MIN_SHOTS = 3  # our own bar; the rules do not set a number
EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 2, 3


class UsageError(Exception):
    pass


# ---------- itch page draft ----------

def probe_video(path):
    """(duration_s, width, height) via ffprobe, or None when ffprobe is missing or fails."""
    if not shutil.which("ffprobe"):
        return None
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:format=duration", "-of", "json", str(path)],
                           capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
        s = d["streams"][0]
        return float(d["format"]["duration"]), int(s["width"]), int(s["height"])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError):
        return None


def _page_text_and_dir(page):
    """(text, base, is_dir). A page given as a file never scans its surroundings: only what it names counts."""
    p = Path(page)
    if p.is_dir():
        cands = [c for c in sorted(p.iterdir()) if c.suffix.lower() in (".md", ".txt", ".html", ".htm")]
        if not cands:
            raise UsageError(f"no page draft (.md/.txt/.html) in {p}")
        return "\n\n".join(c.read_text(encoding="utf-8", errors="replace") for c in cands), p, True
    if not p.is_file():
        raise UsageError(f"page draft {p} does not exist")
    return p.read_text(encoding="utf-8", errors="replace"), p.parent, False


# links that point at one video, not a channel or profile
VIDEO_LINK = re.compile(
    r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?[^\s)\"'>]*v=|embed/|shorts/|live/)|youtu\.be/|vimeo\.com/(?:video/)?\d|"
    r"player\.vimeo\.com/video/\d|twitch\.tv/videos/\d)[^\s)\"'>]*", re.I)
IMG_REF = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img\b[^>]*?\bsrc=[\"']([^\"']+)", re.I)
# a heading opener in Markdown (#, **bold**, __bold__) or HTML (<h2>, <b>, <strong>)
OPEN = r"(?:^[ \t]*(?:#+[ \t]*|\*\*|__)|<h[1-6][^>]*>[ \t]*|<(?:b|strong)>[ \t]*)"
# a plain-text label counts only as "Controls:" or "Controls" alone on its line, never as the start of a sentence
CONTROLS_HEAD = re.compile(OPEN + r"controls?\b|^[ \t]*controls?[ \t]*(?::|$)", re.I | re.M)
CREDITS_HEAD = re.compile(OPEN + r"(?:credits?|attribution)\b|^[ \t]*(?:credits?|attribution)[ \t]*(?::|$)", re.I | re.M)
# every Markdown or HTML heading, with its level
HEADING = re.compile(r"^[ \t]*(#+)[ \t]|<h([1-6])[\s>]", re.I | re.M)
KEYS = re.compile(r"\b(wasd|arrows?|mouse|keyboard|gamepad|controller|click|space|shift|ctrl|esc|press|stick|button)\b", re.I)
# an AI-use heading says it is about use/disclosure, not just that the word AI appears
_AI = r"(?:ai|artificial intelligence)"
_HOPEN = r"(?:^[ \t]*#+[ \t]*|<h[1-6][^>]*>[ \t]*)"  # real headings only; bold prose is not a heading
AI_HEAD = re.compile(
    _HOPEN + r"[^\n<:]{0,30}?\b" + _AI + r"[ \t-]*(?:use|usage|declaration|disclosure|disclaimer|statement|transparency|tools?|"
    r"generated|assisted|credits?)\b"
    r"|" + _HOPEN + r"[^\n<:]{0,30}?\b(?:use of|usage of|declaration of|disclosure of|statement on|made with|created with)"
    r"\s+(?:\w+\s+){0,2}" + _AI + r"\b", re.I | re.M)
# a sentence that says AI helped make the game; "outwit an AI" or "Smart AI enemies use cover" is not one
AI_STMT = re.compile(
    r"\b(?:generated|created|made|written|produced|composed|developed|built|designed|assisted)\s+(?:with|using|via)\s+"
    r"(?:\w+\s+){0,2}" + _AI + r"\b"
    r"|\b" + _AI + r"[- ](?:generated|assisted|made|created|declaration|disclosure|tools?)\b"
    r"|\b(?:used|using)\s+(?:\w+\s+){0,2}" + _AI + r"\b", re.I)


def _section_end(text, head):
    """Where the section opened by match `head` ends: the next heading at the same or a higher level
    (sub-headings stay inside), or the credits section. A plain-text or bold label ends at any heading."""
    opener = text[head.start():head.end()]
    m = re.match(r"\s*(#+)", opener) or re.search(r"<h([1-6])", opener, re.I)
    level = len(m.group(1)) if m and m.group(1).startswith("#") else int(m.group(1)) if m else 7
    end = len(text)
    for h in HEADING.finditer(text, head.end()):
        lv = len(h.group(1)) if h.group(1) else int(h.group(2))
        if lv <= level:
            end = h.start()
            break
    credits = CREDITS_HEAD.search(text, head.end())
    return min(end, credits.start()) if credits else end


def _image_refs(text, base):
    """Distinct screenshot references: remote URLs, or local files that exist next to the draft."""
    out = set()
    for m in IMG_REF.finditer(text):
        ref = (m.group(1) or m.group(2)).strip()
        if re.match(r"https?://", ref, re.I) or (base / ref).is_file():
            out.add(ref)
    return out


def _is_english(text):
    return not any(c.isalpha() and "LATIN" not in unicodedata.name(c, "") for c in text)


def check_page(page, video=None, probe=probe_video):
    """Each check is {name, ok, detail}. A missing thing is a failed check, never an exception."""
    text, base, is_dir = _page_text_and_dir(page)
    checks = []

    def add(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    # video: a local file (given, named by the page, or found in a page folder) or a link to one video
    local = Path(video) if video else None
    if local is None and is_dir:
        found = [f for f in sorted(base.rglob("*")) if f.is_file() and f.suffix.lower() in VIDEO_EXT]
        local = found[0] if found else None
    refs = re.findall(r"[\w./-]+\.(?:mp4|mov|webm|mkv)", text, re.I)
    if local is None:
        local = next((base / r for r in refs if (base / r).is_file()), None)
    links = [m.group(0) for m in VIDEO_LINK.finditer(text)]
    if local is not None:
        if not local.is_file():
            add("video", False, f"video file {local} does not exist")
        else:
            info = probe(local)
            if info is None:
                add("video", False, f"{local.name} found but could not be probed; check 30-60 s and 1920x1080 by hand")
            else:
                dur, w, h = info
                ok = 30 <= dur <= 60 and w >= 1920 and h >= 1080
                add("video", ok, f"{local.name}: {dur:.1f} s, {w}x{h} (need 30-60 s, at least 1920x1080)")
    elif links:
        add("video", True, f"link {links[0]} (length and size cannot be checked from a link; confirm 30-60 s by hand)")
    elif refs:
        add("video", False, f"page names {refs[0]} but no such file was found next to the draft")
    else:
        add("video", False, "no gameplay video file or link to a single video")

    n = len(_image_refs(text, base))
    if is_dir:
        n = max(n, sum(1 for f in base.rglob("*") if f.is_file() and f.suffix.lower() in IMG_EXT))
    add("screenshots", n >= MIN_SHOTS, f"{n} screenshot(s) found (need at least {MIN_SHOTS})")

    head = CONTROLS_HEAD.search(text)
    section = ""
    if head:
        section = text[head.end():_section_end(text, head)]
    has_keys = bool(KEYS.search(section))
    add("controls_text", has_keys, "controls section with actual keys/buttons" if has_keys
        else "no controls section naming keys or buttons")

    credits = CREDITS_HEAD.search(text)
    add("credits", credits, "credits section present" if credits else "no credits section")

    ai = AI_HEAD.search(text) or AI_STMT.search(text)
    add("ai_declaration", ai, "AI use statement present" if ai else "no AI use declaration")

    english = _is_english(text)
    add("english_only", english, "page text is English" if english
        else "page contains non-Latin text; Rule 7(i) wants English only")
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


# ---------- packet ----------

def is_gate_folder(session):
    """A visual_playtest folder (results.json, no journal.jsonl): frames sit in the folder itself."""
    s = Path(session)
    return not (s / "journal.jsonl").is_file() and (s / "results.json").is_file()


def _read_journal(session):
    j = Path(session) / "journal.jsonl"
    if not j.is_file():
        raise UsageError(f"{session} has neither journal.jsonl (agent_playtest) nor results.json "
                         "(visual_playtest); is this a playtest folder?")
    out = []
    for line in j.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                raise UsageError("journal.jsonl has a line that is not JSON") from None
    return out


def marked_evidence(session):
    """{milestone: {files, note}} using the gate's own choice: the latest USABLE mark per milestone."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
    import agent_playtest_cli as apc  # the gate stays the single source of truth
    sess = apc.Session(session)
    entries = sess.entries()
    captured = {e["file"]: i for i, e in enumerate(entries)
                if e["kind"] in ("look", "press", "mouse", "clip") and e.get("file")}
    inputs = [i for i, e in enumerate(entries) if e["kind"] in ("press", "mouse")]
    first_input = inputs[0] if inputs else None
    out = {}
    for m in MILESTONES:
        good = [e for i, e in enumerate(entries) if e["kind"] == "mark" and e.get("event") == m
                and not apc.mark_problems(sess, entries, i, e, captured, first_input)]
        if good:
            out[m] = {"files": list(good[-1]["evidence"]), "note": good[-1].get("note", "")}
    return out


def spread(items, n):
    """n items spread evenly across the list, keeping order."""
    if n <= 0:
        return []
    if len(items) <= n:
        return list(items)
    step = (len(items) - 1) / (n - 1) if n > 1 else 0
    return [items[round(i * step)] for i in range(n)]


def capture_order(rel):
    """Sort key for visual_playtest frame names ('NN_label.png', '100_label.png' after '99_'): leading integer, then name."""
    name = Path(rel).name
    m = re.match(r"(\d+)", name)
    return (int(m.group(1)) if m else 10**9, str(rel))


def gate_receipt_ok(session):
    """True only for a visual_playtest folder whose gate passed (gate.ok valid for the current checklist)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import visual_playtest as vp  # the gate stays the single source of truth
    return vp.receipt_valid(session)


def gate_burst_groups(session, names):
    """label -> frame names of each idle burst. Uses manifest.json's burst flag, else the _burst_ file name."""
    groups = {}
    try:
        man = json.loads((Path(session) / "manifest.json").read_text(encoding="utf-8-sig"))
        if isinstance(man, dict):
            man = [man]
        for m in man or []:
            if m.get("burst") and m.get("file") in names:
                groups.setdefault(m["burst"], []).append(m["file"])
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    seen = {f for g in groups.values() for f in g}
    for n in names:  # fall back for frames the manifest does not flag
        mt = re.match(r"\d+_burst_(.+)_\d+\.png$", n)
        if mt and n not in seen:
            groups.setdefault(mt.group(1), []).append(n)
    return groups


def pick_gate_frames(session, extra, n):
    """Stills first (they are the gameplay beats); idle-burst frames only fill what is left, one per burst."""
    groups = gate_burst_groups(session, set(extra))
    burst = {f for g in groups.values() for f in g}
    stills = [f for f in extra if f not in burst]
    picked = spread(stills, n)
    room = n - len(picked)
    if room > 0:
        mids = [sorted(g, key=capture_order)[len(g) // 2] for g in groups.values()]
        picked += spread(sorted(mids, key=capture_order), room)
    return sorted(picked, key=capture_order)


def build_packet(session, page, out, video=None, max_frames=12, probe=probe_video, gate_check=gate_receipt_ok):
    session, out = Path(session), Path(out)
    gate = is_gate_folder(session)
    if gate:  # no journal, so no marks: the packet is a spread of the gate's own frames (stages/03_playtest/references/judge-pass.md)
        if not gate_check(session):
            raise UsageError(f"{session} is a visual_playtest folder whose gate has not passed (no valid gate.ok): "
                             "finish the checklist and run `visual_playtest.py gate` first")
        marks = {}
    else:
        _read_journal(session)  # clear error if this is not a session folder
        marks = marked_evidence(session)
        missing = [m for m in MILESTONES if m not in marks]
        if missing:
            raise UsageError("the playtest has no usable mark for: " + ", ".join(missing) + " (run the gate first)")
    pc = check_page(page, video=video, probe=probe)

    chosen = []  # session-relative paths, marked evidence first
    for m in marks:
        for f in marks[m]["files"]:
            if f not in chosen:
                chosen.append(f)
    subs = (".",) if gate else ("frames",)
    extra = sorted((str(p.relative_to(session)) for sub in subs if (session / sub).is_dir()
                    for p in (session / sub).iterdir() if p.suffix.lower() == ".png" and "contact" not in p.name.lower()),
                   key=capture_order)
    extra = [f for f in extra if f not in chosen]
    room = max(0, max_frames - len(chosen))
    chosen += pick_gate_frames(session, extra, room) if gate else spread(extra, room)

    fdir = out / "frames"
    sf = (session / "frames").resolve()
    if out.resolve() == session.resolve() or fdir.resolve() == sf or sf.is_relative_to(fdir.resolve()) \
            or (gate and fdir.resolve().parent == session.resolve()):
        raise UsageError(f"--out {out} would overwrite the playtest session's own frames; use a separate folder "
                         "such as SESSION/judge")
    if fdir.is_dir() and (out / "packet.json").is_file():  # only a folder this tool made earlier is cleared
        shutil.rmtree(fdir)
    fdir.mkdir(parents=True, exist_ok=True)
    files = []
    for rel in chosen:
        src = session / rel
        if not src.is_file():
            raise UsageError(f"evidence file {rel} is missing from {session}")
        name = rel.replace("/", "__")
        shutil.copy2(src, fdir / name)
        files.append({"name": name, "source": rel, "kind": "clip" if src.suffix.lower() in VIDEO_EXT else "frame",
                      "milestone": next((m for m in marks if rel in marks[m]["files"]), None)})
    packet = {"files": files, "marks": marks, "source_kind": "visual_playtest" if gate else "agent_playtest", "criteria": list(CRITERIA), "page": pc}
    (out / "packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (out / "page-check.json").write_text(json.dumps(pc, indent=2), encoding="utf-8")
    (out / "report-template.json").write_text(json.dumps(report_template(files), indent=2), encoding="utf-8")
    (out / "prompt.md").write_text(rubric_prompt(files, marks, pc), encoding="utf-8")
    return packet


def report_template(files):
    first = files[0]["name"] if files else "frames/example.png"
    return {
        "scores": {c: {"score": 0, "evidence": "One plain sentence saying what you saw.", "file": first}
                   for c in CRITERIA},
        "page_notes": "One or two plain sentences on the itch page draft, or empty.",
        "top_fixes": ["Up to three plain sentences, most useful first."],
    }


def rubric_prompt(files, marks, pc):
    lines = [
        "# Judge pass: rate this build like an Epic AI MegaJam judge",
        "",
        "You are a judge in the 2026 Epic AI MegaJam. You have never seen this game. " + (
            "The playtest agent already proved the build can be won, lost and restarted."
            if marks else
            "The build passed the automated capture gate, but this packet has no win, lose or restart evidence: "
            "do not assume the build can be won."),
        "Your job is a fair, strict rating. Do not open the",
        "source, the GDD or the brief. Use only the files listed below and the page check.",
        "",
        "## Criteria (Official Rules, Rule 9): score each 1 to 5, whole numbers",
        "",
    ]
    for c in CRITERIA:
        lines.append(f"- `{c}`: {LABELS[c]}")
    lines += [
        "",
        "Scale: 1 broken or missing, 2 weak, 3 fine for a 4-day jam, 4 strong, 5 stands out among all entries.",
        "Only these seven official criteria are scored. Claims from videos that the rules do not contain (a",
        "pre-screen, a default-texture rule) are UNTESTED and unofficial: do not score them.",
        "Disclosed AI use is context only: it must not raise or lower a score by itself.",
        "Sourced assets are not scored. Do not give a 5 without a frame that shows why.",
        "",
        "## Evidence you may cite (open each PNG with Read; a score with no matching file is rejected)",
        "",
    ]
    for f in files:
        tag = f" ({f['milestone']} evidence)" if f["milestone"] else ""
        lines.append(f"- `{f['name']}`: {f['kind']}{tag}")
    for m, v in marks.items():
        if v["note"]:
            lines.append(f"- tester note for {m}: {v['note']}")
    lines += ["", "## Itch page draft checks (already run)", ""]
    for c in pc["checks"]:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}")
    lines += [
        "",
        "## Reply",
        "",
        "Reply with one JSON object in a ```json fence and nothing else. Shape: see report-template.json.",
        "Each score needs `score` (1-5), `evidence` (exactly one plain sentence, at most 40 words) and `file`",
        "(one name from the list above). Add `page_notes` and `top_fixes` (at most 3).",
        "Do not invent anything you cannot see in a file.",
        "",
    ]
    return "\n".join(lines)


# ---------- report parsing ----------

def extract_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    cand = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1] if "{" in text else ""
    try:
        d = json.loads(cand)
    except ValueError:
        raise ValueError("no JSON object found in the report") from None
    if not isinstance(d, dict):
        raise ValueError("the report JSON is not an object")
    return d


def sentences(s):
    return [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", s.strip()) if p]


def validate_report(d, packet=None):
    """Return (normalized, problems)."""
    problems = []
    scores = d.get("scores")
    if not isinstance(scores, dict):
        return None, ["report has no `scores` object"]
    names = {f["name"] for f in packet["files"]} if packet else None
    norm = {}
    for c in CRITERIA:
        e = scores.get(c)
        if not isinstance(e, dict):
            problems.append(f"{c}: missing")
            continue
        sc, ev, fl = e.get("score"), e.get("evidence"), e.get("file")
        if isinstance(sc, bool) or not isinstance(sc, int) or not 1 <= sc <= 5:
            problems.append(f"{c}: score must be a whole number 1-5, got {sc!r}")
        if not isinstance(ev, str) or not ev.strip():
            problems.append(f"{c}: evidence sentence is empty")
            ev = ev if isinstance(ev, str) else ""
        else:
            ev = " ".join(ev.split())
            if len(sentences(ev)) != 1:
                problems.append(f"{c}: evidence must be one sentence, got {len(sentences(ev))}")
            if len(ev.split()) > 40:
                problems.append(f"{c}: evidence is longer than 40 words")
        if not isinstance(fl, str):
            problems.append(f"{c}: file must be one packet file name, got {fl!r}")
        elif names is not None and fl not in names:
            problems.append(f"{c}: file {fl!r} is not in the packet")
        norm[c] = {"label": LABELS[c], "score": sc, "evidence": ev, "file": fl}
    extra = sorted(set(scores) - set(CRITERIA))
    if extra:
        problems.append("unknown criteria: " + ", ".join(extra))
    fixes = d.get("top_fixes", [])
    if not isinstance(fixes, list) or not all(isinstance(x, str) for x in fixes):
        problems.append("top_fixes must be a list of strings")
        fixes = []
    elif len(fixes) > 3:
        problems.append("top_fixes has more than 3 items")
    ok_scores = [v["score"] for v in norm.values()
                 if isinstance(v["score"], int) and not isinstance(v["score"], bool) and 1 <= v["score"] <= 5]
    total = sum(ok_scores) if len(ok_scores) == len(CRITERIA) else None
    notes = d.get("page_notes", "")
    out = {"scores": norm, "total": total, "max": 5 * len(CRITERIA),
           "page_notes": notes if isinstance(notes, str) else "", "top_fixes": fixes,
           "page_check": packet.get("page") if packet else None, "problems": problems, "ok": not problems}
    return out, problems


def render_md(r):
    """The block for the owner handoff message (goes before the build link)."""
    lines = ["**Judge pass** (a second agent rated the packaged build on the Rule 9 criteria, 1-5)", ""]
    if r["total"] is not None:
        lines.append(f"Total {r['total']}/{r['max']}.")
        lines.append("")
    for c in CRITERIA:
        v = r["scores"].get(c)
        if v:
            lines.append(f"- {v['label']}: {v['score']}. {v['evidence']} ({v['file']})")
    pc = r.get("page_check")
    if pc:
        bad = [c for c in pc["checks"] if not c["ok"]]
        lines += ["", "Itch page draft: " + ("all checks pass." if not bad else
                  "; ".join(f"{c['name']} FAIL ({c['detail']})" for c in bad))]
    if r.get("page_notes"):
        lines.append(r["page_notes"])
    if r.get("top_fixes"):
        lines += ["", "Top fixes:"] + [f"{i}. {x}" for i, x in enumerate(r["top_fixes"], 1)]
    if r["problems"]:
        lines += ["", "REPORT PROBLEMS (do not trust these scores): " + "; ".join(r["problems"])]
    return "\n".join(lines) + "\n"


# ---------- cli ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("packet")
    s.add_argument("--session", required=True)
    s.add_argument("--page", required=True)
    s.add_argument("--video")
    s.add_argument("--out", default="judge-packet")
    s.add_argument("--max-frames", type=int, default=12)
    s = sub.add_parser("parse")
    s.add_argument("report")
    s.add_argument("--packet", help="packet folder made by `packet`; checks cited files and adds the page check")
    s.add_argument("--out", help="also write the normalized JSON here")
    s.add_argument("--md", action="store_true", help="print the owner-handoff block instead of JSON")
    s = sub.add_parser("page-check")
    s.add_argument("page")
    s.add_argument("--video")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return EXIT_USAGE if e.code else 0
    try:
        if a.cmd == "packet":
            pk = build_packet(a.session, a.page, a.out, video=a.video, max_frames=a.max_frames)
            print(f"packet in {a.out}: {len(pk['files'])} file(s); page checks "
                  f"{'pass' if pk['page']['ok'] else 'FAIL'}. Give prompt.md and frames/ to the judge agent.")
            return EXIT_OK if pk["page"]["ok"] else EXIT_FAIL
        if a.cmd == "page-check":
            pc = check_page(a.page, video=a.video)
            print(json.dumps(pc, indent=2))
            return EXIT_OK if pc["ok"] else EXIT_FAIL
        rp = Path(a.report)
        if not rp.is_file():
            raise UsageError(f"report {rp} does not exist")
        packet = None
        if a.packet:
            pj = Path(a.packet) / "packet.json"
            if not pj.is_file():
                raise UsageError(f"{pj} does not exist")
            packet = json.loads(pj.read_text(encoding="utf-8"))
        try:
            data = extract_json(rp.read_text(encoding="utf-8"))
        except ValueError as e:
            raise UsageError(str(e)) from None
        res, _ = validate_report(data, packet)
        if res is None:
            raise UsageError("report has no `scores` object")
        if a.out:
            Path(a.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(render_md(res) if a.md else json.dumps(res, indent=2))
        return EXIT_OK if res["ok"] else EXIT_FAIL
    except UsageError as e:
        print(f"judge_pass: {e}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())

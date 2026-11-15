#!/usr/bin/env python3
"""Hand-ask question box for Epic's Developer Assistant (tooling only, Rule 7(h)).

Epic's Supplemental Terms forbid automated access to the Assistant (website or in-editor panel), and the site
is behind a bot check. So agents NEVER drive it. They queue a question here; the OWNER asks it by hand and
pastes the reply under that entry's "Answer" heading in the Markdown note (open it in Obsidian). Answers are
unverified hints: check them against the engine source or in the editor before relying on them.

Agents:  add "question" --context "what I already checked" --from NAME
         list [--open|--answered] [--json]   count --open   show Q-001
Owner:   next   (prints the oldest open question and opens the Assistant page; you then type it yourself)

Queue file: $MEGAJAM_EPIC_ASK_FILE, else the Obsidian note named in DEFAULT_FILE. Only ever appended to.
Answered = the text under an entry's "### Answer" heading (HTML comments ignored) is non-empty.
Known race: Obsidian saves whole files without flock, so an add landing while the owner has unsaved edits can be
lost on Obsidian's next save. `add` prints the id; if a later `show` says "no such question", re-add.
"""
import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_FILE = Path("~/Documents/Obsidian/Work Hub Clean/Projects/megajam/Epic Assistant questions.md")
ASSISTANT_URL = "https://dev.epicgames.com/community/assistant/unreal-engine"
MAX_QUESTION = 1500
MAX_CONTEXT = 600
MAX_NAME = 40
PT = ZoneInfo("America/Los_Angeles")

HEADER = """# Epic Assistant questions (hand-ask queue)

**Owner: what to do.** For each entry below with an empty Answer, open
https://dev.epicgames.com/community/assistant/unreal-engine (or the in-editor Unreal Assistant), type the
question yourself, and paste the reply under that entry's `### Answer` heading. That is all; no command needed.
(`python3 scripts/epic_ask.py next` prints the oldest open one and opens the page.)

**Agents: never drive the site or the editor panel** (Epic's Supplemental Terms ban automated access). Queue
with `python3 scripts/epic_ask.py add`, keep working, read the reply later with `show Q-NNN`. Answers are
unverified hints; verify before relying on them. Do not reflow entries; new ones are appended at the end.
Never delete an entry; answer `n/a` (and why) instead.
Everything after an entry's `### Answer` heading up to the next `## Q-` heading is read as its answer; put owner
notes in `<!-- -->` comments, never after the last entry.
"""

SECRET_RES = [
    re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bxai-[A-Za-z0-9]{16,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"://[^/\s:@]+:[^@\s]{4,}@"),  # credentials embedded in a URL
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"),
    # .env style lines: SOMETHING_KEY=value, api_key: value
    re.compile(r"\b[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Za-z0-9_]*\s*=\s*\S{6,}", re.I),
    re.compile(r"^\s*[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Za-z0-9_]*\s*:\s*\S{6,}", re.I | re.M),
    re.compile(r"\b(api[_-]?key|token|secret|passw(?:or)?d)\s*[=:]\s*['\"]?[A-Za-z0-9/+_\-]{12,}", re.I),
]

HEAD_RE = re.compile(r"^## (Q-\d+)\s*$")
ANSWER_RE = re.compile(r"^###\s+Answer\b")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def ask_file():
    env = os.environ.get("MEGAJAM_EPIC_ASK_FILE")
    return Path(env) if env else DEFAULT_FILE


def now_pt():
    return datetime.now(PT)


def looks_secret(text):
    return any(r.search(text) for r in SECRET_RES)


def fence_for(text):
    longest = max([len(m) for m in re.findall(r"`+", text)] + [0])
    return "`" * max(3, longest + 1)


def one_line(s):
    return re.sub(r"\s+", " ", s).strip()


def outside_fences(block):
    """Yield (index, line) for lines not inside a ``` or ~~~ fence (closer: same char, at least as long)."""
    fence = None
    for i, ln in enumerate(block):
        if fence is None:
            m = re.match(r"^(`{3,}|~{3,})", ln)
            if m:
                fence = m.group(1)
                continue
            yield i, ln
        elif re.match(r"^" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", ln):
            fence = None


def parse(text):
    """Tolerant parse. Returns entries: id, time, who, question, context, answer. Hand edits never raise."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if HEAD_RE.match(ln)]
    entries = []
    for n, s in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        block = lines[s:end]
        e = {"id": HEAD_RE.match(block[0]).group(1), "time": "", "who": "", "question": "", "context": "", "answer": ""}
        a_idx = next((i for i, ln in outside_fences(block) if ANSWER_RE.match(ln)), None)
        pre = block[1:a_idx] if a_idx is not None else block[1:]
        post = block[a_idx + 1:] if a_idx is not None else []
        for ln in pre:
            m = re.match(r"^\s*[-*]\s*\*\*Time \(PT\):\*\*\s*(.*)$", ln)
            if m:
                e["time"] = m.group(1).strip()
            m = re.match(r"^\s*[-*]\s*\*\*Asked by:\*\*\s*(.*)$", ln)
            if m:
                e["who"] = m.group(1).strip()
        q_lines, i = [], 0
        while i < len(pre):
            m = re.match(r"^(`{3,}|~{3,})", pre[i])
            if m:
                fence, j = m.group(1), i + 1
                while j < len(pre) and pre[j].rstrip() != fence:
                    q_lines.append(pre[j])
                    j += 1
                i = j + 1
                break
            i += 1
        e["question"] = "\n".join(q_lines).strip()
        for k, ln in outside_fences(pre):
            m = re.match(r"^\*\*Context:\*\*\s*(.*)$", ln)
            if m:
                e["context"] = "\n".join([m.group(1)] + pre[k + 1:]).strip()
                break
        e["answer"] = COMMENT_RE.sub("", "\n".join(post)).strip()
        entries.append(e)
    return entries


def read_entries(path):
    try:
        return parse(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        return []


def max_id(text):
    return max((int(m.group(1)) for ln in text.splitlines() if (m := re.match(r"^## Q-(\d+)\s*$", ln))), default=0)


def seq_file(path):
    """Dotfile high-water mark next to the note, so an id is never reused after the owner deletes an entry."""
    return path.with_name("." + path.stem + ".seq")


def render(qid, who, question, context):
    safe = "\n".join(("    " + ln) if re.match(r"^\s*## Q-\d+", ln) else ln for ln in question.splitlines())
    f = fence_for(safe)
    ctx = one_line(context) if context else "(none given)"
    return (
        f"\n## {qid}\n"
        f"- **Time (PT):** {now_pt().strftime('%Y-%m-%d %H:%M')}\n"
        f"- **Asked by:** {one_line(who) or 'unknown'}\n\n"
        f"### Question (copy this)\n\n{f}text\n{safe}\n{f}\n\n"
        f"**Context:** {ctx}\n\n"
        f"### Answer\n\n<!-- Owner: paste the Assistant's reply below this line. Leave empty until answered. -->\n\n"
    )


def notify(qid, who, question):
    exe = shutil.which("notify-send")
    if not exe:
        return
    try:
        subprocess.run([exe, "-a", "megajam", "--", f"Epic Assistant question {qid}", f"{who}: {question[:140]}"],
                       timeout=5, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def cmd_add(args):
    q = args.question.strip()
    ctx = (args.context or "").strip()
    who = one_line(args.who or "unknown")[:MAX_NAME]
    if not q:
        return err("empty question")
    if len(q) > MAX_QUESTION:
        return err(f"question is {len(q)} chars; the cap is {MAX_QUESTION}. Shorten it (short snippets of our own code only).")
    if len(ctx) > MAX_CONTEXT:
        return err(f"context is {len(ctx)} chars; the cap is {MAX_CONTEXT}.")
    if looks_secret("\n".join([q, ctx, who])):
        return err("refused: this looks like it contains a secret (key, token, password or .env line). Never submit those.")
    path = ask_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            text = fh.read()
            if not text.strip():
                fh.write(HEADER)
                text = HEADER
            elif not text.endswith("\n"):
                fh.write("\n")
            seq = seq_file(path)
            try:
                hwm = int(seq.read_text().strip() or 0)
            except (FileNotFoundError, ValueError):
                hwm = 0
            n = max(hwm, max_id(text)) + 1
            qid = "Q-%03d" % n
            seq.write_text(str(n))
            fh.write(render(qid, who, q, ctx))
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    notify(qid, who, q)
    print(qid)
    return 0


def err(msg):
    print("epic_ask: " + msg, file=sys.stderr)
    return 2


def select(args):
    es = read_entries(ask_file())
    if getattr(args, "open", False):
        es = [e for e in es if not e["answer"]]
    elif getattr(args, "answered", False):
        es = [e for e in es if e["answer"]]
    return es


def cmd_list(args):
    es = select(args)
    if args.json:
        print(json.dumps([dict(e, answered=bool(e["answer"])) for e in es], indent=2))
        return 0
    for e in es:
        state = "answered" if e["answer"] else "OPEN"
        print(f"{e['id']}  {state:8}  {e['time']}  {e['who']}: {one_line(e['question'])[:90]}")
    return 0


def cmd_count(args):
    if not args.open:
        args.answered = False
    print(len(select(args)))
    return 0


def find(qid):
    qid = qid.upper()
    m = re.fullmatch(r"Q?-?(\d+)", qid)
    if m:
        qid = "Q-%03d" % int(m.group(1))
    return next((e for e in read_entries(ask_file()) if e["id"].upper() == qid), None)


def cmd_show(args):
    e = find(args.id)
    if not e:
        return err(f"no such question: {args.id}")
    print(f"{e['id']}  {e['time']} PT  asked by {e['who']}")
    print("\nQUESTION:\n" + e["question"])
    if e["context"]:
        print("\nCONTEXT:\n" + e["context"])
    if e["answer"]:
        print("\nANSWER (from the owner, pasted from Epic's Assistant):\n" + e["answer"])
        print("\nREMINDER: this answer is an UNVERIFIED hint and may be wrong. Verify it against the engine source "
              "or in the editor before relying on it, and cite " + e["id"] + " where you use it.")
    else:
        print("\nNo answer yet. Keep working on something else and check again later.")
    return 0


def cmd_next(args):
    open_ = [e for e in read_entries(ask_file()) if not e["answer"]]
    if not open_:
        print("No open questions.")
        return 0
    e = open_[0]
    print(f"{e['id']}  asked by {e['who']} at {e['time']} PT ({len(open_)} open)\n")
    print(e["question"])
    if e["context"]:
        print("\nContext: " + e["context"])
    print(f"\nType it into the Assistant yourself, then paste the reply under '### Answer' of {e['id']} in:\n  {ask_file()}")
    print(f"Page: {ASSISTANT_URL}")
    exe = shutil.which("xdg-open")
    if exe and not args.no_open:
        subprocess.Popen([exe, ASSISTANT_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="queue a question (agents)")
    a.add_argument("question")
    a.add_argument("--context", default="", help="what you already checked")
    a.add_argument("--from", dest="who", default="unknown", help="your agent name")
    a.set_defaults(fn=cmd_add)
    for name, fn in (("list", cmd_list), ("count", cmd_count)):
        s = sub.add_parser(name)
        g = s.add_mutually_exclusive_group()
        g.add_argument("--open", action="store_true")
        if name == "list":
            g.add_argument("--answered", action="store_true")
            s.add_argument("--json", action="store_true")
        s.set_defaults(fn=fn)
    s = sub.add_parser("show", help="read a question and its answer")
    s.add_argument("id")
    s.set_defaults(fn=cmd_show)
    s = sub.add_parser("next", help="owner: print the oldest open question and open the Assistant page")
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(fn=cmd_next)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

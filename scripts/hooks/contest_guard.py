#!/usr/bin/env python3
"""Claude Code PreToolUse hook: MegaJam contest guard (stdlib only).

Reads the hook JSON on stdin. Acts only for Bash calls whose cwd is inside the MegaJam repo (worktrees
included); anywhere else it exits 0 silently. A denied command prints the reason to stderr and exits 2.
Default is allow. Fails open (exit 0) on empty or unparseable input.

Wire it in ~/.claude/settings.json only (never in this repo):  python3 <path>/scripts/hooks/contest_guard.py
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = "~/Projects/megajam"

GENERATORS = {"nexus-image", "nexus-3d", "nexus-upscale", "nexus-video", "nexus-music", "nexus-style",
              "gen_asset.py", "gen_music.py", "modly", "comfyui"}
FETCHERS = {"curl", "wget", "http", "https", "aria2c", "git", "pip", "pip3", "uv", "npx"}
STORE = r"mixamo\.com|fab\.com|sketchfab\.com"
CLOUD_AI = (r"meshy\.ai|tripo3d\.ai|api\.tripo|api\.openai\.com|api\.x\.ai|fal\.run|fal\.ai|fal\.media|"
            r"hyper3d\.(com|ai)|"
            r"api\.stability\.ai|replicate\.com|elevenlabs\.io|suno\.(com|ai)|api\.suno")
CLOUD = f"{STORE}|{CLOUD_AI}"

# (name, reason). Matching logic is in check_segment(); this is the one place the rules are described.
RULES = {
    "nexus-image-model": "nexus-image needs --model krea-2-turbo; Nexus's default Qwen-Image 2.1 is non-commercial (Rule 15(b), stages/00_prep/references/license-check-modly-foundrylab.md)",
    "banned-model": "qwen-image*, ultrasharp and hunyuan are non-commercial or territory-restricted outputs (Rule 15(b): qwen-research, CC BY-NC-SA, Tencent license 5(c))",
    "no-3d": "3D generation in MegaJam is allowed only as `nexus-3d ... --model triposplat` (MIT TripoSplat) or a cloud adapter through `gen_asset.py --3d-provider meshy|tripo|hyper3d|fal`. Plain nexus-3d defaults to Hunyuan3D, whose license bars outputs in EU/UK/KR (license 5(c), Rule 15(b)); direct modly / 127.0.0.1:8765 calls are not allowed",
    "cloud-source": "cloud AI hosts (Meshy, Tripo, fal, Hyper3D, OpenAI, xAI, Stability, Replicate, ElevenLabs, Suno) are allowed in MegaJam (owner 2026-11-07: anything the Official Rules allow), but only through a repo adapter that checks the provider's key and *_TERMS_REVIEWED date, never by raw curl/wget/git: concept images `scripts/gen_asset.py --provider auto|gpt|grok|fal`, 3D `scripts/gen_asset.py --3d-provider auto|meshy|tripo|hyper3d|fal`. A provider without an adapter needs one first (pre-jam, Rule 7(h), declared). See _config/reference/ai-providers.md",
    "store-asset": "no automatic downloads from asset stores (Mixamo, Fab, Sketchfab). Store assets are allowed only if licensed and listed as sourced assets (Rule 15(c)): get it by hand, check the licence, and list it in the sourced-assets doc. Sourced assets earn no originality points (Rule 7(a))",
    "model-download": "no new model downloads (hf download / huggingface-cli download / snapshot_download): the jam pipeline is local and pre-staged (win-plan D5, Rule 15(b))",
    "uc2-import": "nothing from UC2/UT2004 may enter this repo: third-party IP and pre-jam content (Rules 8, 15(d), 7(h))",
}


def segments(command):
    """Split a shell command into argv lists (very simple: ; && || | newline)."""
    out = []
    for part in re.split(r"\|\||&&|[;|\n]", command):
        try:
            argv = shlex.split(part, comments=False)
        except ValueError:
            argv = part.split()
        if argv:
            out.append(argv)
    return out


def strip_prefix(argv):
    """Drop env assignments and runners; return (env dict, remaining argv)."""
    env = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", a)
        if m:
            env[m.group(1)] = m.group(2)
        elif os.path.basename(a) in ("env", "time", "nice", "timeout", "uv", "run", "python", "python3", "python3.12", "quiet", "command", "nohup", "exec", "setsid", "builtin", "--"):
            pass
        else:
            break
        i += 1
    return env, argv[i:]


def uses_triposplat(rest):
    """True when the argv selects TripoSplat as its (last) --model: `--model triposplat` or `--model=triposplat`."""
    model = None
    for i, a in enumerate(rest):
        if a == "--model" and i + 1 < len(rest):
            model = rest[i + 1]
        elif a.startswith("--model="):
            model = a.split("=", 1)[1]
    return model == "triposplat"


GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix",
                     "--config-env", "--attr-source"}
GIT_SAFE_SUBCOMMANDS = {"commit", "log", "grep", "show", "diff", "status", "add"}


def git_subcommand(rest):
    """Subcommand of a `git ...` argv, skipping global options (-C DIR, -c K=V, --git-dir=X, --paginate...)."""
    i = 1
    while i < len(rest):
        a = rest[i]
        if not a.startswith("-"):
            return a
        i += 2 if a in GIT_OPTS_WITH_ARG else 1
    return None


def check_segment(argv):
    env, rest = strip_prefix(argv)
    if not rest:
        return None
    exe = os.path.basename(rest[0])
    text = " ".join(argv)
    if exe == "modly" or re.search(r"127\.0\.0\.1:8765|localhost:8765", text):
        return "no-3d"
    if exe in ("nexus-3d", "nexus_3d.py") and not uses_triposplat(rest):
        return "no-3d"
    if exe in GENERATORS:
        if re.search(r"qwen-image|ultrasharp|hunyuan", text, re.I):
            return "banned-model"
        if exe == "nexus-image":
            joined = " ".join(rest)
            if not re.search(r"--model[ =]krea-2-turbo(\s|$)", joined):
                return "nexus-image-model"
    if exe in ("huggingface-cli", "hf") and "download" in rest[1:3]:
        return "model-download"
    if re.search(r"snapshot_download|hf_hub_download", text):
        return "model-download"
    if exe == "git" and any(a == "-c" and i + 1 < len(rest) and rest[i + 1].lower().startswith("alias.")
                            or a.lower().startswith("-calias.") for i, a in enumerate(rest)):
        return "cloud-source"  # aliases can hide a clone or run `!cmd` through a shell
    if exe in FETCHERS and re.search(CLOUD, text, re.I):
        # git is a fetcher in too many ways (clone, fetch-pack, config remote.X.url, aliases) to list;
        # a git command naming a cloud host passes only when its subcommand is a known local one.
        if exe != "git" or git_subcommand(rest) not in GIT_SAFE_SUBCOMMANDS:
            return "store-asset" if re.search(STORE, text, re.I) else "cloud-source"
    if exe in ("cp", "mv", "rsync", "ln", "install", "unzip", "tar") and re.search(r"uc2|ut2004", text, re.I):
        return "uc2-import"
    return None


INTERPRETERS = re.compile(r"^(python[\d.]*|node|nodejs|deno|bun|ruby|perl|php)$")


SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}


def quote_segments(command):
    """Split on unquoted ; & | newline, so `python3 -c "a; b"` stays one segment. Returns (text, end_index)."""
    out, buf, quote, i = [], [], None, 0
    while i < len(command):
        c = command[i]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(command[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c in "'\"":
            quote = c
            buf.append(c)
        elif c == "&" and (command[i - 1:i] == ">" or command[i + 1:i + 2] == ">"):
            buf.append(c)  # redirect (2>&1, &>file), not a separator
        elif c in ";&|\n":
            out.append(("".join(buf), i))
            buf = []
        else:
            buf.append(c)
        i += 1
    out.append(("".join(buf), len(command)))
    return [(t, e) for t, e in out if t.strip()]


def has_unquoted_escape(command):
    """True when a backslash or `#` appears outside quotes. Both can hide a quote from the splitter."""
    quote, i = None, 0
    while i < len(command):
        c = command[i]
        if quote:
            if c == "\\" and quote == '"':
                i += 1
            elif c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c in "\\#" or (c == "$" and command[i + 1:i + 2] in ("'", '"')):
            return True  # also $'..' and $"..": the shell quotes them differently from this splitter
        elif c == "(":
            return True  # any unquoted paren: subshell, zsh =(cmd) and glob qualifiers *(e:'cmd':)
        i += 1
    return False


SAFE_READERS = {"grep", "rg", "cat", "head", "tail", "ls", "echo", "printf", "peek"}
SHELL_SYNTAX = ("$(", "`", "<(", ">(", "<<")  # substitution, process substitution, heredoc / here-string
GIT_EXEC_OPTS = ("--config-env", "--open-files-in-pager", "--ext-diff", "--output")
RG_EXEC_OPTS = ("--pre", "--search-zip", "--hostname-bin")  # --pre also covers --pre-glob
INTERPRETER_DIRS = {"/usr/bin", "/usr/local/bin", "/bin"}


KEYWORDS = {"then", "do", "else", "elif", "if", "while", "until", "time", "!", "{", "}", "(", ")"}


def clean_tokens(text):
    """Raw tokens of one segment minus leading shell keywords. None when the text cannot be parsed (deny)."""
    try:
        tokens = shlex.split(text)
    except ValueError:
        return None
    while tokens and tokens[0] in KEYWORDS:
        tokens.pop(0)
    return tokens


def has_env_prefix(tokens):
    return bool(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]) is not None


def gen_asset_paths():
    own = Path(__file__).resolve().parents[2] / "scripts" / "gen_asset.py"
    return {own, Path(ROOT) / "scripts" / "gen_asset.py"}  # this checkout's own, and the main checkout's


def is_sanctioned_run(tokens, cwd):
    """`python3 <this repo's own scripts/gen_asset.py> plain-args`: the only way to reach a cloud provider."""
    if len(tokens) < 2 or has_env_prefix(tokens):
        return False
    exe = tokens[0]
    if "/" in exe and (os.path.dirname(exe) not in INTERPRETER_DIRS):
        return False
    if not re.match(r"^python3[\d.]*$", os.path.basename(exe)):
        return False
    path = Path(os.path.realpath(Path(cwd or ROOT) / tokens[1]))
    return path in {Path(os.path.realpath(p)) for p in gen_asset_paths()} \
        and not any(t.startswith(("<", "|")) for t in tokens[2:])


def git_exec_option(t):
    """A git option that can start a program. git accepts unique prefixes of long options, so any
    abbreviation (3+ chars, e.g. --op, --ope) of a denied long option counts."""
    if t.startswith("--"):
        name = t.split("=", 1)[0]
        return t.startswith("--open") or len(name) >= 3 and any(d.startswith(name) for d in GIT_EXEC_OPTS + ("--open-files-in-pager",))
    return re.match(r"^-[^-]*O", t) is not None


def is_safe_reader(tokens, piped_out):
    """A known bare-name command that only reads/prints (git commit/log/diff..., grep, cat, ls, echo not piped on)."""
    if not tokens or has_env_prefix(tokens):
        return not tokens
    exe = tokens[0]
    if exe == "git":
        if len(tokens) < 2 or tokens[1] not in GIT_SAFE_SUBCOMMANDS:  # no global options before the subcommand
            return False
        return not any(git_exec_option(t) for t in tokens[2:])
    if exe == "rg":
        return not any(t.startswith(RG_EXEC_OPTS) or (re.match(r"^-[^-]", t) and "z" in t) for t in tokens[1:])
    if exe in ("echo", "printf"):
        return not piped_out
    return exe in SAFE_READERS


def cloud_allowlist(command, cwd=None):
    """When the command names a cloud AI / store host, deny unless every segment is the sanctioned gen_asset.py run
    or a known read-only command. Commands that name no cloud host return None (today's behaviour).

    Residual risk, accepted: variable indirection (U=...; curl $U), split strings ('api.me' 'shy.ai'),
    and writing a file then running it.
    """
    if not re.search(CLOUD, command, re.I):
        return None
    deny = "store-asset" if re.search(STORE, command, re.I) and not re.search(CLOUD_AI, command, re.I) else "cloud-source"
    if any(s in command for s in SHELL_SYNTAX) or has_unquoted_escape(command):
        return deny
    piped_in = False
    for text, end in quote_segments(command):
        tokens = clean_tokens(text)
        if tokens is None:
            return deny
        piped_out = command[end:end + 1] == "|" and command[end + 1:end + 2] != "|"
        was_piped_in, piped_in = piped_in, piped_out
        if not tokens:
            continue
        if is_sanctioned_run(tokens, cwd) and not was_piped_in:
            continue
        if not is_safe_reader(tokens, piped_out):  # every piece, host named in it or not
            return deny
    return None


def evaluate(command, cwd=None):
    """Return (rule_name, reason) for a denied command, else None."""
    rule = cloud_allowlist(command, cwd)
    if rule:
        return rule, RULES[rule]
    for argv in segments(command):
        rule = check_segment(argv)
        if rule:
            return rule, RULES[rule]
    return None


def in_megajam(cwd):
    if not cwd:
        return False
    real = os.path.realpath(cwd)
    return real == ROOT or real.startswith(ROOT + os.sep)


def main():
    try:
        data = json.loads(sys.stdin.read())
        if data.get("tool_name") != "Bash" or not in_megajam(data.get("cwd")):
            return 0
        command = (data.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0
    hit = evaluate(command, data.get("cwd"))
    if hit:
        print(f"contest_guard: blocked [{hit[0]}]: {hit[1]}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

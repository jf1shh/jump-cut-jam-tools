#!/usr/bin/env python3
"""Local VLM judge for one playtest frame (T-20261108-27). Works without ComfyUI.

Sends a frame PNG (base64) to an OpenAI-compatible chat endpoint (default: Lemonade on
http://127.0.0.1:13305/v1) and prints a JSON verdict:
  {"hud_readable": bool, "title_line_present": bool, "camera_steady": bool, "issues": [str], "confidence": 0-1}

  vlm_judge.py FRAME.png            judge one frame
  vlm_judge.py vp_r3/               judge the newest .png in that folder
  vlm_judge.py --dry-run FRAME.png  print the request (image shortened), call nothing

Exit codes: 0 pass (all three flags true), 2 fail, 3 unavailable (endpoint down, bad reply, no frame).
Local only: refuses any endpoint that is not loopback unless --allow-remote is given.
Runbook: stages/03_playtest/references/vlm-judge-spike.md. Never run it while another GPU workload is loaded (run gpu-preflight).
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:13305/v1"
DEFAULT_MODEL = os.environ.get("VLM_JUDGE_MODEL", "Qwen3-VL-8B-Instruct-GGUF")  # check `lemonade list`
EXIT_PASS, EXIT_FAIL, EXIT_UNAVAILABLE = 0, 2, 3
FLAGS = ("hud_readable", "title_line_present", "camera_steady")

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "hud_readable": {"type": "boolean"},
        "title_line_present": {"type": "boolean"},
        "camera_steady": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [*FLAGS, "issues", "confidence"],
    "additionalProperties": False,
}

PROMPT = (
    "You are a strict QA judge for one screenshot of a game. Answer ONLY with the JSON object.\n"
    "- hud_readable: true only if every HUD element (health, score, prompts, timers) is fully visible "
    "and its text can be read at normal size. If there is no HUD at all, false.\n"
    "- title_line_present: true only if a title or caption line (game title, level name or objective text) "
    "is visible on screen.\n"
    "- camera_steady: true only if the frame looks like a normal, stable view: not tilted, not clipped "
    "into geometry, not a black or solid-colour screen, not motion-smeared.\n"
    "- issues: short strings, one per problem you see; empty list if none.\n"
    "- confidence: your certainty from 0 to 1. Do not guess: when unsure, lower confidence and say why in issues."
)


class Unavailable(Exception):
    """The judge could not give a verdict (endpoint down, bad reply, no frame). Exit 3."""


def newest_frame(path):
    p = Path(path)
    if p.is_file():
        return p
    if p.is_dir():
        # contact_*.png are burst mosaics written after the frames; they are not game frames
        pngs = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith("contact_")]
        if pngs:
            return max(pngs, key=lambda f: (f.stat().st_mtime_ns, f.name))
        raise Unavailable(f"no .png frame in {p}")
    raise Unavailable(f"{p} does not exist")


def build_request(frame, model=DEFAULT_MODEL, max_tokens=512, image_b64=None):
    if image_b64 is None:
        image_b64 = base64.b64encode(Path(frame).read_bytes()).decode("ascii")
    return {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64}},
        ]}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "frame_verdict", "strict": True, "schema": VERDICT_SCHEMA}},
    }


def shorten(req):
    """A copy of the request with the image bytes cut, for printing."""
    out = json.loads(json.dumps(req))
    for part in out["messages"][0]["content"]:
        if part.get("type") == "image_url":
            u = part["image_url"]["url"]
            part["image_url"]["url"] = u[:40] + f"...[{len(u)} chars]"
    return out


def check_local(endpoint, allow_remote=False):
    host = urllib.parse.urlparse(endpoint).hostname or ""
    if not allow_remote and host not in ("127.0.0.1", "localhost", "::1"):
        raise Unavailable(f"endpoint host '{host}' is not loopback; the judge is local-only (use --allow-remote to override)")


def _direct_open(req, timeout):
    # No proxy: http_proxy in the environment must never redirect the frame away from the local endpoint.
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout)


def post_json(url, body, timeout, opener=_direct_open):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with opener(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise Unavailable(f"endpoint answered HTTP {e.code}") from e
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise Unavailable(f"endpoint not reachable: {getattr(e, 'reason', e)}") from e
    except ValueError as e:
        raise Unavailable("endpoint reply is not JSON") from e


def parse_verdict(reply):
    """Pull the verdict out of a chat reply and validate its shape. Raises Unavailable if unusable."""
    try:
        text = reply["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise Unavailable("reply has no choices[0].message.content") from e
    if isinstance(text, list):  # some servers return content parts
        text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
    text = (text or "").strip()
    if text.startswith("```"):  # tolerate a fenced block
        text = text.strip("`")
        text = text[4:] if text[:4].lower() == "json" else text
    try:
        v = json.loads(text)
    except ValueError as e:
        raise Unavailable("model reply is not valid JSON") from e
    if not isinstance(v, dict):
        raise Unavailable("model reply is not a JSON object")
    for k in FLAGS:
        if not isinstance(v.get(k), bool):
            raise Unavailable(f"verdict field '{k}' missing or not a boolean")
    issues = v.get("issues", [])
    if not isinstance(issues, list) or not all(isinstance(i, str) for i in issues):
        raise Unavailable("verdict field 'issues' is not a list of strings")
    c = v.get("confidence")
    if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 1:
        raise Unavailable("verdict field 'confidence' missing or outside 0..1")
    return {**{k: v[k] for k in FLAGS}, "issues": issues, "confidence": float(c)}


def passed(verdict):
    return all(verdict[k] for k in FLAGS)


def judge(frame, endpoint=DEFAULT_ENDPOINT, model=DEFAULT_MODEL, timeout=300, allow_remote=False,
          opener=_direct_open):
    """Judge one frame (or the newest in a folder). Returns the verdict dict plus 'frame', 'model', 'pass'.
    Raises Unavailable when no verdict can be had."""
    check_local(endpoint, allow_remote)
    f = newest_frame(frame)
    try:
        req = build_request(f, model)
    except OSError as e:
        raise Unavailable(f"cannot read {f}: {e}") from e
    reply = post_json(endpoint.rstrip("/") + "/chat/completions", req, timeout, opener)
    v = parse_verdict(reply)
    return {**v, "pass": passed(v), "frame": f.name, "model": model}


def main(argv=None):
    class _Parser(argparse.ArgumentParser):
        def error(self, message):  # usage errors are "unavailable" (3), never "fail" (2)
            self.print_usage(sys.stderr)
            print(json.dumps({"unavailable": f"usage error: {message}"}))
            raise SystemExit(EXIT_UNAVAILABLE)

    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frame", help="a frame PNG, or a folder (judges its newest .png)")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"OpenAI-compatible base URL (default {DEFAULT_ENDPOINT})")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="model name as Lemonade lists it (env VLM_JUDGE_MODEL)")
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--dry-run", action="store_true", help="print the request (image shortened) and exit 0")
    ap.add_argument("--allow-remote", action="store_true", help="allow a non-loopback endpoint (off by default: local only)")
    a = ap.parse_args(argv)
    try:
        if a.dry_run:
            check_local(a.endpoint, a.allow_remote)
            f = newest_frame(a.frame)
            try:
                body = shorten(build_request(f, a.model))
            except OSError as e:
                raise Unavailable(f"cannot read {f}: {e}") from e
            print(json.dumps({"url": a.endpoint.rstrip("/") + "/chat/completions", "frame": str(f), "body": body},
                             indent=2))
            return EXIT_PASS
        v = judge(a.frame, a.endpoint, a.model, a.timeout, a.allow_remote)
    except Unavailable as e:
        print(json.dumps({"unavailable": str(e)}))
        return EXIT_UNAVAILABLE
    print(json.dumps(v, indent=2))
    return EXIT_PASS if v["pass"] else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())

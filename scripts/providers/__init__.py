"""Concept-image providers for scripts/gen_asset.py, with an automatic fallback chain.

A provider has `name`, `check()` -> (status, detail) that never spends quota, and
`generate(prompt, out_path, timeout)` that writes a PNG or raises ProviderError.
Status is one of READY, NOT_CONFIGURED, DOWN.

Secrets: the xAI key is read from the XAI_API_KEY environment variable only. It is never
printed, logged, stored or put in a provenance sidecar.
"""
import base64
import json
import os
import shutil
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

READY = "ready"
NOT_CONFIGURED = "not configured"
DOWN = "down"

# The one config line for `--provider auto`: tried left to right.
# Speed-first since owner decision 2026-11-07 (not local-only): Grok API (seconds), then local Krea,
# then the ChatGPT plan (~4-6 min). A provider that is not configured or down is skipped.
# fal (FLUX.1 schnell, seconds, paid from fal credit) sits after Grok since 2026-11-10.
AUTO_ORDER = ("grok", "fal", "local", "gpt")

# Seconds allowed per provider before auto moves on. GPT takes ~4-6 min per image.
TIMEOUTS = {"local": 900, "gpt": 600, "grok": 120, "fal": 120}

GPT_BRIDGE = Path.home() / ".claude/skills/gpt-image-bridge/bin/gpt-image-2"
XAI_IMAGE_URL = "https://api.x.ai/v1/images/generations"
XAI_IMAGE_MODEL = "grok-imagine-image-2.0"  # docs.x.ai/docs/guides/image-generation, checked 2026-11-06


class ProviderError(Exception):
    """A provider failed (non-zero exit, timeout, bad response)."""


def run_group(cmd, capture_output=True, text=True, timeout=None, env=None):
    """subprocess.run, but the child gets its own process group and a timeout SIGTERMs (then SIGKILLs)
    the whole group, so grandchildren (codex, ComfyUI) cannot outlive the attempt."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text, env=env,
                            start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except BaseException as exc:  # timeout, Ctrl-C, anything: never orphan the child tree
        for sig, wait in ((signal.SIGTERM, 5), (signal.SIGKILL, None)):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                break
            try:
                proc.communicate(timeout=wait)
                break
            except subprocess.TimeoutExpired:
                continue
            except BaseException:  # a second Ctrl-C: escalate straight to SIGKILL
                continue
        if isinstance(exc, subprocess.TimeoutExpired):
            raise subprocess.TimeoutExpired(cmd, timeout)
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def _run(cmd, timeout, runner=run_group, env=None, ok_codes=(0,)):
    try:
        result = runner(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise ProviderError(f"timed out after {timeout}s")
    except OSError as exc:
        raise ProviderError(str(exc))
    if result.returncode not in ok_codes:
        raise ProviderError(f"exit {result.returncode}: {(result.stderr or result.stdout or '').strip()[-300:]}")
    return result


def _clear(out_path):
    """Delete any file left by an earlier run so a provider cannot be credited for it."""
    Path(out_path).unlink(missing_ok=True)


def _require(out_path):
    if not Path(out_path).exists() or Path(out_path).stat().st_size == 0:
        raise ProviderError("exited 0 but wrote no file")


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _as_png(raw):
    """Return PNG bytes. Real PNGs pass; JPEG/WebP are converted with Pillow if installed; anything
    else (an HTML error page, say) is an error so auto can try the next provider."""
    if raw.startswith(PNG_MAGIC):
        return raw
    if raw.startswith(b"\xff\xd8\xff") or raw[:4] == b"RIFF":
        try:
            import io
            from PIL import Image
            buf = io.BytesIO()
            Image.open(io.BytesIO(raw)).convert("RGB").save(buf, "PNG")
            return buf.getvalue()
        except Exception as exc:
            raise ValueError(f"image is not PNG and could not be converted ({type(exc).__name__})")
    raise ValueError("response is not an image")


class LocalProvider:
    name = "local"

    BUSY_WAIT = 20  # seconds; nexus-image exit 2 = GPU gate momentarily busy

    def __init__(self, model="krea-2-turbo", runner=run_group, sleep=time.sleep, clock=time.monotonic):
        self.model = model
        self.runner = runner
        self.sleep = sleep
        self.clock = clock

    def check(self):
        if not shutil.which("nexus-image"):
            return NOT_CONFIGURED, "nexus-image not on PATH"
        return READY, f"nexus-image found (model {self.model})"

    def generate(self, prompt, out_path, timeout):
        cmd = ["nexus-image", prompt, "--out", str(out_path), "--model", self.model, "--json"]
        _clear(out_path)
        deadline = self.clock() + timeout  # one budget for the first try, the wait and the retry
        result = _run(cmd, timeout, self.runner, ok_codes=(0, 2))
        if result.returncode == 2:  # busy: wait once and retry before auto spends cloud quota
            self.sleep(self.BUSY_WAIT)
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise ProviderError(f"busy, and no time left in the {timeout}s budget to retry")
            result = _run(cmd, remaining, self.runner)
        _require(out_path)
        return {"model": self.model, "command": cmd}


class GptProvider:
    name = "gpt"

    def __init__(self, bridge=GPT_BRIDGE, runner=run_group):
        self.bridge = Path(bridge)
        self.runner = runner

    def check(self):
        if not self.bridge.exists():
            return NOT_CONFIGURED, f"bridge missing: {self.bridge}"
        if not shutil.which("codex"):
            return NOT_CONFIGURED, "codex CLI not on PATH"
        try:
            result = self.runner(["codex", "login", "status"], capture_output=True, text=True, timeout=30)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return DOWN, f"codex login status failed: {exc}"
        text = (result.stdout or "") + (result.stderr or "")
        if "Logged in using ChatGPT" in text:
            return READY, "codex logged in using ChatGPT"
        return NOT_CONFIGURED, "codex is not logged in with ChatGPT (owner runs `codex login`)"

    def generate(self, prompt, out_path, timeout):
        cmd = [str(self.bridge), prompt, str(Path(out_path).resolve())]
        _clear(out_path)
        _run(cmd, timeout, self.runner)
        _require(out_path)
        return {"model": "chatgpt-image (via codex)", "command": [str(self.bridge), "<prompt>", str(out_path)]}


class GrokProvider:
    name = "grok"

    # Licence gate: the owner sets this env var to a date AFTER reading xAI's live terms
    # (_config/reference/ai-providers.md). Without it Grok is "not configured", for auto and for --provider grok.
    TERMS_ENV = "XAI_TERMS_REVIEWED"

    def __init__(self, environ=None, opener=urllib.request.urlopen, connect=socket.create_connection,
                 clock=time.monotonic):
        self.environ = os.environ if environ is None else environ
        self.opener = opener
        self.connect = connect
        self.clock = clock

    def check(self):
        if not self.environ.get("XAI_API_KEY"):
            return NOT_CONFIGURED, "XAI_API_KEY not set"
        if not self.environ.get(self.TERMS_ENV):
            return NOT_CONFIGURED, f"owner has not signed off xAI terms (set {self.TERMS_ENV}=<date> after reading them)"
        try:
            self.connect(("api.x.ai", 443), timeout=5).close()  # TCP only: no API call, no quota
        except OSError as exc:
            return DOWN, f"api.x.ai unreachable: {exc}"
        return READY, f"key present, api.x.ai reachable (model {XAI_IMAGE_MODEL})"

    def generate(self, prompt, out_path, timeout):
        key = self.environ.get("XAI_API_KEY")
        if not key:
            raise ProviderError("XAI_API_KEY not set")
        _clear(out_path)
        body = json.dumps({"model": XAI_IMAGE_MODEL, "prompt": prompt}).encode()
        req = urllib.request.Request(XAI_IMAGE_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        deadline = self.clock() + timeout  # one budget for the API call and the image download
        try:
            with self.opener(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
            item = data["data"][0]
            if item.get("b64_json"):
                raw = base64.b64decode(item["b64_json"])
            else:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError(f"no time left in the {timeout}s budget for the download")
                with self.opener(item["url"], timeout=remaining) as img:
                    raw = img.read()
            png = _as_png(raw)
        except Exception as exc:  # network, HTTP, JSON shape, bad image: all mean "this provider failed"
            raise ProviderError(f"{type(exc).__name__}: {exc}".replace(key, "***"))
        Path(out_path).write_bytes(png)
        return {"model": XAI_IMAGE_MODEL, "command": ["POST", XAI_IMAGE_URL],
                "licence_gate": f"{self.TERMS_ENV}={self.environ.get(self.TERMS_ENV)}"}


def default_providers(model="krea-2-turbo", environ=None):
    from .fal import FalProvider  # late import: fal imports helpers from this module
    return {"local": LocalProvider(model), "gpt": GptProvider(), "grok": GrokProvider(environ=environ),
            "fal": FalProvider(environ=environ)}


def providers_check(providers):
    """One line per provider, in AUTO_ORDER. Spends no quota."""
    lines = []
    for name in AUTO_ORDER:
        status, detail = providers[name].check()
        lines.append(f"{name}: {status} - {detail}")
    return lines


def generate_concept(choice, prompt, out_path, providers, order=AUTO_ORDER, timeouts=TIMEOUTS, log=print):
    """Make the concept image with one provider, or walk `order` when choice == 'auto'.

    Returns {"provider", "model", "command", "seconds", "attempts"}; attempts lists every try
    as {"provider", "outcome", "detail", "seconds"}. Raises ProviderError if nothing worked.
    """
    import time
    names = list(order) if choice == "auto" else [choice]
    attempts = []
    for name in names:
        provider = providers[name]
        status, detail = provider.check()
        if status != READY:
            attempts.append({"provider": name, "outcome": status, "detail": detail, "seconds": 0.0})
            log(f"concept: {name} skipped ({status}: {detail})")
            continue
        start = time.monotonic()
        try:
            info = provider.generate(prompt, out_path, timeouts[name])
        except ProviderError as exc:
            secs = time.monotonic() - start
            attempts.append({"provider": name, "outcome": "failed", "detail": str(exc), "seconds": round(secs, 2)})
            log(f"concept: {name} failed ({exc})")
            continue
        secs = time.monotonic() - start
        attempts.append({"provider": name, "outcome": "ok", "detail": "", "seconds": round(secs, 2)})
        return {**info, "provider": name, "seconds": secs, "attempts": attempts}
    summary = "; ".join(f"{a['provider']}={a['outcome']}" for a in attempts)
    err = ProviderError(f"no provider produced a concept image ({summary})")
    err.attempts = attempts
    raise err

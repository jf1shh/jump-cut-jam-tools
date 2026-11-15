"""Meshy (meshy.ai) cloud image-to-3D adapter for scripts/gen_asset.py. stdlib only.

Flow: POST /openapi/v1/image-to-3d with the stage-1 concept image as a base64 data URI, poll
GET /openapi/v1/image-to-3d/<id> until SUCCEEDED, download model_urls.glb, check the glTF magic.
Docs read 2026-11-07: https://docs.meshy.ai/en/api/image-to-3d (see _config/reference/ai-providers.md, "Meshy").

Secrets: MESHY_API_KEY comes from the env mapping gen_asset passes in. It is sent only to
api.meshy.ai (never to the asset download host), and it is never printed, logged or stored.
Meshy is "not configured" unless the key AND MESHY_TERMS_REVIEWED=<date> are both set.
"""
import base64
import json
import os
import socket
import threading
import time
import urllib.request
from pathlib import Path

NOT_CONFIGURED = "not configured"
READY = "ready"
DOWN = "down"

API_HOST = "api.meshy.ai"
API_BASE = f"https://{API_HOST}/openapi/v1/image-to-3d"
MESHY_MODEL = "latest"  # Meshy's default (meshy-7.1 when checked); recorded in the sidecar
TERMS_ENV = "MESHY_TERMS_REVIEWED"
KEY_ENV = "MESHY_API_KEY"
GLB_MAGIC = b"glTF"
POLL_SECONDS = 5
THREED_TIMEOUT = 900  # total seconds for create + poll + download
BALANCE_URL = f"https://{API_HOST}/openapi/v1/balance"  # GET, spends nothing (docs read 2026-11-12)
POLY_MIN, POLY_MAX = 100, 300_000  # target_polycount range when remeshing a standard model

# The first-error class is shared with the concept providers.
from . import ProviderError, PNG_MAGIC  # noqa: E402
import re  # noqa: E402
import urllib.error  # noqa: E402

UC2_RE = re.compile(r"uc2|ut2004", re.IGNORECASE)
_REPO = Path(__file__).resolve().parents[2]
DEFAULT_ROOTS = (_REPO, Path("~/Projects/megajam"))
MAX_GLB = 300 << 20


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused (would forward the API key)", headers, fp)


_NO_REDIRECT = urllib.request.build_opener(_NoRedirect)


class MeshyProvider:
    name = "meshy"

    def __init__(self, environ=None, opener=None, connect=socket.create_connection,
                 clock=time.monotonic, sleep=time.sleep, poll_seconds=POLL_SECONDS,
                 allowed_roots=None, api_opener=None):
        self.environ = os.environ if environ is None else environ
        # `opener` fetches the pre-signed GLB (redirects fine, no key sent). `api_opener` carries the
        # Bearer key and must never follow a redirect, or urllib would copy the key to the new host.
        self.opener = opener or urllib.request.urlopen
        self.api_opener = api_opener or opener or _NO_REDIRECT.open
        self.allowed_roots = [Path(r).resolve() for r in (allowed_roots if allowed_roots is not None else DEFAULT_ROOTS)]
        self.connect = connect
        self.clock = clock
        self.sleep = sleep
        self.poll_seconds = poll_seconds

    def check(self):
        if not self.environ.get(KEY_ENV):
            return NOT_CONFIGURED, f"{KEY_ENV} not set"
        if not self.environ.get(TERMS_ENV):
            return NOT_CONFIGURED, f"owner has not signed off Meshy terms (set {TERMS_ENV}=<date> after reading them)"
        try:
            self.connect((API_HOST, 443), timeout=5).close()  # TCP only: no API call, no credits
        except OSError as exc:
            return DOWN, f"{API_HOST} unreachable: {exc}"
        return READY, f"key present, {API_HOST} reachable (model {MESHY_MODEL})"

    def _read(self, resp, deadline, limit):
        """Read a whole response within the time budget. The read runs in a daemon thread and is abandoned (and the
        response closed) when the deadline passes, because a socket timeout only bounds each recv, not the transfer."""
        box = {}

        def work():
            try:
                box["value"] = self._read_chunks(resp, deadline, limit)
            except BaseException as exc:  # noqa: BLE001 - re-raised in the caller's thread
                box["error"] = exc

        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        worker.join(max(0.0, deadline - self.clock()))
        if worker.is_alive():
            # close() waits for the reader's lock, so do it off-thread; the abandoned reader ends on its next chunk
            threading.Thread(target=lambda: getattr(resp, "close", lambda: None)(), daemon=True).start()
            raise TimeoutError("time budget used up while reading a response")
        if "error" in box:
            raise box["error"]
        return box["value"]

    def _read_chunks(self, resp, deadline, limit):
        """Read a response in chunks, checking the wall clock between chunks."""
        chunks, size = [], 0
        while True:
            if self.clock() >= deadline:
                raise TimeoutError("time budget used up while reading a response")
            chunk = resp.read(1 << 16)
            if not chunk:
                return b"".join(chunks)
            size += len(chunk)
            if size > limit:
                raise ValueError("response too large")
            chunks.append(chunk)

    def _json(self, req, deadline):
        with self.api_opener(req, timeout=max(1, deadline - self.clock())) as resp:
            return json.loads(self._read(resp, deadline, 1 << 20))

    def _check_image(self, image_path):
        """Only a real PNG/JPEG/WebP inside the repo's work dirs may leave this machine (no UC2/UT2004, no home files)."""
        real = Path(image_path).resolve()
        if UC2_RE.search(str(real)):
            raise ValueError("image path touches a UC2/UT2004 path; refusing to upload")
        if not any(real == r or r in real.parents for r in self.allowed_roots):
            raise ValueError("image is outside the repo work dirs; refusing to upload")
        head = real.read_bytes()[:12]
        if not (head.startswith(PNG_MAGIC) or head.startswith(b"\xff\xd8\xff") or
                (head[:4] == b"RIFF" and head[8:12] == b"WEBP")):
            raise ValueError("image is not a PNG, JPEG or WebP; refusing to upload")
        return real, ("image/png" if head.startswith(PNG_MAGIC) else
                      "image/jpeg" if head.startswith(b"\xff\xd8\xff") else "image/webp")

    def balance(self, timeout=30):
        """Credits left: GET /openapi/v1/balance (spends nothing). Returns the four documented fields or raises ProviderError."""
        key = self.environ.get(KEY_ENV)
        if not key:
            raise ProviderError(f"{KEY_ENV} not set")
        if not self.environ.get(TERMS_ENV):
            raise ProviderError(f"{TERMS_ENV} not set")
        try:
            data = self._json(urllib.request.Request(BALANCE_URL, headers={"Authorization": f"Bearer {key}"}),
                              self.clock() + timeout)
            return {k: data.get(k) for k in ("balance", "monthly_credits", "permanent_credits", "monthly_resets_at")}
        except Exception as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}".replace(key, "***")) from None

    def generate_3d(self, image_path, out_path, timeout=THREED_TIMEOUT, *, target_polycount=None):
        """Make a GLB from `image_path`. Returns {"model","task_id","command","licence_gate"} or raises ProviderError.
        `target_polycount` asks Meshy to remesh to about that many triangles (100..300000); None keeps Meshy's default."""
        key = self.environ.get(KEY_ENV)
        if not key:
            raise ProviderError(f"{KEY_ENV} not set")
        if not self.environ.get(TERMS_ENV):
            raise ProviderError(f"{TERMS_ENV} not set")
        if target_polycount is not None and not (POLY_MIN <= int(target_polycount) <= POLY_MAX):
            raise ProviderError(f"target_polycount {target_polycount} outside {POLY_MIN}..{POLY_MAX}")
        Path(out_path).unlink(missing_ok=True)
        deadline = self.clock() + timeout
        auth = {"Authorization": f"Bearer {key}"}
        task_id = None
        try:
            real, mime = self._check_image(image_path)
            data_uri = f"data:{mime};base64," + base64.b64encode(real.read_bytes()).decode()
            body = json.dumps({"image_url": data_uri, "ai_model": MESHY_MODEL, "should_texture": True,
                               "enable_pbr": True, "target_formats": ["glb"],
                               **({"should_remesh": True, "topology": "triangle",
                                   "target_polycount": int(target_polycount)} if target_polycount is not None else {})}).encode()
            req = urllib.request.Request(API_BASE, data=body, method="POST",
                                         headers={**auth, "Content-Type": "application/json"})
            task_id = self._json(req, deadline)["result"]
            task = {}
            while True:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError(f"task {task_id} not done within the {timeout}s budget")
                task = self._json(urllib.request.Request(f"{API_BASE}/{task_id}", headers=auth), deadline)
                status = task.get("status")
                if status == "SUCCEEDED":
                    break
                if status in ("FAILED", "CANCELED"):
                    err = (task.get("task_error") or {}).get("message") if isinstance(task.get("task_error"), dict) else task.get("task_error")
                    raise RuntimeError(f"task {task_id} {status}: {err}")
                self.sleep(min(self.poll_seconds, max(0, deadline - self.clock())))
            url = (task.get("model_urls") or {}).get("glb")
            if not url:
                raise RuntimeError(f"task {task_id} succeeded but has no glb url")
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise TimeoutError(f"no time left in the {timeout}s budget for the download")
            # The asset URL is pre-signed: no Authorization header, so the key never leaves api.meshy.ai.
            if not str(url).startswith("https://"):
                raise ValueError("glb url is not https")
            with self.opener(url, timeout=remaining) as dl:
                raw = self._read(dl, deadline, MAX_GLB)
            if not raw.startswith(GLB_MAGIC):
                raise ValueError("download is not a GLB (missing glTF header)")
        except Exception as exc:
            err = ProviderError(f"{type(exc).__name__}: {exc}".replace(key, "***"))
            err.task_id = task_id
            raise err
        Path(out_path).write_bytes(raw)
        info = {"model": MESHY_MODEL, "task_id": task_id, "command": ["POST", API_BASE],
                "licence_gate": f"{TERMS_ENV}={self.environ.get(TERMS_ENV)}"}
        if target_polycount is not None:
            info["target_polycount"] = int(target_polycount)
        return info

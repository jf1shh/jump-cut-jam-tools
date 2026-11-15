"""Shared plumbing for the opt-in cloud adapters (fal, Hyper3D Rodin, Tripo). stdlib only.

Same safety rules as providers/meshy.py: the key comes only from the env mapping gen_asset passes in
(~/.config/megajam.env, then the real environment); it is sent only to the vendor's API host, redirects
on keyed requests are refused, downloads go out without the key, every read runs under one hard deadline,
and the key is redacted from every error. A provider is "not configured" unless its key AND its
*_TERMS_REVIEWED=<date> are both set. check() is a TCP connect only: no API call, no credits.
"""
import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from . import DOWN, NOT_CONFIGURED, PNG_MAGIC, READY, ProviderError

UC2_RE = re.compile(r"uc2|ut2004", re.IGNORECASE)
_REPO = Path(__file__).resolve().parents[2]
DEFAULT_ROOTS = (_REPO, Path("~/Projects/megajam"))
GLB_MAGIC = b"glTF"
MAX_GLB = 300 << 20
MAX_IMAGE = 50 << 20
POLL_SECONDS = 5
THREED_TIMEOUT = 900  # total seconds for upload + create + poll + download


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused (would forward the API key)", headers, fp)


_NO_REDIRECT = urllib.request.build_opener(_NoRedirect)


def multipart(fields, files):
    """Encode a multipart/form-data body. fields: [(name, str)]; files: [(name, filename, mime, bytes)]."""
    boundary = "megajam" + uuid.uuid4().hex
    out = []
    for name, value in fields:
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for name, filename, mime, data in files:
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                   f"Content-Type: {mime}\r\n\r\n".encode() + data + b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


class CloudProvider:
    """Base class. Subclasses set name, API_HOST, KEY_ENV, TERMS_ENV (tuple allowed), MODEL, AUTH_SCHEME."""
    name = "cloud"
    API_HOST = ""
    KEY_ENV = ""
    TERMS_ENV = ()
    MODEL = ""
    AUTH_SCHEME = "Bearer"

    def __init__(self, environ=None, opener=None, connect=socket.create_connection,
                 clock=time.monotonic, sleep=time.sleep, poll_seconds=POLL_SECONDS,
                 allowed_roots=None, api_opener=None):
        self.environ = os.environ if environ is None else environ
        # `opener` fetches pre-signed results (no key sent). `api_opener` carries the key and never follows redirects.
        self.opener = opener or urllib.request.urlopen
        self.api_opener = api_opener or opener or _NO_REDIRECT.open
        roots = allowed_roots if allowed_roots is not None else DEFAULT_ROOTS
        self.allowed_roots = [Path(r).resolve() for r in roots]
        self.connect = connect
        self.clock = clock
        self.sleep = sleep
        self.poll_seconds = poll_seconds

    # --- gate -----------------------------------------------------------------------------------
    def terms_envs(self):
        return (self.TERMS_ENV,) if isinstance(self.TERMS_ENV, str) else tuple(self.TERMS_ENV)

    def licence_gate(self):
        return ",".join(f"{t}={self.environ.get(t)}" for t in self.terms_envs())

    def gate(self):
        """(status, detail) for key + terms, without any network."""
        if not self.environ.get(self.KEY_ENV):
            return NOT_CONFIGURED, f"{self.KEY_ENV} not set"
        for t in self.terms_envs():
            if not self.environ.get(t):
                return NOT_CONFIGURED, f"owner has not signed off the terms (set {t}=<date> after reading them)"
        return READY, ""

    def check(self):
        status, detail = self.gate()
        if status != READY:
            return status, detail
        try:
            self.connect((self.API_HOST, 443), timeout=5).close()  # TCP only: no API call, no credits
        except OSError as exc:
            return DOWN, f"{self.API_HOST} unreachable: {exc}"
        return READY, f"key present, {self.API_HOST} reachable (model {self.MODEL})"

    def _key(self):
        status, detail = self.gate()
        if status != READY:
            raise ProviderError(detail)
        return self.environ[self.KEY_ENV]

    # --- I/O --------------------------------------------------------------------------------------
    def _read(self, resp, deadline, limit):
        """Read a whole response within the time budget (a socket timeout bounds each recv, not the transfer)."""
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
            threading.Thread(target=lambda: getattr(resp, "close", lambda: None)(), daemon=True).start()
            raise TimeoutError("time budget used up while reading a response")
        if "error" in box:
            raise box["error"]
        return box["value"]

    def _read_chunks(self, resp, deadline, limit):
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

    def _api(self, url, deadline, key, body=None, content_type="application/json", method=None):
        """Keyed call to the vendor API host only. Returns parsed JSON."""
        if not url.startswith(f"https://{self.API_HOST}/"):
            raise ValueError(f"refusing to send the key to a URL outside https://{self.API_HOST}/")
        headers = {"Authorization": f"{self.AUTH_SCHEME} {key}"}
        if body is not None:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(url, data=body, method=method or ("POST" if body is not None else "GET"),
                                     headers=headers)
        with self.api_opener(req, timeout=max(1, deadline - self.clock())) as resp:
            return json.loads(self._read(resp, deadline, 1 << 20))

    def _post_json(self, url, payload, deadline, key):
        return self._api(url, deadline, key, json.dumps(payload).encode())

    def _download(self, url, deadline, limit):
        """Fetch a result file without the key. https only."""
        if not str(url).startswith("https://"):
            raise ValueError("result url is not https")
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError("no time left in the budget for the download")
        with self.opener(url, timeout=remaining) as dl:
            return self._read(dl, deadline, limit)

    def _wait(self, deadline, what):
        if deadline - self.clock() <= 0:
            raise TimeoutError(f"{what} not done within the time budget")
        self.sleep(min(self.poll_seconds, max(0, deadline - self.clock())))

    def check_image(self, image_path):
        """Only a real PNG/JPEG/WebP inside the repo's work dirs may leave this machine (no UC2/UT2004, no home files)."""
        real = Path(image_path).resolve()
        if UC2_RE.search(str(real)):
            raise ValueError("image path touches a UC2/UT2004 path; refusing to upload")
        if not any(real == r or r in real.parents for r in self.allowed_roots):
            raise ValueError("image is outside the repo work dirs; refusing to upload")
        data = real.read_bytes()
        if len(data) > MAX_IMAGE:
            raise ValueError("image too large to upload")
        head = data[:12]
        if head.startswith(PNG_MAGIC):
            return real, "image/png", data
        if head.startswith(b"\xff\xd8\xff"):
            return real, "image/jpeg", data
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return real, "image/webp", data
        raise ValueError("image is not a PNG, JPEG or WebP; refusing to upload")

    def _fail(self, exc, key, task_id=None):
        err = ProviderError(f"{type(exc).__name__}: {exc}".replace(key, "***") if key else f"{type(exc).__name__}: {exc}")
        err.task_id = task_id
        return err

    def _finish_glb(self, raw, out_path, task_id, command):
        if not raw.startswith(GLB_MAGIC):
            raise ValueError("download is not a GLB (missing glTF header)")
        Path(out_path).write_bytes(raw)
        return {"model": self.MODEL, "task_id": task_id, "command": command, "licence_gate": self.licence_gate()}

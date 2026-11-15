"""fal (fal.ai) cloud adapters for scripts/gen_asset.py: FLUX.1 [schnell] concept images and Rodin-on-fal 3D. stdlib only.

Queue flow (docs read 2026-11-10, https://fal.ai/docs/model-apis/model-endpoints/queue):
  POST https://queue.fal.run/<model_id>   header "Authorization: Key <FAL_KEY>", JSON inputs
       -> {"request_id", "status_url", "response_url", ...}
  GET  status_url -> {"status": IN_QUEUE | IN_PROGRESS | COMPLETED (+ "error" when it failed)}
  GET  response_url -> model output (hosted file URLs on fal.media, fetched without the key)
The key goes only to queue.fal.run; status/response URLs from the reply are refused if they point elsewhere.

Models:
- `fal-ai/flux/schnell` (https://fal.ai/models/fal-ai/flux/schnell): $0.003 per megapixel, FLUX.1 [schnell] is
  Apache-2.0 ("suitable for personal and commercial use"). Output "images": [{"url", "content_type"}].
- `fal-ai/hyper3d/rodin/v2.5` (https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5): $0.40 per generation, paid from fal
  credit. Input "image_urls" (we send a base64 data URI, which fal accepts on many models), output "model_mesh": {"url"}.
  It is Hyper3D's model, so it needs HYPER3D_TERMS_REVIEWED as well as FAL_TERMS_REVIEWED.
- `fal-ai/elevenlabs/music` (https://fal.ai/models/fal-ai/elevenlabs/music, llms.txt read 2026-11-12): $0.60 per
  output audio minute, "rounded up to the closest minute"; fal model page tags "Commercial use". Input is a
  `composition_plan` (named sections, per-section styles and duration_ms 3000-120000) or a plain `prompt`; instrumental
  via negative styles (`force_instrumental` works only with `prompt`); `output_format` (pcm_44100 needs the Pro
  tier, mp3_44100_192 Creator). Output "audio": {"url", "content_type", "file_size"}.
- `fal-ai/stable-audio-25/text-to-audio` (llms.txt read 2026-11-12): $0.20 per clip, no negative prompt, wav.
Music prices are re-read from the pricing API (GET https://api.fal.ai/v1/models/pricing, header "Authorization: Key
<FAL_KEY>"): the key goes to that one extra host only, for that one read-only GET.
Key: FAL_KEY (fal's own name). Gate: FAL_TERMS_REVIEWED.
"""
import base64
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import _as_png
from .cloud import MAX_GLB, MAX_IMAGE, THREED_TIMEOUT, CloudProvider

API_HOST = "queue.fal.run"
API_BASE = f"https://{API_HOST}"
KEY_ENV = "FAL_KEY"
TERMS_ENV = "FAL_TERMS_REVIEWED"
IMAGE_MODEL = "fal-ai/flux/schnell"
THREED_MODEL = "fal-ai/hyper3d/rodin/v2.5"
THREED_TIER = "Gen-2.5-Medium"
MUSIC_MODEL = "fal-ai/elevenlabs/music"
MUSIC_FALLBACK_MODEL = "fal-ai/stable-audio-25/text-to-audio"
PRICING_URL = "https://api.fal.ai/v1/models/pricing"
USAGE_URL = "https://api.fal.ai/v1/models/usage"
MAX_AUDIO = 200 << 20
MUSIC_TIMEOUT = 600
STT_MODEL = "fal-ai/wizper"  # Whisper large-v3 turbo on fal: the machine "vocal gate" (does the take contain sung words?)
MAX_STT_BYTES = 8 << 20  # a 2-minute mono 64 kbps mp3 is about 1 MB; nothing bigger needs to leave the machine
REQUEST_ID_RE = re.compile(r"[0-9A-Za-z_-]{1,64}")  # no '/', '.', '?' or spaces: a request id goes into a URL path
# Audio that may never be uploaded (Rule 8: nothing from UC2/UT2004). The name test below (uc2 / ut2004 anywhere in the
# path, which also covers ~/Projects/UC2* and ~/Projects/Unreal/extracted/UC2004) cannot see the Steam install, whose
# folder is called "Unreal Tournament 2004", so the roots are listed too.
UC2_NAME_RE = re.compile(r"uc2|ut2004", re.IGNORECASE)
PROTECTED_AUDIO_ROOTS = (
    Path.home() / "Projects/Unreal/extracted/UC2004",
    Path.home() / ".local/share/Steam/steamapps/common/Unreal Tournament 2004",
    Path.home() / ".steam/steam/steamapps/common/Unreal Tournament 2004",
)


def stt_inputs(audio_path, trusted_copy=False):
    """The fal speech-to-text inputs for one audio file (a data URI), or ValueError if it must not be uploaded: not a
    plain file, over MAX_STT_BYTES, not WAV/MP3, and (unless `trusted_copy`) the audio_path_problem checks. Pass
    trusted_copy=True ONLY for a file the caller itself made from a source that already passed audio_path_problem (the
    vocal-check temp transcode): its own random temp name must not be judged by the UC2/UT2004 name test."""
    if not trusted_copy:
        problem = audio_path_problem(audio_path)
        if problem:
            raise ValueError(f"{problem}; refusing to upload")
    real = Path(audio_path).resolve()
    if not real.is_file():
        raise ValueError("audio is not a plain file; refusing to upload")
    data = real.read_bytes()
    if len(data) > MAX_STT_BYTES:
        raise ValueError("audio too large to upload for transcription")
    head = data[:4]
    mime = ("audio/wav" if head == b"RIFF" else "audio/mpeg" if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
            else None)
    if mime is None:
        raise ValueError("audio is not a WAV or MP3; refusing to upload")
    uri = f"data:{mime};base64," + base64.b64encode(data).decode()
    return {"audio_url": uri, "task": "transcribe", "language": "en", "chunk_level": "segment"}


def valid_request_id(request_id):
    return bool(REQUEST_ID_RE.fullmatch(str(request_id)))


def audio_path_problem(path):
    """Why the audio at `path` must not be uploaded, or None if it may. Checked on the path AS GIVEN (a symlink is
    refused, never followed) and on its real path (plain file, not under a UC2/UT2004 or protected tree)."""
    given = Path(path)
    if given.is_symlink():
        return "audio path is a symlink"
    real = given.resolve()
    if not real.is_file():
        return "audio is not a plain file"
    if UC2_NAME_RE.search(str(given)) or UC2_NAME_RE.search(str(real)):
        return "audio path touches UC2/UT2004"
    for root in PROTECTED_AUDIO_ROOTS:
        if real == root.resolve() or root.resolve() in real.parents:
            return f"audio is inside the protected tree {root}"
    return None
# Cost basis per model, read from the models' llms.txt pages on 2026-11-12. kind "minute" rounds the audio up to the
# started minute; "clip" and "call" are one flat charge per request. These are the FLOOR for every estimate: a live price
# is used only if it is higher and in the right unit (see unit_price_for).
MUSIC_PRICES = {
    MUSIC_MODEL: {"kind": "minute", "usd": 0.60,
                  "terms": "fal model page tag 'Commercial use' (read 2026-11-12); ElevenLabs partner model on fal"},
    MUSIC_FALLBACK_MODEL: {"kind": "clip", "usd": 0.20,
                           "terms": "Stability AI Stable Audio 2.5 on fal; fal page states no licence text: commercial "
                                    "terms NOT verified, check before shipping"},
    STT_MODEL: {"kind": "call", "usd": 0.05,
                "terms": "analysis only (vocal gate on our own generated music); output not shipped. fal lists '$0 per "
                         "compute seconds' (really cents), so 0.05 per call is a conservative upper-bound estimate"},
}
_UNITS = {"minute": ("minute",), "clip": ("audio", "clip", "request", "generation"),
          "call": ("audio", "clip", "request", "call", "generation")}


def music_cost_estimate(model_id, audio_seconds, usd=None):
    """Dollar estimate for one call. ElevenLabs bills per output minute rounded up to the started minute; the other
    models per request. `usd` overrides the table price (see unit_price_for)."""
    price = MUSIC_PRICES[model_id]
    usd = price["usd"] if usd is None else usd
    if not math.isfinite(usd) or usd < 0 or not math.isfinite(audio_seconds):
        raise ValueError("price or audio length is not a finite number")
    if price["kind"] == "minute":
        return round(usd * max(1, math.ceil(audio_seconds / 60.0)), 4)
    return round(usd, 4)


def unit_price_for(model_id, live_price, live_unit):
    """(usd per unit to use, basis text). The live price from fal's pricing API replaces the table only when it is
    a positive number in the model's own unit AND not below the table; otherwise the table price stays (so a 0 or a
    wrong-unit live price can never make a paid call look free)."""
    table = MUSIC_PRICES[model_id]
    label = f"{table['usd']} USD per {table['kind']}"
    unit = (live_unit or "").lower()
    if (live_price is None or isinstance(live_price, bool) or not isinstance(live_price, (int, float))
            or not math.isfinite(live_price) or live_price <= 0):  # NaN / inf / 0 / negative / text: never trusted
        return table["usd"], f"table {label} (live price {live_price!r} ignored)"
    if not any(u in unit for u in _UNITS[table["kind"]]):
        return table["usd"], f"table {label} (live unit {live_unit!r} ignored)"
    if live_price < table["usd"]:
        return table["usd"], f"table {label} (live {live_price} is lower; table kept as the floor)"
    return float(live_price), f"live pricing API {live_price} USD per {live_unit}"


class FalProvider(CloudProvider):
    """Concept images (provider name "fal" in --provider)."""
    name = "fal"
    API_HOST = API_HOST
    KEY_ENV = KEY_ENV
    TERMS_ENV = TERMS_ENV
    MODEL = IMAGE_MODEL
    AUTH_SCHEME = "Key"
    # fal image_size: a preset name or {"width": W, "height": H}. gen_asset --image-size sets the dict.
    image_size = "square_hd"

    def _queue(self, model_id, inputs, deadline, key, info=None, on_queued=None):
        """Submit, poll, fetch. Returns (request_id, output dict). `info`, if given, gets request_id the moment
        the submit is accepted (so a later failure still shows that a billable request exists), and
        `on_queued(request_id)` runs right then, before any polling (callers ledger the spend there)."""
        sub = self._post_json(f"{API_BASE}/{model_id}", inputs, deadline, key)
        request_id = sub.get("request_id")
        if info is not None:
            info["request_id"] = request_id
        if request_id and on_queued:
            try:
                on_queued(request_id)
            except Exception:  # noqa: BLE001 - the caller's reserved row already counts this spend; keep going
                pass
        status_url, response_url = sub.get("status_url"), sub.get("response_url")
        if not (request_id and status_url and response_url):
            raise RuntimeError("submit reply is missing request_id / status_url / response_url")
        return request_id, self._poll_result(status_url, response_url, request_id, deadline, key)

    def _poll_result(self, status_url, response_url, request_id, deadline, key):
        """Poll a queued request to COMPLETED, then return its output dict."""
        while True:
            st = self._api(status_url, deadline, key)  # _api refuses any host but queue.fal.run
            status = st.get("status")
            if status == "COMPLETED":
                if st.get("error"):
                    raise RuntimeError(f"request {request_id} failed: {st.get('error_type') or ''} {st['error']}".strip())
                break
            if status not in ("IN_QUEUE", "IN_PROGRESS"):
                raise RuntimeError(f"request {request_id} unexpected status {status!r}")
            self._wait(deadline, f"request {request_id}")
        return self._api(response_url, deadline, key)

    def generate(self, prompt, out_path, timeout):
        """Concept PNG from a prompt. Same contract as the other concept providers."""
        key = self._key()
        Path(out_path).unlink(missing_ok=True)
        deadline = self.clock() + timeout
        try:
            _, out = self._queue(IMAGE_MODEL, {"prompt": prompt, "image_size": self.image_size, "num_images": 1,
                                               "output_format": "png", "enable_safety_checker": True}, deadline, key)
            images = out.get("images") or []
            if not images or not images[0].get("url"):
                raise RuntimeError("result has no image url")
            url = images[0]["url"]
            raw = base64.b64decode(url.split(",", 1)[1]) if url.startswith("data:") else self._download(url, deadline, MAX_IMAGE)
            png = _as_png(raw)
            Path(out_path).write_bytes(png)
        except Exception as exc:
            raise self._fail(exc, key)
        return {"model": IMAGE_MODEL, "command": ["POST", f"{API_BASE}/{IMAGE_MODEL}"], "licence_gate": self.licence_gate()}


class Fal3DProvider(FalProvider):
    """Rodin Gen-2.5 hosted on fal, billed to fal credit (provider name "fal" in --3d-provider)."""
    TERMS_ENV = (TERMS_ENV, "HYPER3D_TERMS_REVIEWED")
    MODEL = f"{THREED_MODEL} {THREED_TIER}"

    def generate_3d(self, image_path, out_path, timeout=THREED_TIMEOUT):
        key = self._key()
        Path(out_path).unlink(missing_ok=True)
        deadline = self.clock() + timeout
        task_id = None
        try:
            _, mime, data = self.check_image(image_path)
            uri = f"data:{mime};base64," + base64.b64encode(data).decode()
            task_id, out = self._queue(THREED_MODEL, {"image_urls": [uri], "tier": THREED_TIER,
                                                       "geometry_file_format": "glb", "material": "PBR"}, deadline, key)
            url = (out.get("model_mesh") or {}).get("url")
            if not url:
                raise RuntimeError(f"request {task_id} has no model_mesh url")
            raw = self._download(url, deadline, MAX_GLB)
            return self._finish_glb(raw, out_path, task_id, ["POST", f"{API_BASE}/{THREED_MODEL}"])
        except Exception as exc:
            raise self._fail(exc, key, task_id)


class FalMusicProvider(FalProvider):
    """Music on fal: ElevenLabs Music (composition plan) and Stable Audio 2.5 (provider name "fal-music")."""
    name = "fal-music"
    MODEL = MUSIC_MODEL

    def _api_error_text(self, exc, key):
        """Short, key-free text for an HTTPError, with fal's JSON detail (it explains tier and schema errors)."""
        body = ""
        try:
            body = exc.read(2000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 - best effort
            pass
        return f"HTTP {exc.code} {body}".replace(key, "***").strip()

    def _platform_get(self, base_url, params, timeout=30):
        """One read-only keyed GET to fal's platform API (pricing / usage). Returns parsed JSON."""
        key = self._key()
        deadline = self.clock() + timeout
        url = base_url + "?" + urllib.parse.urlencode(params, safe=",/")
        req = urllib.request.Request(url, headers={"Authorization": f"Key {key}"})
        try:
            with self.api_opener(req, timeout=timeout) as resp:
                return json.loads(self._read(resp, deadline, 1 << 20))
        except urllib.error.HTTPError as exc:
            raise self._fail(RuntimeError(self._api_error_text(exc, key)), key)
        except Exception as exc:
            raise self._fail(exc, key)

    def price(self, model_ids, timeout=30):
        """Live unit prices from fal's pricing API: {endpoint_id: (unit_price, unit)}. Read-only, spends nothing."""
        data = self._platform_get(PRICING_URL, {"endpoint_id": ",".join(model_ids)}, timeout)
        rows = data.get("prices") if isinstance(data, dict) else None
        return {p["endpoint_id"]: (p.get("unit_price"), p.get("unit"))  # a changed schema gives {} -> the table price stays
                for p in (rows if isinstance(rows, list) else []) if isinstance(p, dict) and p.get("endpoint_id")}

    def usage(self, model_ids, start, timeout=30):
        """What fal billed since `start` (YYYY-MM-DD or ISO time), summed per endpoint: {endpoint_id: (quantity,
        cost_total_usd)}. Needs a key with billing read scope; a key without it raises ProviderError (HTTP 403)."""
        data = self._platform_get(USAGE_URL, {"endpoint_id": ",".join(model_ids), "start": start, "expand": "summary"},
                                  timeout)
        return {r["endpoint_id"]: (r.get("quantity"), r.get("cost_total", r.get("cost")))
                for r in data.get("summary", [])}

    def _paid_call(self, model_id, timeout, run):
        """Shared wrapper for a billable request. `run(key, deadline, info)` submits/polls/finishes and fills `info`.
        On failure the raised ProviderError carries `.info`: `request_id` is set once fal accepted the submit (it is
        then billed, whatever happens next); `definitive_reject` is True only when fal answered the submit itself with
        an HTTP 4xx (nothing was queued, nothing is billed). Any other failure before a request_id is ambiguous."""
        if model_id not in MUSIC_PRICES:
            raise ValueError(f"unknown model {model_id!r}")
        key = self._key()
        deadline = self.clock() + timeout
        info = {"model": model_id, "request_id": None, "definitive_reject": False, "http_status": None,
                "licence_gate": self.licence_gate(), "command": ["POST", f"{API_BASE}/{model_id}"]}
        try:
            try:
                run(key, deadline, info)
            except urllib.error.HTTPError as exc:
                info["http_status"] = exc.code
                info["definitive_reject"] = info["request_id"] is None and 400 <= exc.code < 500
                raise RuntimeError(self._api_error_text(exc, key))
            return info
        except Exception as exc:
            err = self._fail(exc, key, info.get("request_id"))
            err.info = info
            raise err

    def _save_audio(self, out, request_id, info, deadline, out_path):
        audio = out.get("audio") or {}
        url = audio.get("url")
        if not url:
            raise RuntimeError(f"request {request_id} has no audio url")
        raw = self._download(url, deadline, MAX_AUDIO)
        Path(out_path).write_bytes(raw)
        info.update(content_type=audio.get("content_type"), file_name=audio.get("file_name"), seed=out.get("seed"),
                    bytes=len(raw))

    def generate_music(self, model_id, inputs, out_path, timeout=MUSIC_TIMEOUT, on_queued=None):
        """Queue one music request and download the audio to out_path. Returns an info dict with `request_id`.
        `on_queued(request_id)` runs the moment fal accepts the submit, before polling: the caller writes the spend
        there. See _paid_call for what a failure's `.info` means."""
        Path(out_path).unlink(missing_ok=True)

        def run(key, deadline, info):
            request_id, out = self._queue(model_id, inputs, deadline, key, info, on_queued)
            self._save_audio(out, request_id, info, deadline, out_path)

        return self._paid_call(model_id, timeout, run)

    def fetch_music(self, model_id, request_id, out_path, timeout=MUSIC_TIMEOUT):
        """Collect the audio of a request that was already queued (and billed) but whose download was lost, e.g. a
        poll timeout. Submits nothing, so it costs nothing extra."""
        if not valid_request_id(request_id):
            raise ValueError("request id has an unexpected shape")
        Path(out_path).unlink(missing_ok=True)
        app = "/".join(model_id.split("/")[:2])

        def run(key, deadline, info):
            info["request_id"] = request_id
            out = self._poll_result(f"{API_BASE}/{app}/requests/{request_id}/status",
                                    f"{API_BASE}/{app}/requests/{request_id}", request_id, deadline, key)
            self._save_audio(out, request_id, info, deadline, out_path)

        return self._paid_call(model_id, timeout, run)

    def transcribe(self, audio_path, timeout=300, on_queued=None, model_id=STT_MODEL, inputs=None):
        """Speech-to-text of a (small) audio file, the machine vocal gate. The file goes out as a data URI. Returns an
        info dict with `result` (fal's output: text + chunks). Same billing/`.info` rules as generate_music. All local checks
        raise ValueError BEFORE anything is sent (they are `stt_inputs`); a caller that books the charge first runs
        `stt_inputs` itself before booking and passes the result as `inputs`."""
        if inputs is None:
            inputs = stt_inputs(audio_path)

        def run(key, deadline, info):
            request_id, out = self._queue(model_id, inputs, deadline, key, info, on_queued)
            info["result"] = out

        return self._paid_call(model_id, timeout, run)

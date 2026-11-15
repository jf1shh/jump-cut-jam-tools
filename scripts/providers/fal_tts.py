"""fal text-to-speech for `scripts/gen_asset.py --tts` (short voice lines). stdlib only.

Same gate and safety rules as the fal image/3D adapters (providers/fal.py, providers/cloud.py): FAL_KEY and
FAL_TERMS_REVIEWED must both be set, the key goes only to queue.fal.run, status/response URLs pointing elsewhere are
refused, the audio file is fetched without the key, everything runs under one deadline, the key is redacted from errors.

Models (API pages read 2026-11-12):
- `fal-ai/gemini-tts` (https://fal.ai/models/fal-ai/gemini-tts/api): inputs `prompt`, `style_instructions`
  (delivery direction in plain words), `voice` (30 presets, e.g. Algenib "gravelly", Fenrir "excitable"),
  `model` (`gemini-2.5-flash-tts` | `gemini-2.5-pro-tts`), `temperature`, `output_format` (`wav` = 24 kHz 16-bit
  mono PCM). Output `audio.url`. Tagged "Commercial use" on fal.
- `fal-ai/minimax/speech-02-hd` (https://fal.ai/models/fal-ai/minimax/speech-02-hd/api): inputs `text`,
  `voice_setting` {`voice_id`, `speed`, `vol`, `pitch`, `emotion`}, `audio_setting` {`format`, `sample_rate`},
  `output_format` (`url`). Output `audio.url`, `duration_ms`. Tagged "Commercial use" on fal. Fallback only.
Output is AI-generated content (Rule 15(c)): not a sourced asset, disclose it in the AI field.
"""
import base64
from pathlib import Path

from .cloud import CloudProvider  # noqa: F401  (re-exported for tests)
from .fal import FalProvider

GEMINI_MODEL = "fal-ai/gemini-tts"
MINIMAX_MODEL = "fal-ai/minimax/speech-02-hd"
ENGINES = {"gemini": GEMINI_MODEL, "minimax": MINIMAX_MODEL}
AUTO_ORDER = ("gemini", "minimax")
GEMINI_QUALITY = {"flash": "gemini-2.5-flash-tts", "pro": "gemini-2.5-pro-tts"}
DEFAULT_VOICE = {"gemini": "Algenib", "minimax": "Deep_Voice_Man"}
MINIMAX_EMOTIONS = ("happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral")
MAX_TEXT = 400  # voice lines, not audiobooks: keeps every call cheap
MAX_STYLE = 600
MAX_AUDIO = 20 << 20
TTS_TIMEOUT = 180


def audio_kind(raw):
    """File extension for the bytes, or None if they are not audio we accept."""
    if raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
        return "wav"
    if raw[:4] == b"fLaC":
        return "flac"
    if raw[:3] == b"ID3" or (len(raw) > 1 and raw[0] == 0xFF and (raw[1] & 0xE0) == 0xE0):
        return "mp3"
    if raw[:4] == b"OggS":
        return "ogg"
    return None


class FalTTSProvider(FalProvider):
    """Voice lines through fal. `synthesize()` writes <out_stem>.<ext> and returns its provenance fields."""
    name = "fal-tts"
    MODEL = GEMINI_MODEL

    def check(self):
        status, detail = super().check()
        return status, detail.replace(f"(model {FalProvider.MODEL})", f"(model {GEMINI_MODEL})")

    def _inputs(self, engine, text, voice, style, quality, temperature, emotion):
        if engine == "gemini":
            inputs = {"prompt": text, "voice": voice or DEFAULT_VOICE["gemini"], "model": GEMINI_QUALITY[quality],
                      "output_format": "wav", "enable_safety_checker": True}
            if style:
                inputs["style_instructions"] = style
            if temperature is not None:
                inputs["temperature"] = float(temperature)
            return inputs
        voice_setting = {"voice_id": voice or DEFAULT_VOICE["minimax"], "speed": 1.0, "vol": 1.0, "pitch": 0}
        if emotion:
            voice_setting["emotion"] = emotion
        return {"text": text, "voice_setting": voice_setting, "output_format": "url",
                "audio_setting": {"format": "flac", "sample_rate": 44100, "channel": 1},
                "enable_safety_checker": True}

    def synthesize(self, text, out_stem, engine="gemini", voice=None, style=None, quality="pro",
                   temperature=None, emotion=None, timeout=TTS_TIMEOUT):
        if engine not in ENGINES:
            raise ValueError(f"unknown tts engine {engine!r}")
        text = (text or "").strip()
        if not text or len(text) > MAX_TEXT:
            raise ValueError(f"tts text must be 1-{MAX_TEXT} characters")
        if style and len(style) > MAX_STYLE:
            raise ValueError(f"tts style must be at most {MAX_STYLE} characters")
        if quality not in GEMINI_QUALITY:
            raise ValueError(f"tts quality must be one of {sorted(GEMINI_QUALITY)}")
        if emotion and emotion not in MINIMAX_EMOTIONS:
            raise ValueError(f"tts emotion must be one of {MINIMAX_EMOTIONS}")
        key = self._key()
        model_id = ENGINES[engine]
        inputs = self._inputs(engine, text, voice, style, quality, temperature, emotion)
        deadline = self.clock() + timeout
        out_stem = Path(out_stem)
        try:
            request_id, out = self._queue(model_id, inputs, deadline, key)
            audio = out.get("audio") or {}
            url = audio.get("url")
            if not url:
                raise RuntimeError("result has no audio url")
            raw = base64.b64decode(url.split(",", 1)[1]) if url.startswith("data:") else self._download(url, deadline, MAX_AUDIO)
            ext = audio_kind(raw)
            if ext is None:
                raise ValueError("download is not WAV, FLAC, MP3 or Ogg audio")
            for old in out_stem.parent.glob(f"{out_stem.name}.*"):
                if old.suffix.lstrip(".") in ("wav", "flac", "mp3", "ogg"):
                    old.unlink()
                    Path(f"{old}.provenance.json").unlink(missing_ok=True)  # a stale sidecar would describe the wrong take
            path = out_stem.with_name(f"{out_stem.name}.{ext}")
            path.write_bytes(raw)
        except Exception as exc:
            raise self._fail(exc, key)
        settings = {k: v for k, v in inputs.items() if k not in ("prompt", "text", "enable_safety_checker")}
        return {"path": str(path), "engine": engine, "model": model_id, "request_id": request_id,
                "settings": settings, "command": ["POST", f"https://queue.fal.run/{model_id}"],
                "licence_gate": self.licence_gate()}

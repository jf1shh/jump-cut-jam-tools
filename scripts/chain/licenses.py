"""Licence gate. Refuses any engine/model that is not "ok" / "ok-with-credit".

Source of truth: config/asset-licenses.json (written by the licence-audit ticket). Until it exists we
fall back to a tiny built-in allowlist and warn. Hunyuan, Qwen-Image and UltraSharp are always refused.
"""
import json
import re
from pathlib import Path

OK_VERDICTS = ("ok", "ok-with-credit")
ALWAYS_BANNED = re.compile(r"hunyuan|qwen-image|ultrasharp", re.IGNORECASE)

# Used only when config/asset-licenses.json is missing: TripoSplat + GPT + Blender (+ the Krea
# checkpoint that feeds them, and owner-supplied reference images).
FALLBACK = {
    "triposplat": {"verdict": "ok", "credit": ""},
    "gpt": {"verdict": "ok", "credit": ""},
    "krea-2-turbo": {"verdict": "ok", "credit": ""},
    "blender": {"verdict": "ok", "credit": ""},
    "reference-image": {"verdict": "ok", "credit": "owner-supplied reference image"},
    "passthrough": {"verdict": "ok", "credit": ""},
}


INTERNAL = frozenset({("texture", "passthrough"), ("image", "reference-image")})


class LicenceError(Exception):
    pass


def _entries(data):
    """Flatten the file into {name_lower: entry}. Accepts flat, {"engines"|"models"|"tools": {...}}, or lists."""
    out = {}

    def add(name, entry):
        if isinstance(entry, dict) and name:
            out[str(name).lower()] = entry

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("engines", "models", "tools", "entries") and isinstance(v, (dict, list)):
                    walk(v)
                elif isinstance(v, dict):
                    add(k, v)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    add(item.get("name") or item.get("id"), item)

    walk(data)
    return out


class LicenceGate:
    def __init__(self, path, warn=print):
        self.path = Path(path)
        self.warn = warn
        if self.path.is_file():
            self.table = _entries(json.loads(self.path.read_text()))
            self.source = str(self.path)
            self.fallback = False
        else:
            self.table = {k: dict(v) for k, v in FALLBACK.items()}
            self.source = "built-in fallback"
            self.fallback = True
            warn(f"licence: {self.path} not found; allowing only {', '.join(sorted(FALLBACK))}")

    def check(self, stage, name, aliases=()):
        """Return {"engine", "verdict", "credit", "source"}; raise LicenceError if not allowed."""
        keys = [k.lower() for k in (f"{stage}:{name}", name, *aliases)]
        for k in keys:
            if ALWAYS_BANNED.search(k):
                raise LicenceError(f"{stage}:{name} refused: banned model ({k})")
        if (stage, name) in INTERNAL and not aliases:  # chain-internal no-ops run no third-party model
            credit = "owner-supplied reference image" if name == "reference-image" else ""
            return {"engine": f"{stage}:{name}", "verdict": "ok", "credit": credit, "source": "internal"}
        # Every listed key counts (name AND the model aliases it runs): any refusal refuses the engine.
        found = [(k, self.table[k]) for k in keys if k in self.table]
        for k, entry in found:
            verdict = str(entry.get("verdict", entry.get("status", ""))).lower()
            if verdict not in OK_VERDICTS:
                raise LicenceError(f"{stage}:{name} refused: licence verdict {verdict or 'missing'!r} for {k}")
        if not found:
            raise LicenceError(f"{stage}:{name} refused: not listed in {self.source} (tried {', '.join(keys)})")
        verdicts = [str(e.get("verdict", e.get("status", ""))).lower() for _, e in found]
        credits = sorted({str(e.get("credit") or e.get("credit_text") or "") for _, e in found} - {""})
        return {"engine": f"{stage}:{name}", "verdict": "ok-with-credit" if "ok-with-credit" in verdicts else "ok",
                "credit": "; ".join(credits), "source": self.source}

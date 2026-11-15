"""gen_asset.py --tts and providers/fal_tts.py: mocked HTTP only. No live calls, no real keys."""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_cloud_providers import ENV, KEYS, Base, Clock, Router, gen_asset, make  # noqa: E402
from providers import fal_tts as TTS  # noqa: E402

WAV = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVEfmt " + b"\x00" * 24
FLAC = b"fLaC" + b"\x00" * 30


def tts_routes(model, audio_url, audio_bytes, status=("IN_QUEUE", "COMPLETED"), status_host="https://queue.fal.run"):
    app = "/".join(model.split("/")[:2])
    return [
        (f"https://queue.fal.run/{model}", "POST",
         {"request_id": "v-1", "status_url": f"{status_host}/{app}/requests/v-1/status",
          "response_url": f"https://queue.fal.run/{app}/requests/v-1"}),
        (f"https://queue.fal.run/{app}/requests/v-1/status", "GET", [{"status": s} for s in status]),
        (f"https://queue.fal.run/{app}/requests/v-1", "GET", {"audio": {"url": audio_url}}),
        ("https://v3b.fal.media/", "GET", audio_bytes),
    ]


class Provider(Base):
    def test_gemini_line_writes_wav_and_sends_direction(self):
        router = Router(tts_routes(TTS.GEMINI_MODEL, "https://v3b.fal.media/files/x/line.wav", WAV))
        info = make(TTS.FalTTSProvider, router).synthesize(
            "CUT!", self.d / "VO_Cut", style="energetic film director", voice="Algenib", temperature=1.2)
        self.assertEqual(Path(info["path"]), self.d / "VO_Cut.wav")
        self.assertEqual((self.d / "VO_Cut.wav").read_bytes(), WAV)
        body = json.loads(router.calls[0][3])
        self.assertEqual(body["prompt"], "CUT!")
        self.assertEqual(body["style_instructions"], "energetic film director")
        self.assertEqual((body["voice"], body["model"], body["output_format"]), ("Algenib", "gemini-2.5-pro-tts", "wav"))
        self.assertEqual(body["temperature"], 1.2)
        self.assertNotIn("prompt", info["settings"])
        self.assertEqual(info["licence_gate"], "FAL_TERMS_REVIEWED=2026-11-10")
        self.assert_key_only_to(router, "queue.fal.run", KEYS["FAL_KEY"], "Key")

    def test_minimax_fallback_shape_and_flac(self):
        router = Router(tts_routes(TTS.MINIMAX_MODEL, "https://v3b.fal.media/files/y/line.flac", FLAC))
        info = make(TTS.FalTTSProvider, router).synthesize("Print it!", self.d / "VO", engine="minimax", emotion="happy")
        self.assertTrue(info["path"].endswith("VO.flac"))
        body = json.loads(router.calls[0][3])
        self.assertEqual(body["text"], "Print it!")
        self.assertEqual(body["voice_setting"]["emotion"], "happy")
        self.assertEqual(body["output_format"], "url")
        self.assertEqual(router.calls[1][1], "https://queue.fal.run/fal-ai/minimax/requests/v-1/status")

    def test_non_audio_download_fails_and_hides_key(self):
        router = Router(tts_routes(TTS.GEMINI_MODEL, "https://v3b.fal.media/files/x/a.wav", b"<html>" + KEYS["FAL_KEY"].encode()))
        with self.assertRaises(Exception) as ctx:
            make(TTS.FalTTSProvider, router).synthesize("Again!", self.d / "VO")
        self.assertNotIn(KEYS["FAL_KEY"], str(ctx.exception))
        self.assertEqual(list(self.d.glob("VO.*")), [])

    def test_status_url_off_host_is_refused(self):
        router = Router(tts_routes(TTS.GEMINI_MODEL, "https://v3b.fal.media/a.wav", WAV, status_host="https://evil.example"))
        with self.assertRaises(Exception) as ctx:
            make(TTS.FalTTSProvider, router).synthesize("Again!", self.d / "VO")
        self.assertIn("refusing", str(ctx.exception))
        self.assertFalse(any(u.startswith("https://evil.example") for _, u, _, _ in router.calls))

    def test_bad_text_never_calls_the_network(self):
        router = Router([])
        p = make(TTS.FalTTSProvider, router)
        for text in ("", "   ", "x" * (TTS.MAX_TEXT + 1)):
            with self.assertRaises(ValueError):
                p.synthesize(text, self.d / "VO")
        self.assertEqual(router.calls, [])

    def test_not_configured_without_terms(self):
        p = make(TTS.FalTTSProvider, Router([]), env={"FAL_KEY": "k"})
        self.assertEqual(p.gate()[0], "not configured")
        self.assertIn("(model fal-ai/gemini-tts)", make(TTS.FalTTSProvider, Router([])).check()[1])


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.log = self.tmp / "log.csv"
        gen_asset.ensure_csv_header(self.log)

    def args(self, engine="auto"):
        return SimpleNamespace(name="VO_Cut", tts="CUT!", tts_engine=engine, tts_voice=None, tts_style="director",
                               tts_quality="pro", tts_temperature=None, tts_emotion=None)

    def rows(self):
        with self.log.open() as f:
            return [(r["stage"], r["exit_code"]) for r in csv.DictReader(f)]

    def test_auto_falls_back_to_minimax_and_writes_sidecar(self):
        routes = tts_routes(TTS.MINIMAX_MODEL, "https://v3b.fal.media/files/y/l.flac", FLAC)
        routes.insert(0, (f"https://queue.fal.run/{TTS.GEMINI_MODEL}", "POST", {"oops": 1}))
        p = make(TTS.FalTTSProvider, Router(routes))
        code = gen_asset.run_tts(self.args(), self.tmp, self.log, ENV, provider=p)
        self.assertEqual(code, 0)
        self.assertEqual(self.rows(), [("tts:gemini", "1"), ("tts:minimax", "0")])
        record = json.loads((self.tmp / "VO_Cut.flac.provenance.json").read_text())
        self.assertTrue(record["ai_generated"])
        self.assertEqual((record["text"], record["engine"], record["model"]), ("CUT!", "minimax", TTS.MINIMAX_MODEL))
        self.assertEqual(len(record["output_sha256"]), 64)

    def test_fallback_gets_minimax_voice_not_gemini_voice_and_records_it(self):
        routes = tts_routes(TTS.MINIMAX_MODEL, "https://v3b.fal.media/files/y/l.flac", FLAC)
        routes.insert(0, (f"https://queue.fal.run/{TTS.GEMINI_MODEL}", "POST", {"oops": 1}))
        router = Router(routes)
        a = self.args()
        a.tts_voice = "Fenrir"
        self.assertEqual(gen_asset.run_tts(a, self.tmp, self.log, ENV, provider=make(TTS.FalTTSProvider, router)), 0)
        post = [c for c in router.calls if c[0] == "POST" and c[1].endswith(TTS.MINIMAX_MODEL)][0]
        body = json.loads(post[3])
        self.assertEqual(body["voice_setting"]["voice_id"], TTS.DEFAULT_VOICE["minimax"])
        rec = json.loads((self.tmp / "VO_Cut.flac.provenance.json").read_text())
        self.assertEqual(rec["voice"], TTS.DEFAULT_VOICE["minimax"])
        self.assertIsNone(rec["style"])
        self.assertEqual(rec["requested"]["voice"], "Fenrir")
        self.assertTrue(any("Fenrir" in n for n in rec["notes"]) and any("style" in n for n in rec["notes"]))

    def test_gemini_sidecar_records_voice_and_style(self):
        p = make(TTS.FalTTSProvider, Router(tts_routes(TTS.GEMINI_MODEL, "https://v3b.fal.media/files/x/a.wav", WAV)))
        a = self.args()
        a.tts_voice = "Fenrir"
        self.assertEqual(gen_asset.run_tts(a, self.tmp, self.log, ENV, provider=p), 0)
        rec = json.loads((self.tmp / "VO_Cut.wav.provenance.json").read_text())
        self.assertEqual((rec["engine"], rec["voice"], rec["style"]), ("gemini", "Fenrir", "director"))

    def test_other_engines_stale_wav_and_sidecar_removed(self):
        (self.tmp / "VO_Cut.wav").write_bytes(WAV)
        (self.tmp / "VO_Cut.wav.provenance.json").write_text("{}")
        p = make(TTS.FalTTSProvider, Router(tts_routes(TTS.MINIMAX_MODEL, "https://v3b.fal.media/files/y/l.flac", FLAC)))
        self.assertEqual(gen_asset.run_tts(self.args("minimax"), self.tmp, self.log, ENV, provider=p), 0)
        self.assertEqual(sorted(x.name for x in self.tmp.glob("VO_Cut.*")),
                         ["VO_Cut.flac", "VO_Cut.flac.provenance.json"])

    def test_forced_engine_does_not_fall_back(self):
        routes = [(f"https://queue.fal.run/{TTS.GEMINI_MODEL}", "POST", {"oops": 1})]
        p = make(TTS.FalTTSProvider, Router(routes))
        self.assertEqual(gen_asset.run_tts(self.args("gemini"), self.tmp, self.log, ENV, provider=p), 1)
        self.assertEqual(self.rows(), [("tts:gemini", "1")])

    def test_not_configured_exits_1_and_logs(self):
        p = make(TTS.FalTTSProvider, Router([]), env={})
        self.assertEqual(gen_asset.run_tts(self.args(), self.tmp, self.log, {}, provider=p), 1)
        self.assertEqual(self.rows(), [("tts:fal", "1")])

    def test_cli_accepts_tts_and_rejects_tts_with_prompt(self):
        with mock.patch.object(sys, "argv", ["gen_asset.py", "--name", "VO_Cut", "--tts", "CUT!", "--tts-voice", "Fenrir"]):
            a = gen_asset.parse_args()
        self.assertEqual((a.tts, a.tts_voice, a.tts_engine, a.tts_quality), ("CUT!", "Fenrir", "auto", "pro"))
        with mock.patch.object(sys, "argv", ["gen_asset.py", "--name", "x", "--tts", "a", "--prompt", "b"]), \
                mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            gen_asset.parse_args()


if __name__ == "__main__":
    unittest.main()

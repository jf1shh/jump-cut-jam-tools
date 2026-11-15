"""fal music adapter and CLI: mocked HTTP only. No live calls, no real keys, nothing billed."""
import csv
import io
import json
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import wave
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
import gen_music_fal as G  # noqa: E402
import test_cloud_providers as TC  # noqa: E402  (Router, Clock, make, ENV: the shared HTTP fakes)
from providers import ProviderError  # noqa: E402
from providers import fal as F  # noqa: E402

WAV = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"x" * 40
MODEL = F.MUSIC_MODEL
APP = "fal-ai/elevenlabs"
STATUS = f"https://queue.fal.run/{APP}/requests/q-1/status"
RESULT = f"https://queue.fal.run/{APP}/requests/q-1"
SECRET = "fal_SECRET_1"


def http_error(url, code, body=b'{"detail":"x"}'):
    return urllib.error.HTTPError(url, code, "x", {}, io.BytesIO(body))


def routes(submit=None, status=None, pricing=None, audio=WAV, model=MODEL):
    """Router table for one fal queue job. `submit` / `status` may be a reply, a list (sequence) or a callable(req)."""
    app = "/".join(model.split("/")[:2])
    return [
        (f"https://queue.fal.run/{model}", "POST", submit or {
            "request_id": "q-1", "status_url": f"https://queue.fal.run/{app}/requests/q-1/status",
            "response_url": f"https://queue.fal.run/{app}/requests/q-1"}),
        (f"https://queue.fal.run/{app}/requests/q-1/status", "GET", status or [{"status": "IN_QUEUE"}, {"status": "COMPLETED"}]),
        (f"https://queue.fal.run/{app}/requests/q-1", "GET",
         {"audio": {"url": "https://v3.fal.media/files/m.wav", "content_type": "audio/wav"}, "text": "Thank you."}),
        ("https://v3.fal.media/", "GET", audio),
        ("https://api.fal.ai/v1/models/pricing", "GET", pricing or {"prices": [
            {"endpoint_id": MODEL, "unit_price": 0.6, "unit": "minute", "currency": "USD"}]}),
    ]


class Cost(unittest.TestCase):
    def test_elevenlabs_rounds_up_to_the_started_minute(self):
        e = F.music_cost_estimate
        self.assertEqual([e(MODEL, s) for s in (1, 58, 60, 60.1, 112, 115.2, 120, 120.5)],
                         [0.6, 0.6, 0.6, 1.2, 1.2, 1.2, 1.2, 1.8])

    def test_flat_priced_models(self):
        self.assertEqual(F.music_cost_estimate(F.MUSIC_FALLBACK_MODEL, 190), 0.2)
        self.assertEqual(F.music_cost_estimate(F.STT_MODEL, 190), 0.05)

    def test_live_price_cannot_make_a_call_look_free_or_cheap(self):
        u = F.unit_price_for
        self.assertEqual(u(MODEL, 0, "minute")[0], 0.6)           # zero
        self.assertEqual(u(MODEL, None, None)[0], 0.6)             # missing
        self.assertEqual(u(MODEL, -1, "minute")[0], 0.6)           # negative
        self.assertEqual(u(MODEL, 0.01, "second")[0], 0.6)         # wrong unit
        self.assertEqual(u(MODEL, 0.3, "minute")[0], 0.6)          # below the table floor
        self.assertEqual(u(MODEL, "0.6", "minute")[0], 0.6)        # not a number
        self.assertEqual(u(F.MUSIC_FALLBACK_MODEL, 0.2, "audios")[0], 0.2)
        self.assertEqual(u(F.STT_MODEL, 0, "compute seconds")[0], 0.05)

    def test_higher_live_price_in_the_right_unit_wins(self):
        usd, basis = F.unit_price_for(MODEL, 0.9, "minute")
        self.assertEqual(usd, 0.9)
        self.assertIn("live pricing API", basis)
        self.assertEqual(F.music_cost_estimate(MODEL, 112, usd), 1.8)


class Presets(unittest.TestCase):
    def test_drive_is_the_spec_sections_in_whole_bars(self):
        plan = G.preset_plan("drive")
        self.assertEqual([s["section_name"] for s in plan["sections"]], ["INTRO", "DRIVE-A", "DRIVE-B", "DRIVE-A'", "TAG"])
        for s in plan["sections"]:
            self.assertEqual(s["duration_ms"] % G.BAR_MS, 0, s["section_name"])
        self.assertTrue(all(x in plan["negative_global_styles"] for x in ("vocals", "lyrics", "singing")))
        self.assertIn("112 BPM", plan["positive_global_styles"])

    def test_b_is_bigger_and_a_is_sparser_in_the_plan_text(self):
        secs = {s["section_name"]: s for s in G.preset_plan("drive")["sections"]}
        self.assertIn("brass", " ".join(secs["DRIVE-B"]["positive_local_styles"]))
        self.assertIn("brass", secs["DRIVE-A"]["negative_local_styles"])
        self.assertIn("wah-wah", secs["DRIVE-A"]["negative_local_styles"])

    def test_every_preset_fits_fal_limits_and_the_billed_minutes(self):
        for name, cost in (("drive", 1.2), ("drive-test", 0.6), ("hold-pack", 0.6)):
            plan = G.preset_plan(name)
            for s in plan["sections"]:
                self.assertTrue(3000 <= s["duration_ms"] <= 120000, (name, s["section_name"]))
                self.assertTrue(1 <= len(s["section_name"]) <= 100)
            self.assertEqual(F.music_cost_estimate(MODEL, G.plan_seconds(plan)), cost, name)
            self.assertLessEqual(G.plan_seconds(plan), 60 * (2 if name == "drive" else 1), name)

    def test_key_is_pinned_when_given(self):
        self.assertIn("key of F minor", G.preset_plan("hold-pack", "F minor")["positive_global_styles"])


class VocalVerdict(unittest.TestCase):
    def test_filler_is_ignored_and_lyrics_are_rejected(self):
        v = lambda t: G.vocal_verdict(t)["verdict"]  # noqa: E731
        self.assertEqual(v(""), "clean")
        self.assertEqual(v("Thank you."), "clean")
        self.assertEqual(v("[Music]"), "clean")
        self.assertEqual(v("♪ Music ♪ Thank you for watching."), "clean")
        self.assertEqual(v("Oh yeah"), "borderline")
        self.assertEqual(v("Baby baby oh baby I love you so"), "vocals-suspected")
        self.assertEqual(v("Thank you. Thank you. we are the champions of the night"), "vocals-suspected")


class Provider(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.d = Path(d)

    def prov(self, router, **kw):
        return TC.make(F.FalMusicProvider, router, **kw)

    def test_generate_writes_audio_and_calls_on_queued_before_polling(self):
        order = []
        router = TC.Router(routes(status=lambda req: order.append("poll") or {"status": "COMPLETED"}))
        info = self.prov(router).generate_music(MODEL, {"composition_plan": {}}, self.d / "t.dl", 60,
                                                on_queued=lambda rid: order.append(f"queued:{rid}"))
        self.assertEqual(order[0], "queued:q-1")
        self.assertEqual((self.d / "t.dl").read_bytes(), WAV)
        self.assertEqual((info["request_id"], info["content_type"], info["definitive_reject"]), ("q-1", "audio/wav", False))
        for method, url, headers, _ in router.calls:  # the key goes to the queue host (and pricing host) only
            if url.startswith("https://queue.fal.run/"):
                self.assertEqual(headers.get("authorization"), f"Key {SECRET}")
            else:
                self.assertNotIn("authorization", headers, url)

    def test_http_4xx_on_submit_is_a_definitive_reject_and_the_key_is_redacted(self):
        def reject(req):
            raise http_error(req.full_url, 403, b'{"detail":"tier fal_SECRET_1"}')

        with self.assertRaises(ProviderError) as cm:
            self.prov(TC.Router(routes(submit=reject))).generate_music(MODEL, {}, self.d / "t.dl", 60)
        info = cm.exception.info
        self.assertEqual((info["request_id"], info["definitive_reject"], info["http_status"]), (None, True, 403))
        self.assertIn("HTTP 403", str(cm.exception))
        self.assertNotIn(SECRET, str(cm.exception))

    def test_other_submit_failures_are_ambiguous_not_definitive(self):
        for exc in (lambda req: (_ for _ in ()).throw(urllib.error.URLError("reset")),
                    lambda req: (_ for _ in ()).throw(http_error(req.full_url, 502)),
                    lambda req: {"status_url": "x"}):  # reply without a request id
            with self.assertRaises(ProviderError) as cm:
                self.prov(TC.Router(routes(submit=exc))).generate_music(MODEL, {}, self.d / "t.dl", 60)
            self.assertFalse(cm.exception.info["definitive_reject"])

    def test_failure_after_queue_keeps_the_request_id(self):
        status = {"status": "COMPLETED", "error": "boom", "error_type": "x"}
        with self.assertRaises(ProviderError) as cm:
            self.prov(TC.Router(routes(status=status))).generate_music(MODEL, {}, self.d / "t.dl", 60)
        self.assertEqual(cm.exception.info["request_id"], "q-1")
        self.assertFalse(cm.exception.info["definitive_reject"])

    def test_poll_timeout_keeps_the_request_id(self):
        with self.assertRaises(ProviderError) as cm:
            self.prov(TC.Router(routes(status={"status": "IN_PROGRESS"}))).generate_music(MODEL, {}, self.d / "t.dl", 20)
        self.assertEqual(cm.exception.info["request_id"], "q-1")

    def test_fetch_collects_audio_without_submitting(self):
        router = TC.Router(routes(status={"status": "COMPLETED"}))
        info = self.prov(router).fetch_music(MODEL, "q-1", self.d / "f.dl", 60)
        self.assertEqual((self.d / "f.dl").read_bytes(), WAV)
        self.assertTrue(all(m == "GET" for m, *_ in router.calls))  # nothing was submitted
        self.assertEqual(info["request_id"], "q-1")

    def test_fetch_refuses_a_malformed_request_id(self):
        for bad in ("../x", "a/b", "", "x" * 100, "q 1"):
            with self.assertRaises(ValueError):
                self.prov(TC.Router([])).fetch_music(MODEL, bad, self.d / "f.dl", 5)

    def test_unknown_model_is_refused(self):
        with self.assertRaises(ValueError):
            self.prov(TC.Router([])).generate_music("fal-ai/other", {}, self.d / "t", 5)

    def test_price_sends_the_key_to_the_pricing_host_only(self):
        router = TC.Router(routes())
        self.assertEqual(self.prov(router).price([MODEL]), {MODEL: (0.6, "minute")})
        method, url, headers, _ = router.calls[0]
        self.assertTrue(url.startswith("https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai/elevenlabs/music"))
        self.assertEqual(headers["authorization"], f"Key {SECRET}")

    def test_not_configured_without_terms_date(self):
        env = {k: v for k, v in TC.ENV.items() if k != "FAL_TERMS_REVIEWED"}
        with self.assertRaises(ProviderError):
            self.prov(TC.Router(routes()), env=env).generate_music(MODEL, {}, self.d / "t", 5)

    def test_transcribe_uploads_a_data_uri_and_returns_the_result(self):
        mp3 = self.d / "a.mp3"
        mp3.write_bytes(b"ID3" + b"\x00" * 50)
        router = TC.Router(routes(model=F.STT_MODEL))
        info = self.prov(router).transcribe(mp3, 60)
        self.assertEqual(info["result"]["text"], "Thank you.")
        body = json.loads(router.calls[0][3])
        self.assertTrue(body["audio_url"].startswith("data:audio/mpeg;base64,"))
        self.assertEqual((body["task"], body["language"]), ("transcribe", "en"))

    def test_transcribe_refuses_non_audio_and_uc2_paths(self):
        bad = self.d / "x.mp3"
        bad.write_bytes(b"MZ" + b"\x00" * 50)
        with self.assertRaises(ValueError):
            self.prov(TC.Router([])).transcribe(bad, 5)
        uc2 = self.d / "uc2"
        uc2.mkdir()
        (uc2 / "a.mp3").write_bytes(b"ID3" + b"\x00" * 50)
        with self.assertRaises(ValueError):
            self.prov(TC.Router([])).transcribe(uc2 / "a.mp3", 5)


class Cli(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.d = Path(d)
        self.ledger, self.log = self.d / "ledger.csv", self.d / "pipeline.csv"
        self.log.write_text("timestamp_iso,name,stage,seconds,exit_code,output_path,human_review\n")
        self.repo_copy = self.d / "repo-copy.csv"
        for p in (mock.patch.object(G, "SPEND_LEDGER", self.ledger), mock.patch.object(G, "ASSET_LOG", self.log),
                  mock.patch.object(G, "REPO_LEDGER_COPY", self.repo_copy),
                  mock.patch.object(G, "STOP_APPROVAL_FILE", self.d / "approval.txt"),
                  mock.patch.object(G, "audio_seconds_of", return_value=58.0)):
            p.start()
            self.addCleanup(p.stop)

    def args(self, **kw):
        base = dict(job="t1", out=str(self.d / "t1"), model="eleven", preset="drive-test", plan_file=None, key=None,
                    prompt=None, negative=None, seconds=None, accept_unverified_licence=False,
                    output_format="pcm_44100,mp3_44100_128", campaign="music1", cap=None, stop_at=None, timeout=60,
                    no_price_check=False, dry_run=False, note="unit test")
        base.update(kw)
        return Namespace(**base)

    def run_cmd(self, fn, router, **kw):
        prov = TC.make(F.FalMusicProvider, router)
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(G, "make_provider", return_value=prov), redirect_stderr(err), redirect_stdout(out):
            code = fn(self.args(**kw), TC.ENV)
        return code, err.getvalue(), out.getvalue()

    def run_gen(self, router, **kw):
        return self.run_cmd(G.cmd_gen, router, **kw)

    def rows(self, path=None):
        with open(path or self.ledger, newline="") as f:
            return list(csv.DictReader(f))

    def seed(self, cost, campaign="music1"):
        G.reserve({"campaign": campaign, "job": "seed"}, cost, 99, 99)

    # --- success and bookkeeping
    def test_success_ledgers_the_call_and_writes_a_sidecar(self):
        code, err, out = self.run_gen(TC.Router(routes()))
        self.assertEqual(code, 0, err)
        wav = self.d / "t1.wav"
        self.assertTrue(wav.exists())
        row = self.rows()[0]
        self.assertEqual((row["campaign"], row["job"], row["model"], row["status"], row["request_id"]),
                         ("music1", "t1", MODEL, "ok", "q-1"))
        self.assertEqual(row["cost_usd_est"], "0.6000")
        self.assertIn("live pricing API", row["cost_basis"])
        self.assertIn("Commercial use", row["licence_note"])
        self.assertTrue(row["row_id"])
        side = json.loads((self.d / "t1.wav.provenance.json").read_text())
        self.assertEqual((side["model"], side["inputs"]["output_format"], side["ai_generated"]), (MODEL, "pcm_44100", True))
        self.assertEqual(self.rows(self.log)[0]["stage"], "music:fal")
        blob = self.ledger.read_text() + (self.d / "t1.wav.provenance.json").read_text()
        self.assertNotIn(SECRET, blob + out)

    def test_the_charge_is_reserved_before_the_request_and_updated_before_polling(self):
        seen = {}

        def submit(req):
            seen["at_submit"] = [(r["status"], r["request_id"], r["cost_usd_est"]) for r in self.rows()]
            return {"request_id": "q-1", "status_url": STATUS, "response_url": RESULT}

        def status(req):
            seen.setdefault("at_poll", [(r["status"], r["request_id"]) for r in self.rows()])
            return {"status": "COMPLETED"}

        code, err, _ = self.run_gen(TC.Router(routes(submit=submit, status=status)))
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["at_submit"], [("reserved", "", "0.6000")])   # counted before fal is even called
        self.assertEqual(seen["at_poll"], [("queued", "q-1")])              # request id recorded before polling

    # --- kills and failures keep the spend counted
    def test_ctrl_c_after_submit_still_counts_the_spend(self):
        def poll(req):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self.run_gen(TC.Router(routes(status=poll)))
        row = self.rows()[0]
        self.assertEqual((row["request_id"], row["cost_usd_est"]), ("q-1", "0.6000"))
        self.assertIn("interrupted", row["status"])
        self.assertEqual(G.spent_total(), 0.6)

    def test_a_kill_that_never_runs_cleanup_leaves_the_reserved_row_counted(self):
        def die(req):
            raise SystemExit("simulated SIGKILL: no cleanup runs")

        with self.assertRaises(SystemExit):
            self.run_gen(TC.Router(routes(submit=die)))
        self.assertEqual(G.spent_total(), 0.6)

    def test_poll_timeout_is_counted_and_names_the_fetch_command(self):
        code, err, _ = self.run_gen(TC.Router(routes(status={"status": "IN_PROGRESS"})), timeout=20)
        self.assertEqual(code, 1)
        row = self.rows()[0]
        self.assertEqual((row["cost_usd_est"], row["request_id"]), ("0.6000", "q-1"))
        self.assertIn("failed-after-queue", row["status"])
        self.assertIn("fetch --job t1 --request-id q-1", err)

    def test_fetch_collects_the_lost_audio_and_adds_no_cost(self):
        self.run_gen(TC.Router(routes(status={"status": "IN_PROGRESS"})), timeout=20)  # timed out, billed, audio lost
        self.assertEqual(G.spent_total(), 0.6)
        code, err, out = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 0, err + out)
        rows = self.rows()
        self.assertEqual((len(rows), rows[0]["status"], G.spent_total()), (1, "ok (fetched)", 0.6))
        self.assertTrue((self.d / "t1.wav").exists())

    def test_fetch_of_a_request_missing_from_the_ledger_is_counted_again(self):
        code, err, out = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 0, err + out)
        self.assertIn("original row missing", self.rows()[0]["status"])
        self.assertEqual(G.spent_total(), 0.6)

    def test_rejected_format_costs_nothing_and_the_next_format_is_reserved_fresh(self):
        sent = []

        def submit(req):
            body = json.loads(req.data)
            sent.append(body["output_format"])
            if body["output_format"] == "pcm_44100":
                raise http_error(req.full_url, 403, b'{"detail":"Pro tier"}')
            return {"request_id": "q-1", "status_url": STATUS, "response_url": RESULT}

        code, err, _ = self.run_gen(TC.Router(routes(submit=submit)))
        self.assertEqual((code, sent), (0, ["pcm_44100", "mp3_44100_128"]), err)
        rows = self.rows()
        self.assertEqual([(r["status"][:8], r["cost_usd_est"]) for r in rows], [("rejected", "0.0000"), ("ok", "0.6000")])
        self.assertEqual(G.spent_total(), 0.6)

    def test_an_ambiguous_submit_failure_is_counted_and_never_resubmitted(self):
        sent = []

        def submit(req):
            sent.append(1)
            raise urllib.error.URLError("connection reset after the request was sent")

        code, err, _ = self.run_gen(TC.Router(routes(submit=submit)))
        self.assertEqual((code, len(sent)), (1, 1))
        row = self.rows()[0]
        self.assertEqual(row["cost_usd_est"], "0.6000")
        self.assertIn("submit-uncertain", row["status"])

    # --- budget
    def test_hard_cap_and_stop_line_refuse_before_any_call(self):
        self.seed(11.5)
        router = TC.Router([])  # any HTTP call would fail the test
        code, err, _ = self.run_gen(router, no_price_check=True)
        self.assertEqual(code, 5, err)  # 11.50 + 0.60 > the 12 stop line
        self.assertEqual((router.calls, len(self.rows())), ([], 1))
        self.seed(2.5)  # 14.0 spent: still under the cap but past the stop line
        self.assertEqual(self.run_gen(router, no_price_check=True)[0], 5)
        self.seed(0.9)
        self.assertEqual(self.run_gen(router, no_price_check=True)[0], 4)  # 14.9 + 0.6 > 15
        self.assertEqual(router.calls, [])

    def test_flags_can_only_lower_the_limits(self):
        self.assertEqual(G.limits(100, 100), (15.0, 12.0))
        self.assertEqual(G.limits(10, None), (10, 10))
        self.assertEqual(G.limits(None, 8), (15.0, 8))
        self.seed(11.8)
        self.assertEqual(self.run_gen(TC.Router([]), no_price_check=True, cap=999, stop_at=999)[0], 5)

    def test_only_the_lead_file_raises_the_stop_line_and_never_past_the_cap(self):
        approval = self.d / "approval.txt"
        approval.write_text("14\n")
        self.assertEqual(G.limits(), (15.0, 14.0))
        approval.write_text("99")
        self.assertEqual(G.limits(), (15.0, 12.0))
        approval.write_text("banana")
        self.assertEqual(G.limits(), (15.0, 12.0))

    def test_every_campaign_counts_toward_the_one_budget(self):
        self.seed(11.8, campaign="someone-else")
        self.assertEqual(self.run_gen(TC.Router([]), no_price_check=True, campaign="a-new-name")[0], 5)

    def test_dry_run_spends_and_writes_nothing(self):
        router = TC.Router([])
        code, err, _ = self.run_gen(router, no_price_check=True, dry_run=True)
        self.assertEqual((code, router.calls, self.ledger.exists()), (0, [], False))

    def test_live_price_zero_or_wrong_unit_does_not_make_a_call_free(self):
        for price in ({"endpoint_id": MODEL, "unit_price": 0, "unit": "minute"},
                      {"endpoint_id": MODEL, "unit_price": 0.01, "unit": "second"}):
            self.ledger.unlink(missing_ok=True)
            code, err, _ = self.run_gen(TC.Router(routes(pricing={"prices": [price]})))
            self.assertEqual(code, 0, err)
            self.assertEqual(self.rows()[0]["cost_usd_est"], "0.6000", price)
            self.assertIn("table", self.rows()[0]["cost_basis"])

    def test_two_runs_cannot_both_pass_the_cap(self):
        self.seed(11.0)  # 11.0 + 0.6 passes the 12 stop line once; a second 0.6 must not
        results, barrier = [], threading.Barrier(2)

        def attempt():
            barrier.wait()
            try:
                G.reserve({"campaign": "music1", "job": "race"}, 0.6, 15, 12)
                results.append("ok")
            except G.Refuse as exc:
                results.append(exc.code)

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(map(str, results)), ["5", "ok"])
        self.assertEqual(G.spent_total(), 11.6)

    # --- second review (hub 142 adversarial pass)
    def test_the_live_ledger_is_one_fixed_path_outside_every_git_checkout(self):
        self.assertEqual(G.LIVE_LEDGER, Path.home() / ".local/state/megajam/cloud-spend-ledger.csv")
        self.assertNotIn(G.REPO, G.LIVE_LEDGER.parents)
        self.assertNotEqual(G.LIVE_LEDGER, G.REPO / "stages/02_build/output/cloud-spend-ledger.csv")

    def test_the_repo_copy_follows_every_write_to_the_live_ledger(self):
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):  # stand-in for the live path; a temp file, never the real one
            self.seed(1.0)
            self.assertEqual(self.rows(self.repo_copy)[0]["cost_usd_est"], "1.0000")
            G.update_row(self.rows()[0]["row_id"], status="ok")
            self.assertEqual(self.rows(self.repo_copy)[0]["status"], "ok")
            self.assertEqual(self.repo_copy.read_bytes(), self.ledger.read_bytes())  # deterministic: the same bytes

    # --- third review (round 3)
    def test_f1_no_environment_variable_can_move_the_budget(self):
        """MEGAJAM_SPEND_LEDGER used to be honoured for any existing file: `touch x.csv` = a fresh $15. Now it is ignored."""
        for content in (b"", None):  # an empty file, and a file that does not exist
            override = self.d / "override.csv"
            override.unlink(missing_ok=True)
            if content is not None:
                override.write_bytes(content)
            out = subprocess.run(
                [sys.executable, "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import gen_music_fal as G; "
                 "print(G.SPEND_LEDGER); print(hasattr(G, '_live_ledger'))", os.path.join(ROOT, "scripts")],
                capture_output=True, text=True, timeout=60, env=dict(os.environ, MEGAJAM_SPEND_LEDGER=str(override)))
            self.assertEqual(out.stdout.split("\n")[:2], [str(G.LIVE_LEDGER), "False"], out.stderr)

    def test_f1_an_empty_or_foreign_ledger_file_is_corrupt_not_a_fresh_budget(self):
        for content in ("", "job,cost\nx,0.1\n", "timestamp_iso,campaign\n"):  # empty, other columns, a truncated header
            self.ledger.write_text(content)
            router = TC.Router([])
            code, err, _ = self.run_gen(router, no_price_check=True)
            self.assertEqual((code, router.calls), (2, []), content)
            self.assertIn("header", err)
            with self.assertRaises(G.Refuse):
                G.reserve({"job": "x"}, 0.6, 15, 12)
            self.assertEqual(self.ledger.read_text(), content)  # nothing was rewritten

    def test_f1_a_symlinked_ledger_is_refused(self):
        real = self.d / "real.csv"
        G.write_rows(real, [])
        self.ledger.symlink_to(real)
        router = TC.Router([])
        code, err, _ = self.run_gen(router, no_price_check=True)
        self.assertEqual((code, router.calls), (2, []))
        self.assertIn("symlink", err)
        with self.assertRaises(G.Refuse):
            G.spent_total()

    def test_f2_a_probe_ledger_never_refreshes_the_repo_copy(self):
        self.seed(1.0)  # SPEND_LEDGER is a temp file here, not LIVE_LEDGER
        self.assertEqual(G.spent_total(), 1.0)
        self.assertFalse(self.repo_copy.exists())
        self.repo_copy.write_text("committed record\n")
        G.update_row(self.rows()[0]["row_id"], status="ok")
        G.write_rows(self.ledger, self.rows())
        self.assertEqual(self.repo_copy.read_text(), "committed record\n")

    def test_f3_a_missing_empty_or_short_cost_is_corrupt_not_zero(self):
        for row in ({}, {"cost_usd_est": ""}, {"cost_usd_est": "  "}, {"cost_usd_est": None}, {"job": "j"}):
            with self.assertRaises(G.Refuse, msg=row) as cm:
                G.row_cost(row)
            self.assertEqual(cm.exception.code, 2)
        self.seed(14.9)
        good = self.ledger.read_text()
        header = good.splitlines()[0]
        cells = good.splitlines()[1].split(",")
        renamed = header.replace("cost_usd_est", "cost_usd")
        cost_i = G.LEDGER_FIELDS.index("cost_usd_est")
        blank = cells[:cost_i] + [""] + cells[cost_i + 1:]
        for text in (renamed + "\n" + ",".join(cells) + "\n",               # cost column renamed
                     header + "\n" + ",".join(blank) + "\n",                 # empty cost cell
                     header + "\n" + ",".join(cells[:cost_i]) + "\n",        # short row: the cost cell is missing
                     header + "\n" + ",".join(cells + ["x"]) + "\n"):        # long row: cells shifted
            self.ledger.write_text(text)
            router = TC.Router([])
            code, err, _ = self.run_gen(router, no_price_check=True)
            self.assertEqual((code, router.calls), (2, []), text)
            self.assertIn("spend ledger", err)
            with self.assertRaises(G.Refuse):
                G.spent_total()

    def test_f4_fetch_checks_the_ledger_before_any_network_call(self):
        self.seed(1.0)
        rows = self.rows()
        rows[0]["cost_usd_est"] = "nan"
        G.write_rows(self.ledger, rows)
        before = self.ledger.read_text()
        router = TC.Router(routes(status={"status": "COMPLETED"}))
        code, err, out = self.run_cmd(G.cmd_fetch, router, request_id="q-1")
        self.assertEqual((code, router.calls), (2, []))
        self.assertFalse((self.d / "t1.wav").exists() or (self.d / "t1.dl").exists())
        self.assertIn("corrupt", err)
        self.assertIn("not fetching request q-1", err)
        self.assertIn("Nothing was downloaded", err)
        self.assertEqual(self.ledger.read_text(), before)

    def test_f4_a_ledger_that_breaks_after_the_download_is_reported_not_silent(self):
        broke = G.Refuse(2, "the spend ledger broke")
        with mock.patch.object(G, "reserve", side_effect=broke):  # the up-front check passed; the write then fails
            code, err, out = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 2)
        self.assertTrue((self.d / "t1.wav").exists())
        self.assertIn("request q-1 was fetched", err)
        self.assertIn("NOT ledgered", err)
        self.assertIn("$0.60", err)

    def test_f4_forced_booking_does_not_sum_a_corrupt_cell(self):
        rows_before = [{"job": "bad", "cost_usd_est": "nan", "row_id": "r0"}]
        G.write_rows(self.ledger, rows_before)
        rid = G.reserve({"job": "late"}, 0.6, 15, 12, force=True)  # the money is already spent: it is booked regardless
        self.assertIn(rid, [r["row_id"] for r in self.rows()])

    def test_f5_a_malformed_request_id_is_a_clean_exit_2(self):
        for bad in ("../x", "a/b", "a b", "", "x" * 65, "q-1?x=1", "q-1\n"):
            router = TC.Router([])
            code, err, _ = self.run_cmd(G.cmd_fetch, router, request_id=bad)
            self.assertEqual((code, router.calls), (2, []), bad)
            self.assertIn("invalid --request-id", err)
            self.assertNotIn("Traceback", err)
        self.assertEqual(self.rows() if self.ledger.exists() else [], [])

    def test_f5_main_returns_2_for_a_malformed_request_id_without_a_traceback(self):
        argv = ["fetch", "--job", "t1", "--request-id", "../x", "--out", str(self.d / "t1")]
        old = signal.getsignal(signal.SIGTERM)
        self.addCleanup(signal.signal, signal.SIGTERM, old)
        err = io.StringIO()
        with mock.patch.object(G.gen_asset, "merged_env", return_value={}), \
                mock.patch.object(G, "make_provider", side_effect=AssertionError("no provider before the id is checked")), \
                redirect_stderr(err):
            code = G.main(argv)
        self.assertEqual(code, 2)
        self.assertIn("invalid --request-id", err.getvalue())

    # --- vocal-check guards run on the ORIGINAL file (finding 6)
    def vocal_refused(self, src):
        router = TC.Router([])
        with mock.patch.object(G.subprocess, "run", side_effect=AssertionError("ffmpeg must not run")) as run:
            code, err, out = self.run_cmd(G.cmd_vocal_check, router, audio=str(src))
        self.assertEqual((code, router.calls, run.call_count), (2, [], 0), err)
        self.assertIn("refusing", err)
        self.assertFalse(self.ledger.exists())  # nothing reserved either
        return err

    def wav(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            w.writeframes(b"\x00\x00" * 2205)
        return path

    def test_f6_vocal_check_refuses_a_symlink_before_ffmpeg(self):
        real = self.wav(self.d / "real.wav")
        link = self.d / "link.wav"
        link.symlink_to(real)
        self.assertIn("symlink", self.vocal_refused(link))
        dangling = self.d / "dangling.wav"
        dangling.symlink_to(self.d / "nowhere.wav")
        self.assertIn("symlink", self.vocal_refused(dangling))

    def test_f6_vocal_check_refuses_a_directory_or_special_file(self):
        (self.d / "folder.wav").mkdir()
        self.assertIn("not a plain file", self.vocal_refused(self.d / "folder.wav"))

    def test_f6_vocal_check_refuses_uc2_and_ut2004_paths_before_ffmpeg(self):
        for name in ("UC2004", "UC2 Characters for UT2004", "UT2004", "uc2-pc"):
            err = self.vocal_refused(self.wav(self.d / name / "take.wav"))
            self.assertIn("UC2/UT2004", err, name)

    def test_f6_vocal_check_refuses_protected_trees_by_root(self):
        root = self.d / "Unreal Tournament 2004"  # the Steam install: no "uc2" or "ut2004" in its name
        self.assertTrue(len(F.PROTECTED_AUDIO_ROOTS) >= 3)
        with mock.patch.object(F, "PROTECTED_AUDIO_ROOTS", (root,)):
            err = self.vocal_refused(self.wav(root / "System" / "take.wav"))
        self.assertIn("protected tree", err)

    def test_f6_the_default_protected_roots_name_the_pristine_extract_and_the_steam_install(self):
        roots = {str(r) for r in F.PROTECTED_AUDIO_ROOTS}
        self.assertIn(str(Path.home() / "Projects/Unreal/extracted/UC2004"), roots)
        self.assertIn(str(Path.home() / ".local/share/Steam/steamapps/common/Unreal Tournament 2004"), roots)
        self.assertIsNone(F.audio_path_problem(self.wav(self.d / "ok" / "take.wav")))

    # --- fourth review (round 4)
    def spent_export(self):
        """A repo export holding $5.70 of prior spend, as the committed CSV looks after real runs. Returns its bytes."""
        G.write_rows(self.repo_copy, [{"campaign": "music1", "job": "prior", "cost_usd_est": "5.7000", "status": "ok",
                                       "row_id": "p1"}])
        return self.repo_copy.read_bytes()

    def test_r4_1_a_missing_or_empty_live_ledger_with_a_spent_export_refuses(self):
        before = self.spent_export()
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):  # stand-in for the live path: a temp file, never the real one
            for header_only in (False, True):  # a missing live ledger, then a header-only one
                self.ledger.unlink(missing_ok=True)
                if header_only:
                    G.write_rows(self.ledger, [])
                for kw in ({}, {"dry_run": True}):
                    router = TC.Router(routes())
                    code, err, _ = self.run_gen(router, **kw)
                    self.assertEqual((code, router.calls), (2, []), (header_only, kw))  # not even the free pricing GET
                    self.assertIn("$5.70 of prior spend in 1 rows", err)
                    self.assertIn("install -D -m 600 ", err)
                router = TC.Router(routes(status={"status": "COMPLETED"}))
                code, err, _ = self.run_cmd(G.cmd_fetch, router, request_id="q-1")
                self.assertEqual((code, router.calls), (2, []))
                self.assertFalse((self.d / "t1.wav").exists())
            self.assertEqual(self.repo_copy.read_bytes(), before)  # the export was never overwritten
            self.assertEqual(self.ledger.read_text().count("\n"), 1)  # still header-only: no row was written

    def test_r4_1_restoring_the_export_by_hand_resumes_spending_on_top_of_it(self):
        self.spent_export()
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            self.ledger.write_bytes(self.repo_copy.read_bytes())  # the documented `install -D -m 600 export live`
            code, err, _ = self.run_gen(TC.Router(routes()))
            self.assertEqual(code, 0, err)
            self.assertEqual(G.spent_total(), 6.3)  # 5.70 + 0.60: the prior spend still counts
            self.assertEqual(self.repo_copy.read_bytes(), self.ledger.read_bytes())

    def test_r4_1_the_very_first_ledger_is_still_possible_when_the_export_is_empty_or_absent(self):
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            for prepare in (lambda: None, lambda: G.write_rows(self.repo_copy, [])):  # export absent, then header-only
                self.ledger.unlink(missing_ok=True)
                prepare()
                code, err, _ = self.run_gen(TC.Router(routes()))
                self.assertEqual(code, 0, err)
                self.assertEqual(len(self.rows()), 1)
                self.assertEqual(len(self.rows(self.repo_copy)), 1)

    def test_r4_1_a_corrupt_export_also_refuses_a_missing_live_ledger(self):
        self.repo_copy.write_text("not,the,ledger\n1,2,3\n")
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            router = TC.Router([])
            code, err, _ = self.run_gen(router, no_price_check=True)
            self.assertEqual((code, router.calls), (2, []))
            self.assertFalse(self.ledger.exists())

    def test_r4_1_an_empty_write_never_overwrites_a_non_empty_export(self):
        before = self.spent_export()
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            G.write_rows(self.ledger, [])
        self.assertEqual(self.repo_copy.read_bytes(), before)

    def test_r4_2_a_ledger_that_turns_structurally_corrupt_during_the_fetch_prints_the_notice(self):
        self.seed(1.0)

        def corrupt_during_poll(req):  # healthy at the up-front check, a truncated row by the time the audio is saved
            lines = self.ledger.read_text().splitlines()
            self.ledger.write_text(lines[0] + "\n" + lines[1].rsplit(",", 3)[0] + "\n")
            return {"status": "COMPLETED"}

        code, err, _ = self.run_cmd(G.cmd_fetch, TC.Router(routes(status=corrupt_during_poll)), request_id="q-1")
        self.assertEqual(code, 2)
        self.assertTrue((self.d / "t1.wav").exists())
        self.assertIn("request q-1 was fetched to", err)
        self.assertIn("reading the ledger failed", err)
        self.assertIn("NOT in the budget", err)

    def test_r4_2_the_notice_says_which_step_failed_and_what_it_means(self):
        broke = G.Refuse(2, "the spend ledger broke")
        rid = G.reserve({"job": "seed"}, 0.6, 99, 99)
        G.update_row(rid, request_id="q-1")  # the original row exists
        with mock.patch.object(G, "update_row", side_effect=broke):
            code, err, _ = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 2)
        self.assertIn("updating the original row failed", err)
        self.assertIn("already booked", err)
        self.assertNotIn("NOT ledgered", err)
        self.ledger.unlink()  # now no row for q-1: the charge is booked as reserved, then the update fails
        with mock.patch.object(G, "update_row", side_effect=broke):
            code, err, _ = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 2)
        self.assertIn("finishing the booked row failed", err)
        self.assertIn("booked only as a reserved row", err)
        self.assertEqual(G.spent_total(), 0.6)

    def test_r4_2_a_fully_booked_fetch_is_not_an_error_if_only_the_cap_check_fails(self):
        with mock.patch.object(G, "spent_total", side_effect=[0.0, G.Refuse(2, "boom")]):  # pre-check, then the total
            code, err, out = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 0, err)
        self.assertIn("the fetch is booked", err)
        self.assertNotIn("NOT ledgered", err)
        self.assertIn("original row missing", self.rows()[0]["status"])

    # --- vocal-check: every local validation runs before the charge is booked (round 4, finding 3)
    def vocal_run(self, payload, router=None, tmp_prefix=None, **kw):
        src = self.wav(self.d / "take.wav")
        kw.setdefault("no_price_check", True)  # so the router sees only what the vocal gate itself sends
        stt = routes(model=F.STT_MODEL, pricing={"prices": []})
        stt[2] = (stt[2][0], "GET", {"text": "Thank you.", "chunks": []})
        router = router or TC.Router(stt)

        def fake_ffmpeg(cmd, **_):
            Path(cmd[-1]).write_bytes(payload)  # stands in for the transcode: the temp copy is whatever we say
            return subprocess.CompletedProcess(cmd, 0)

        real_td = tempfile.TemporaryDirectory
        with mock.patch.object(G.subprocess, "run", side_effect=fake_ffmpeg), \
                mock.patch.object(G.tempfile, "TemporaryDirectory", lambda: real_td(prefix=tmp_prefix or "tmp")):
            code, err, out = self.run_cmd(G.cmd_vocal_check, router, audio=str(src), **kw)
        return code, err, out, router

    def assert_nothing_sent_or_booked(self, code, err, router):
        self.assertEqual((code, router.calls), (2, []), err)
        self.assertIn("nothing was sent", err)
        self.assertNotIn("Traceback", err)
        self.assertFalse(self.ledger.exists())  # no phantom "interrupted (counted)" row
        self.assertFalse((self.d / "take.wav.vocal.json").exists())

    def test_r4_3_an_oversize_transcode_is_refused_before_anything_is_booked(self):
        big = b"ID3" + b"\x00" * F.MAX_STT_BYTES  # one byte over the cap
        for kw in ({}, {"dry_run": True}):
            code, err, _, router = self.vocal_run(big, **kw)
            self.assert_nothing_sent_or_booked(code, err, router)
            self.assertIn("too large", err)

    def test_r4_3_a_transcode_that_is_not_wav_or_mp3_is_refused_before_anything_is_booked(self):
        code, err, _, router = self.vocal_run(b"MZ" + b"\x00" * 50)
        self.assert_nothing_sent_or_booked(code, err, router)
        self.assertIn("not a WAV or MP3", err)

    def test_r4_3_the_temp_copys_own_name_is_not_judged_by_the_uc2_test(self):
        code, err, out, router = self.vocal_run(b"ID3" + b"\x00" * 50, tmp_prefix="tmpuc2")  # random tempfile names can hit
        self.assertEqual(code, 0, err)
        self.assertEqual((router.calls[0][0], F.STT_MODEL in router.calls[0][1]), ("POST", True))  # the upload happened
        self.assertIn("ok (vocal gate: clean)", self.rows()[0]["status"])

    def test_r4_3_a_local_check_that_fires_after_booking_leaves_no_charge(self):
        with mock.patch.object(F.FalMusicProvider, "transcribe", side_effect=ValueError("late local check")):
            code, err, _, router = self.vocal_run(b"ID3" + b"\x00" * 50)
        self.assertEqual((code, router.calls), (2, []))
        self.assertNotIn("Traceback", err)
        self.assertIn("late local check", err)
        row = self.rows()[0]
        self.assertEqual((row["cost_usd_est"], G.spent_total()), ("0.0000", 0.0))
        self.assertIn("rejected-not-sent", row["status"])

    def test_r4_3_stt_inputs_skips_the_name_test_only_for_a_trusted_copy(self):
        uc2 = self.d / "uc2" / "vc.mp3"
        uc2.parent.mkdir()
        uc2.write_bytes(b"ID3" + b"\x00" * 50)
        with self.assertRaises(ValueError):
            F.stt_inputs(uc2)
        inputs = F.stt_inputs(uc2, trusted_copy=True)
        self.assertTrue(inputs["audio_url"].startswith("data:audio/mpeg;base64,"))
        with self.assertRaises(ValueError):  # a trusted copy must still be a plain file of the right size and format
            F.stt_inputs(self.d / "uc2", trusted_copy=True)

    # --- fifth review (round 5): a live ledger BEHIND the export, vocal-check ledger order, the printed restore line
    def led(self, *pairs):
        """Ledger rows from (row_id, cost) pairs."""
        return [{"campaign": "music1", "job": f"j-{rid}", "cost_usd_est": f"{cost:.4f}", "status": "ok", "row_id": rid}
                for rid, cost in pairs]

    def behind_setup(self):
        """The review's repro: the export has 12 rows / $5.70; the live ledger has ONE row of $0.60 that is not among them."""
        G.write_rows(self.repo_copy, self.led(*[(f"e{i}", 0.5) for i in range(11)], ("e11", 0.2)))
        G.write_rows(self.ledger, self.led(("m1", 0.6)))  # not the live path yet: neither file's bytes are touched by this
        return self.led(("m1", 0.6)), self.led(*[(f"e{i}", 0.5) for i in range(11)], ("e11", 0.2))

    def test_r5_1_a_live_ledger_behind_the_export_refuses_before_any_call(self):
        self.behind_setup()
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            before = (self.ledger.read_bytes(), self.repo_copy.read_bytes())
            for kw in ({}, {"dry_run": True}):
                router = TC.Router(routes())
                code, err, _ = self.run_gen(router, **kw)
                self.assertEqual((code, router.calls), (2, []), (kw, err))  # not even the free pricing GET
                self.assertIn("BEHIND the repo export", err)
                self.assertIn("lacks 12 of the export's rows ($5.70", err)
                self.assertIn("do NOT copy the export over it", err)  # the live row m1 is not in the export: a copy drops it
                self.assertNotIn("install -D", err)
            router = TC.Router(routes(status={"status": "COMPLETED"}))
            code, err, _ = self.run_cmd(G.cmd_fetch, router, request_id="q-1")
            self.assertEqual((code, router.calls), (2, []))
            self.assertFalse((self.d / "t1.wav").exists())
            src = self.wav(self.d / "take.wav")
            for kw in ({}, {"dry_run": True}):
                router = TC.Router([])
                with mock.patch.object(G.subprocess, "run", side_effect=AssertionError("ffmpeg must not run")):
                    code, err, _ = self.run_cmd(G.cmd_vocal_check, router, audio=str(src), **kw)
                self.assertEqual((code, router.calls), (2, []), (kw, err))
            self.assertEqual((self.ledger.read_bytes(), self.repo_copy.read_bytes()), before)  # nothing overwritten

    def test_r5_1_after_the_hand_merge_spending_resumes_on_top_of_both(self):
        live, export = self.behind_setup()
        G._atomic_csv(self.ledger, live + export)  # what the message asks for: append the export's missing rows by hand
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            code, err, _ = self.run_gen(TC.Router(routes()))
            self.assertEqual(code, 0, err)
            self.assertEqual(G.spent_total(), 6.9)  # 0.60 + 5.70 + the new 0.60
            self.assertEqual(len(self.rows(self.repo_copy)), 14)

    def test_r5_1_a_live_ledger_that_is_a_subset_of_the_export_is_told_to_copy_it(self):
        export = self.led(("e1", 0.5), ("e2", 0.5))
        G.write_rows(self.repo_copy, export)
        G.write_rows(self.ledger, export[:1])
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            router = TC.Router(routes())
            code, err, _ = self.run_gen(router)
            self.assertEqual((code, router.calls), (2, []), err)
            self.assertIn("lacks 1 of the export's rows ($0.50; row_id e2)", err)
            self.assertIn("install -D -m 600 ", err)  # the export holds every live row: copying it loses nothing
            self.assertNotIn("do NOT copy", err)

    def test_r5_1_a_live_ledger_ahead_of_a_stale_export_is_normal_and_passes(self):
        export = self.led(("e1", 0.6), ("e2", 0.6))  # this worktree's export is older than the live ledger
        G.write_rows(self.repo_copy, export)
        # live: e1 was zeroed by a failed call in another worktree (same row_id, lower cost), plus a row the export lacks
        G._atomic_csv(self.ledger, [dict(export[0], cost_usd_est="0.0000", status="rejected"), export[1],
                                    *self.led(("n1", 0.6))])
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            code, err, _ = self.run_gen(TC.Router(routes()))
            self.assertEqual(code, 0, err)
            self.assertEqual(G.spent_total(), 1.8)
            self.assertEqual(len(self.rows(self.repo_copy)), 4)  # the export caught up

    def test_r5_1_a_legacy_row_without_a_row_id_is_matched_by_all_its_cells(self):
        legacy = {"campaign": "music1", "job": "old", "cost_usd_est": "0.6000", "status": "ok"}
        G.write_rows(self.repo_copy, [legacy])
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            G._atomic_csv(self.ledger, [legacy, *self.led(("n1", 0.6))])
            self.assertEqual(len(G.read_rows(self.ledger)), 2)
            G._atomic_csv(self.ledger, self.led(("n1", 0.6)))
            with self.assertRaises(G.Refuse) as cm:
                G.read_rows(self.ledger)
            self.assertIn("(no row_id)", str(cm.exception))

    def test_r5_1_an_unreadable_export_refuses_even_when_the_live_ledger_has_rows(self):
        self.seed(1.0)  # a healthy live ledger; the export is what cannot be read
        self.repo_copy.write_text("<<<<<<< HEAD\nnot,the,ledger\n")  # e.g. a git conflict left in the tracked copy
        before = (self.ledger.read_bytes(), self.repo_copy.read_bytes())
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            router = TC.Router(routes())
            code, err, _ = self.run_gen(router)
            self.assertEqual((code, router.calls), (2, []), err)
            self.assertIn("is not a usable ledger", err)
            self.assertIn("git checkout -- ", err)
        self.assertEqual((self.ledger.read_bytes(), self.repo_copy.read_bytes()), before)

    def test_r5_1_a_write_landing_between_the_two_reads_never_makes_the_reader_refuse(self):
        a, b = self.led(("a", 0.5)), self.led(("b", 0.5))
        G.write_rows(self.repo_copy, a)
        with mock.patch.object(G, "LIVE_LEDGER", self.ledger):
            G.write_rows(self.ledger, a)
            real, calls = G._parse_ledger, []

            def racing(path):
                rows = real(path)
                calls.append(Path(path).name)
                if len(calls) == 1:  # another worktree books a charge right after our FIRST read (live first, then export)
                    G.write_rows(self.ledger, a + b)
                return rows

            with mock.patch.object(G, "_parse_ledger", racing):
                rows = G.read_rows(self.ledger)  # export read first, so the live read that follows has everything
            self.assertEqual(len(calls), 2)
            self.assertEqual([r["row_id"] for r in rows], ["a", "b"])

    def test_r5_2_vocal_check_checks_the_ledger_before_ffprobe_pricing_or_ffmpeg(self):
        self.seed(1.0)
        rows = self.rows()
        rows[0]["cost_usd_est"] = "nan"
        G._atomic_csv(self.ledger, rows)
        src = self.wav(self.d / "take.wav")
        for kw in ({}, {"dry_run": True}):
            router = TC.Router([])
            with mock.patch.object(G.subprocess, "run", side_effect=AssertionError("ffmpeg must not run")) as run:
                code, err, _ = self.run_cmd(G.cmd_vocal_check, router, audio=str(src), **kw)  # price check left ON
            self.assertEqual((code, router.calls, run.call_count), (2, [], 0), (kw, err))
            self.assertIn("corrupt cost", err)
            self.assertFalse(G.audio_seconds_of.called)  # not even ffprobe
            self.assertNotIn("would transcribe", err)

    def test_r5_2_vocal_check_dry_run_gives_the_same_budget_answer_as_gen(self):
        for seeded, want in ((0.0, 0), (11.98, 5), (14.98, 4)):
            self.ledger.unlink(missing_ok=True)
            if seeded:
                self.seed(seeded)
            code, err, out, router = self.vocal_run(b"ID3" + b"\x00" * 50, dry_run=True)
            self.assertEqual((code, router.calls), (want, []), (seeded, err))
            self.assertIn("would transcribe", out)
            self.assertIn(f"spent+reserved ${seeded:.2f}", out)
            self.assertEqual(G.spent_total(), seeded)  # a dry run books nothing

    def test_r5_3_the_printed_restore_line_works_when_the_state_dir_does_not_exist(self):
        G.write_rows(self.repo_copy, self.led(("e1", 0.6), ("e2", 0.6)))
        live = self.d / "no-state-yet" / "megajam" / "cloud-spend-ledger.csv"  # a second machine: nothing created the dir
        with mock.patch.object(G, "LIVE_LEDGER", live), mock.patch.object(G, "SPEND_LEDGER", live):
            router = TC.Router(routes())
            code, err, _ = self.run_gen(router)
            self.assertEqual((code, router.calls), (2, []), err)
            self.assertFalse(live.parent.exists())
            self.assertNotIn("cp ", err)
            line = next(ln for ln in err.splitlines() if ln.startswith("  install "))
            argv = shlex.split(line)
            self.assertEqual(argv[:4], ["install", "-D", "-m", "600"])
            self.assertEqual(argv[4:], [str(self.repo_copy), str(live)])
            plain = subprocess.run(["cp", str(self.repo_copy), str(live)], capture_output=True)
            self.assertNotEqual(plain.returncode, 0)  # the old `cp EXPORT LIVE` line fails here
            done = subprocess.run(argv, capture_output=True, text=True)  # the printed line, run as printed
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(live.read_bytes(), self.repo_copy.read_bytes())
            self.assertEqual(live.stat().st_mode & 0o777, 0o600)
            code, err, _ = self.run_gen(TC.Router(routes()))
            self.assertEqual(code, 0, err)
            self.assertEqual(G.spent_total(), 1.8)  # 0.60 + 0.60 restored, plus the new 0.60

    def test_nan_and_inf_never_get_through(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            self.assertEqual(F.unit_price_for(MODEL, bad, "minute")[0], 0.6, bad)
            with self.assertRaises(G.Refuse):
                G.reserve({"job": "x"}, bad, 15, 12)
        self.assertEqual(G.spent_total(), 0.0)  # nothing was written

    def test_a_corrupt_ledger_cost_stops_all_spend(self):
        self.seed(1.0)
        rows = self.rows()
        rows[0]["cost_usd_est"] = "nan"
        G.write_rows(self.ledger, rows)
        router = TC.Router([])
        code, err, _ = self.run_gen(router, no_price_check=True)
        self.assertEqual((code, router.calls), (2, []))
        self.assertIn("corrupt", err)

    def test_fetch_of_an_unledgered_request_is_ledgered_even_past_the_stop_line(self):
        self.seed(11.9)  # 0.6 more would be refused for a new call, but the money is already spent
        code, err, out = self.run_cmd(G.cmd_fetch, TC.Router(routes(status={"status": "COMPLETED"})), request_id="q-1")
        self.assertEqual(code, 0, err + out)
        self.assertEqual((G.spent_total(), (self.d / "t1.wav").exists()), (12.5, True))
        self.assertIn("original row missing", self.rows()[-1]["status"])

    def test_cap_zero_spends_nothing(self):
        router = TC.Router([])
        code, err, _ = self.run_gen(router, no_price_check=True, cap=0)
        self.assertEqual((code, router.calls), (4, []))

    def test_a_changed_price_schema_falls_back_to_the_table(self):
        for body in ({"prices": [{"endpoint_id": MODEL}]}, {"prices": "x"}, {"nope": 1}, ["a"]):
            self.ledger.unlink(missing_ok=True)
            code, err, _ = self.run_gen(TC.Router(routes(pricing=body)))
            self.assertEqual(code, 0, (body, err))
            self.assertEqual(self.rows()[0]["cost_usd_est"], "0.6000")

    def test_stable_needs_the_licence_acknowledgement(self):
        router = TC.Router([])
        code, err, _ = self.run_gen(router, model="stable", prompt="x", seconds=34)
        self.assertEqual((code, router.calls), (2, []))
        self.assertIn("NOT verified", err)

    def test_stable_with_the_flag_runs_per_clip(self):
        code, err, _ = self.run_gen(TC.Router(routes(model=F.MUSIC_FALLBACK_MODEL, pricing={"prices": []})),
                                    model="stable", prompt="funk loop", seconds=34, accept_unverified_licence=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.rows()[0]["cost_usd_est"], "0.2000")

    # --- vocal gate
    def vocal(self, text, **kw):
        src = self.d / "take.wav"
        with wave.open(str(src), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(b"\x00\x00" * 2 * 4410)
        stt = routes(model=F.STT_MODEL, pricing={"prices": []})
        stt[2] = (stt[2][0], "GET", {"text": text, "chunks": [{"text": text}]})
        return self.run_cmd(G.cmd_vocal_check, TC.Router(stt), audio=str(src), **kw), src

    def test_vocal_gate_passes_instrumental_filler(self):
        (code, err, out), src = self.vocal("Thank you.")
        self.assertEqual(code, 0, err + out)
        self.assertIn("VOCAL CLEAN", out)
        self.assertEqual(json.loads((self.d / "take.wav.vocal.json").read_text())["verdict"], "clean")
        row = self.rows()[0]
        self.assertEqual((row["model"], row["cost_usd_est"]), (F.STT_MODEL, "0.0500"))
        self.assertIn("vocal gate: clean", row["status"])

    def test_vocal_gate_rejects_sung_words_with_exit_6(self):
        (code, err, out), _ = self.vocal("Baby baby oh baby I love you so")
        self.assertEqual(code, 6)
        self.assertIn("VOCALS-SUSPECTED", out)

    def test_vocal_check_is_ledgered_before_the_call_and_obeys_the_cap(self):
        self.seed(11.98)
        (code, err, out), _ = self.vocal("Thank you.", no_price_check=True)
        self.assertEqual(code, 5, err)


if __name__ == "__main__":
    unittest.main()

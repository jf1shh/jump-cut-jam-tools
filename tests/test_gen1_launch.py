"""gen1_launch with fake providers: no process, no cloud, no spend."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gen1_launch as g  # noqa: E402

SPEC = importlib.util.spec_from_file_location("gen_asset_t", os.path.join(ROOT, "scripts", "gen_asset.py"))
gen_asset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_asset)


def name_of(cmd):
    return cmd[cmd.index("--name") + 1]


class Launcher(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.lanes = g.jobs()
        for items in self.lanes.values():  # sidecars land in the temp dir, not the repo
            for j in items:
                j["done"] = self.tmp / (j["name"] + ".done")
        patcher = mock.patch.object(g, "STATUS", self.tmp / "status.json")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.calls = []

    def fake_run(self, fail=(), hang=()):
        done = {name_of(j["cmd"]): j["done"] for items in self.lanes.values() for j in items}

        def run(cmd, **kw):
            n = name_of(cmd)
            self.calls.append((n, kw.get("timeout")))
            if n in hang:
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            if n in fail:
                return SimpleNamespace(returncode=1, stdout="", stderr="provider down")
            done[n].write_text("{}")
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")
        return run

    def test_plan_shape(self):
        self.assertEqual([len(v) for v in self.lanes.values()], [12, 12, 7])
        flat = " ".join(" ".join(j["cmd"]) for v in self.lanes.values() for j in v).lower()
        self.assertNotIn("grok", flat)

    def test_concept_jobs_are_concept_only_and_never_3d(self):
        for lane in ("gpt", "fal"):
            for j in self.lanes[lane]:
                self.assertIn("--concept-only", j["cmd"])
                self.assertNotIn("--3d-provider", j["cmd"])
        for j in self.lanes["3d"]:
            self.assertNotIn("--concept-only", j["cmd"])

    def test_resume_skips_jobs_with_a_sidecar(self):
        first = self.lanes["gpt"][0]
        first["done"].write_text("{}")
        with mock.patch.object(g, "RUN", self.fake_run()):
            g.run_all(self.lanes)
        ran = [n for n, _ in self.calls]
        self.assertNotIn(first["name"], ran)
        self.assertEqual(len(ran), 30)

    def test_timeout_and_failure_do_not_stop_other_lanes_and_exit_is_1(self):
        gpt, fal = self.lanes["gpt"][0]["name"], self.lanes["fal"][0]["name"]
        with mock.patch.object(g, "RUN", self.fake_run(fail=(fal,), hang=(gpt,))):
            rc = g.run_all(self.lanes)
        self.assertEqual(rc, 1)
        self.assertEqual(len(self.calls), 31)  # every job was still attempted
        line = g.status_line(self.lanes)
        self.assertIn("gpt 11/12 done, 0 running, 1 failed", line)
        self.assertIn("fal 11/12 done, 0 running, 1 failed", line)
        self.assertIn("3d 7/7 done", line)

    def test_every_job_gets_a_timeout(self):
        with mock.patch.object(g, "RUN", self.fake_run()):
            g.run_all(self.lanes)
        self.assertTrue(all(t and t > 0 for _, t in self.calls))

    def test_all_green_exit_0(self):
        with mock.patch.object(g, "RUN", self.fake_run()):
            self.assertEqual(g.run_all(self.lanes), 0)

    def test_status_line_before_start(self):
        self.assertIn("gpt 0/12 done, 0 running, 0 failed, 12 todo", g.status_line(self.lanes))


class LicenceGate(unittest.TestCase):
    """licence_problems refuses anything but ok / ok-with-credit, so an unsure provider never gets a paid run."""

    def job(self, flag, prov, cmd=None):
        return {"name": f"j_{prov}", "cmd": cmd or ["python3", "scripts/gen_asset.py", flag, prov], "licence": (flag, prov)}

    def test_the_default_plan_passes(self):
        all_jobs = [j for lane in g.jobs().values() for j in lane]
        self.assertEqual(g.licence_problems(all_jobs), [])

    def test_unclear_no_and_not_listed_providers_are_blocked(self):
        verdicts = {"u": "unclear", "n": "no", "x": "not listed", "t": "table unreadable", "m": "missing"}
        jobs = [self.job("--provider", p) for p in verdicts]
        with mock.patch.object(g.gen_asset, "licence_verdict", side_effect=lambda prov, flag: verdicts[prov]):
            bad = g.licence_problems(jobs)
        self.assertEqual(len(bad), len(verdicts), bad)
        for prov, verdict in verdicts.items():
            self.assertIn(f"--provider {prov}: licence {verdict}", bad)

    def test_ok_and_ok_with_credit_are_allowed(self):
        verdicts = {"a": "ok", "b": "ok-with-credit"}
        jobs = [self.job("--3d-provider", p) for p in verdicts]
        with mock.patch.object(g.gen_asset, "licence_verdict", side_effect=lambda prov, flag: verdicts[prov]):
            self.assertEqual(g.licence_problems(jobs), [])

    def test_the_flag_reaches_the_verdict_lookup(self):
        seen = []
        with mock.patch.object(g.gen_asset, "licence_verdict", side_effect=lambda prov, flag: seen.append((flag, prov)) or "ok"):
            g.licence_problems([self.job("--3d-provider", "meshy"), self.job("--provider", "gpt")])
        self.assertEqual(sorted(seen), [("--3d-provider", "meshy"), ("--provider", "gpt")])

    def test_real_table_blocks_tripo_hunyuan_and_unlisted_fal_3d(self):
        for flag, prov, verdict in (("--3d-provider", "tripo3d", "unclear"), ("--3d-provider", "tripo", "unclear"),
                                    ("--3d-provider", "hunyuan3d", "no"), ("--3d-provider", "fal", "not listed")):
            self.assertEqual(g.licence_problems([self.job(flag, prov)]), [f"{flag} {prov}: licence {verdict}"], (flag, prov))

    def test_grok_anywhere_in_a_command_is_blocked(self):
        bad = g.licence_problems([self.job("--provider", "gpt", ["python3", "x.py", "--prompt", "a Grok render"])])
        self.assertEqual(bad, ["j_gpt: grok in the plan"])


class RedoAImportSafety(unittest.TestCase):
    """gen1_redo_a makes paid fal calls; importing it must spawn nothing."""

    def load(self):
        spec = importlib.util.spec_from_file_location("gen1_redo_a_under_test", os.path.join(ROOT, "scripts", "gen1_redo_a.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_import_spawns_nothing(self):
        with mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen, \
                mock.patch("subprocess.check_output") as check_output, mock.patch("subprocess.call") as call, \
                mock.patch("os.system") as system:
            mod = self.load()
        for fn in (run, popen, check_output, call, system):
            fn.assert_not_called()
        self.assertTrue(callable(mod.main))

    def test_main_runs_both_concepts_through_subprocess_only_when_called(self):
        done = SimpleNamespace(returncode=0, stdout="ok", stderr="")
        with mock.patch("subprocess.run", return_value=done) as run:
            mod = self.load()
            run.assert_not_called()
            self.assertEqual(mod.main(), 0)
        self.assertEqual(run.call_count, len(mod.REDO))
        for call in run.call_args_list:
            self.assertIn("--concept-only", call.args[0])
            self.assertIn("fal", call.args[0])


class ConceptOnly(unittest.TestCase):
    def test_gen_asset_concept_only_skips_the_3d_stage(self):
        tmp = tempfile.mkdtemp()
        fake = {"provider": "gpt", "model": "fake", "command": "fake", "seconds": 0.1,
                "attempts": [{"provider": "gpt", "outcome": "ok", "detail": "", "seconds": 0.1}]}
        argv = ["gen_asset.py", "--name", "c1", "--provider", "gpt", "--concept-only", "--prompt", "a car",
                "--out-dir", tmp, "--log", os.path.join(tmp, "log.csv")]

        def fake_generate(choice, prompt, out_path, providers, **kw):
            Path(out_path).write_bytes(b"fake png")  # a real provider writes the image; the sidecar now hashes it
            return fake

        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(gen_asset.concept_providers, "generate_concept", side_effect=fake_generate), \
                mock.patch.object(gen_asset.concept_providers, "default_providers", return_value={}), \
                mock.patch.object(gen_asset, "three_d_stage", side_effect=AssertionError("3D stage must not run")):
            with self.assertRaises(SystemExit) as cm:
                gen_asset.main()
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((Path(tmp) / "c1" / "concept.png.provenance.json").exists())
        self.assertFalse(list(Path(tmp).glob("c1/*.glb")))


if __name__ == "__main__":
    unittest.main()

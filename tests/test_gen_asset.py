import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("gen_asset", os.path.join(ROOT, "scripts", "gen_asset.py"))
gen_asset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_asset)


class Provenance(unittest.TestCase):
    def test_sidecar_records_models_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "concept.png"
            glb = Path(tmp) / "crate.glb"
            image.write_bytes(b"png")
            glb.write_bytes(b"glb")
            args = SimpleNamespace(name="crate", prompt="a crate", model="krea-2-turbo")
            env = gen_asset.threed_env({})
            sidecar = gen_asset.write_provenance(glb, args, image, [["nexus-3d", "--model", "triposplat"]], env)
            record = json.loads(sidecar.read_text())
        self.assertEqual(sidecar.name, "crate.glb.provenance.json")
        self.assertEqual(record["image_model"], "krea-2-turbo")
        self.assertEqual(record["threed_model"], "triposplat")
        self.assertEqual(record["threed_image_checkpoint"], "krea-2-turbo")
        self.assertTrue(record["local_only"])
        self.assertEqual(record["glb_sha256"], hashlib.sha256(b"glb").hexdigest())
        self.assertEqual(record["source_image_sha256"], hashlib.sha256(b"png").hexdigest())

    def test_concept_model_id_is_written_out(self):
        concept = {"provider": "fal", "model": "fal-ai/flux/schnell", "licence_gate": "FAL_TERMS_REVIEWED=x", "attempts": []}
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "concept.png"
            glb = Path(tmp) / "crate.glb"
            image.write_bytes(b"png")
            glb.write_bytes(b"glb")
            args = SimpleNamespace(name="crate", prompt="a crate", model="krea-2-turbo")
            record = json.loads(gen_asset.write_provenance(glb, args, image, [], gen_asset.threed_env({}), concept).read_text())
        self.assertEqual(record["image_model_id"], "fal-ai/flux/schnell")
        self.assertEqual(record["image_provider_model"], "fal-ai/flux/schnell")

    def test_banned_models_refused(self):
        for model in ("qwen-image-2.1", "ultrasharp", "hunyuan3d-2"):
            self.assertIsNotNone(gen_asset.check_model_allowed(model))
        self.assertIsNone(gen_asset.check_model_allowed("krea-2-turbo"))


class EnvFile(unittest.TestCase):
    def write(self, text, mode=0o600):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = Path(d) / "megajam.env"
        p.write_text(text)
        os.chmod(p, mode)
        return p

    def test_parses_key_value_lines_only(self):
        p = self.write("# c\n\nXAI_API_KEY=abc\nexport XAI_TERMS_REVIEWED='2026-11-07'\nbad line\nX=$(touch /nope)\n")
        msgs = []
        got = gen_asset.load_env_file(p, warn=msgs.append)
        self.assertEqual(got["XAI_API_KEY"], "abc")
        self.assertEqual(got["XAI_TERMS_REVIEWED"], "2026-11-07")
        self.assertEqual(got["X"], "$(touch /nope)")  # taken literally, never evaluated
        self.assertNotIn("bad line", got)
        self.assertEqual(len(msgs), 1)  # the malformed line is reported by number, not content
        self.assertIn("line 5", msgs[0])
        self.assertNotIn("bad line", msgs[0])

    def test_bom_and_spaced_equals(self):
        p = self.write("﻿XAI_API_KEY=k1\nOTHER = secretval\n")
        msgs = []
        got = gen_asset.load_env_file(p, warn=msgs.append)
        self.assertEqual(got, {"XAI_API_KEY": "k1"})
        self.assertEqual(len(msgs), 1)
        self.assertNotIn("secretval", msgs[0])

    def test_group_or_world_readable_refused_without_leaking_value(self):
        for mode in (0o640, 0o604, 0o644):
            p = self.write("XAI_API_KEY=supersecret\n", mode)
            msgs = []
            self.assertEqual(gen_asset.load_env_file(p, warn=msgs.append), {})
            self.assertEqual(len(msgs), 1)
            self.assertNotIn("supersecret", msgs[0])

    def test_trailing_comments_stripped(self):
        p = self.write('XAI_API_KEY=xai-abc  # from console\nXAI_TERMS_REVIEWED="2026-11-07" # note\nH=a#b\n')
        got = gen_asset.load_env_file(p, warn=lambda m: self.fail(m))
        self.assertEqual(got["XAI_API_KEY"], "xai-abc")
        self.assertEqual(got["XAI_TERMS_REVIEWED"], "2026-11-07")
        self.assertEqual(got["H"], "a#b")

    def test_empty_env_does_not_mask_file(self):
        p = self.write("XAI_API_KEY=xai-real\n")
        msgs = []
        env = gen_asset.merged_env({"XAI_API_KEY": ""}, path=p, warn=msgs.append)
        self.assertEqual(env["XAI_API_KEY"], "xai-real")
        self.assertEqual(len(msgs), 1)
        self.assertNotIn("xai-real", msgs[0])

    def test_missing_file_is_empty_and_silent(self):
        self.assertEqual(gen_asset.load_env_file("/nonexistent/megajam.env", warn=lambda m: self.fail(m)), {})

    def test_real_env_wins(self):
        p = self.write("XAI_API_KEY=fromfile\nOTHER=1\n")
        env = gen_asset.merged_env({"XAI_API_KEY": "fromenv"}, path=p)
        self.assertEqual(env["XAI_API_KEY"], "fromenv")
        self.assertEqual(env["OTHER"], "1")

    def test_providers_check_sees_file_values(self):
        p = self.write("XAI_API_KEY=k\nXAI_TERMS_REVIEWED=2026-11-07\n")
        env = gen_asset.merged_env({}, path=p)
        providers = gen_asset.concept_providers.default_providers(environ=env)
        status, detail = providers["grok"].check()
        self.assertEqual(status, "ready", detail)
        self.assertNotIn("k\n", detail)
        # a key without the file is still "not configured"
        providers = gen_asset.concept_providers.default_providers(environ={})
        self.assertNotEqual(providers["grok"].check()[0], "ready")


class LicenceVerdict(unittest.TestCase):
    """Banned names are refused up front; otherwise the strictest matching row wins (the real table's names)."""

    def table(self, *rows):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "t.json"
        path.write_text(json.dumps({"entries": [{"id": f"r{i}", "match": m, "verdict": v} for i, (m, v) in enumerate(rows)]}))
        return path

    def test_banned_names_are_refused_even_when_the_table_says_ok(self):
        ok_all = self.table((".*", "ok"))
        for name in ("triposplat-hunyuan3d", "realesrgan-ultrasharp", "qwen-image-2.1"):
            self.assertEqual(gen_asset.licence_verdict(name), "no", name)
            self.assertEqual(gen_asset.licence_verdict(name, ok_all), "no", name)
        self.assertEqual(gen_asset.licence_verdict("x", self.table((".*", "ok"))), "ok")

    def test_banned_check_runs_before_the_table_is_read(self):
        self.assertEqual(gen_asset.licence_verdict("hunyuan3d-2", "/nonexistent/table.json"), "no")
        self.assertEqual(gen_asset.licence_verdict("krea", "/nonexistent/table.json"), "table unreadable")

    def test_meshy_3d_provider_is_unchanged(self):
        self.assertEqual(gen_asset.licence_verdict("meshy", flag="--3d-provider"), "ok-with-credit")

    def test_strictest_row_wins_whatever_the_order(self):
        for rows, want in (((("foo", "ok"), ("foo", "unclear")), "unclear"),
                           ((("foo", "unclear"), ("foo", "ok")), "unclear"),
                           ((("foo", "ok"), ("foo", "ok-with-credit")), "ok-with-credit"),
                           ((("foo", "ok-with-credit"), ("foo", "unclear"), ("foo", "no")), "no"),
                           ((("foo", "ok"), ("foo", "")), "missing"),
                           ((("nomatch", "no"), ("foo", "ok")), "ok")):
            self.assertEqual(gen_asset.licence_verdict("foo", self.table(*rows)), want, rows)
        self.assertEqual(gen_asset.licence_verdict("bar", self.table(("foo", "ok"))), "not listed")

    def test_flag_form_row_and_bare_row_both_count(self):
        t = self.table(("--3d-provider[ =]foo", "ok"), ("foo", "unclear"))
        self.assertEqual(gen_asset.licence_verdict("foo", t, flag="--3d-provider"), "unclear")
        self.assertEqual(gen_asset.licence_verdict("foo", t, flag="--provider"), "unclear")

    def test_tripo3d_is_unclear_because_tripo_cloud_is_listed_unclear(self):
        # real table: tripo-pro "ok" and tripo-cloud "unclear" both match tripo3d; blocked by design (hub 2026-11-12)
        self.assertEqual(gen_asset.licence_verdict("tripo3d"), "unclear")
        self.assertEqual(gen_asset.licence_verdict("tripo3d", flag="--3d-provider"), "unclear")

    def test_the_real_tripo_flag_is_unclear_not_unlisted(self):
        # `--3d-provider tripo` (the real flag) must hit the tripo rows, so it stays "unclear" if either row is edited later
        self.assertEqual(gen_asset.licence_verdict("tripo", flag="--3d-provider"), "unclear")
        # the image lane has no tripo flag form; local TripoSplat and TripoSG are not caught by the new pattern
        self.assertEqual(gen_asset.licence_verdict("triposplat", flag="--3d-provider"), "ok")
        self.assertEqual(gen_asset.licence_verdict("triposg", flag="--3d-provider"), "ok")

    def test_both_tripo_rows_carry_the_provider_flag_pattern(self):
        entries = json.loads((Path(ROOT) / "config" / "asset-licenses.json").read_text())["entries"]
        rows = [e for e in entries if e["id"] in ("tripo-cloud", "tripo-pro")]
        self.assertEqual(sorted(e["id"] for e in rows), ["tripo-cloud", "tripo-pro"])
        for e in rows:
            self.assertRegex("--3d-provider tripo", e["match"])
            self.assertRegex("--3d-provider=tripo", e["match"])
            self.assertNotRegex("--3d-provider triposplat", e["match"])

    def test_asset_licence_ids_are_unique(self):
        entries = json.loads((Path(ROOT) / "config" / "asset-licenses.json").read_text())["entries"]
        ids = [e["id"] for e in entries]
        self.assertEqual(sorted(i for i in set(ids) if ids.count(i) > 1), [])

    def test_the_two_banned_model_patterns_ban_the_same_set(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from chain import licenses as chain_licenses
        def terms(rx):
            return sorted(rx.pattern.split("|"))
        self.assertEqual(terms(gen_asset.BANNED_MODEL_RE), terms(chain_licenses.ALWAYS_BANNED))
        self.assertEqual(gen_asset.BANNED_MODEL_RE.flags & 2, chain_licenses.ALWAYS_BANNED.flags & 2)  # both IGNORECASE
        for name in ("Hunyuan3D-2", "QWEN-IMAGE-2.1", "4x-UltraSharp", "krea-2-turbo", "triposplat"):
            self.assertEqual(bool(gen_asset.BANNED_MODEL_RE.search(name)),
                             bool(chain_licenses.ALWAYS_BANNED.search(name)), name)


if __name__ == "__main__":
    unittest.main()

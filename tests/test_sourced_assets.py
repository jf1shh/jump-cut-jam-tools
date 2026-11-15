"""sourced_assets tests: ledger add/list/credits, validation, duplicates."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sourced_assets as S  # noqa: E402


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = Path(self.tmp.name) / "ledger.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = S.main(["--csv", str(self.csv), *args])
        return code, out.getvalue(), err.getvalue()

    def add(self, name="Kenney Nature Kit", licence="CC0", author="Kenney"):
        return self.run_cli("add", "--name", name, "--url", "https://kenney.nl/assets/nature-kit",
                            "--licence", licence, "--author", author, "--files", "Content/Sourced/Nature",
                            "--date", "2026-11-12")

    def test_add_creates_header_and_row(self):
        code, out, _ = self.add()
        self.assertEqual(code, 0)
        self.assertIn("logged", out)
        lines = self.csv.read_text().splitlines()
        self.assertEqual(lines[0], "name,source_url,licence,author,files_used,date")
        self.assertEqual(len(lines), 2)

    def test_duplicate_rejected(self):
        self.add()
        code, _, err = self.add()
        self.assertEqual(code, 2)
        self.assertIn("already logged", err)

    def test_missing_licence_rejected(self):
        code, _, err = self.add(licence=" ")
        self.assertEqual(code, 2)
        self.assertIn("licence is required", err)

    def test_bad_url_rejected(self):
        code, _, err = self.run_cli("add", "--name", "x", "--url", "kenney", "--licence", "CC0", "--author", "k")
        self.assertEqual(code, 2)
        self.assertIn("http", err)

    def test_list_empty_and_filled(self):
        self.assertIn("empty", self.run_cli("list")[1])
        self.add()
        self.assertIn("Kenney Nature Kit | CC0", self.run_cli("list")[1])

    def test_credits_empty(self):
        self.assertIn("none", self.run_cli("credits")[1])

    def test_credits_splits_by_licence(self):
        self.add()
        self.add(name="Rock by A", licence="CC BY 4.0", author="Alice")
        text = self.run_cli("credits")[1]
        must, free = text.index("Credit required"), text.index("No credit required")
        self.assertLess(must, free)
        self.assertLess(text.index("Rock by A"), free)
        self.assertGreater(text.index("Kenney Nature Kit"), free)
        self.assertIn("not claimed for Visuals", text)

    def test_commas_and_quotes_roundtrip(self):
        S.add_row(self.csv, 'Pack, "Big"', "https://x.test/a", "CC0", "A, B", "a,b", "2026-11-12")
        self.assertEqual(S.read_rows(self.csv)[0]["name"], 'Pack, "Big"')


class RobustnessTest(unittest.TestCase):
    HEADER = "name,source_url,licence,author,files_used,date"
    ROW = "Kenney Nature Kit,https://kenney.nl/assets/nature-kit,CC0,Kenney,/Game/Sourced/Nature,2026-11-12"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = Path(self.tmp.name) / "ledger.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_trailing_newline(self):
        self.csv.write_text(self.HEADER + "\n" + self.ROW, encoding="utf-8")
        S.add_row(self.csv, "Rock", "https://x.test/rock", "CC BY 4.0", "Alice", "", "2026-11-12")
        self.assertEqual([r["name"] for r in S.read_rows(self.csv)], ["Kenney Nature Kit", "Rock"])

    def test_bom_and_padded_header(self):
        self.csv.write_bytes(("﻿" + self.HEADER.replace(",", " , ") + "\r\n" + self.ROW + "\r\n").encode())
        self.assertEqual(S.read_rows(self.csv)[0]["licence"], "CC0")
        S.add_row(self.csv, "Rock", "https://x.test/rock", "CC0", "A", "", "2026-11-12")
        self.assertEqual(len(S.read_rows(self.csv)), 2)

    def test_url_normalised_duplicate(self):
        S.add_row(self.csv, "Pack", "https://Kenney.nl/assets/p", "CC0", "K", "", "2026-11-12")
        for u in ("https://kenney.nl/assets/p/", "http://kenney.nl/assets/p#x"):
            with self.assertRaises(ValueError):
                S.add_row(self.csv, "pack", u, "CC0", "K", "", "2026-11-12")

    def test_bad_date_rejected(self):
        for d in ("not-a-date", "2026-13-01", "2026-1-2"):
            with self.assertRaises(ValueError):
                S.add_row(self.csv, "x", "https://x.test/x", "CC0", "K", "", d)

    def test_pre_window_warning(self):
        self.assertIn("WARNING", S.window_warning("2026-11-10"))
        self.assertIsNone(S.window_warning("2026-11-12"))
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = S.main(["--csv", str(self.csv), "add", "--name", "x", "--url", "https://x.test/x",
                           "--licence", "CC0", "--author", "K", "--date", "2026-11-10"])
        self.assertEqual(code, 0)
        self.assertIn("WARNING", err.getvalue())

    def test_default_date_uses_eastern_time(self):
        # 2026-11-12 06:00 UTC = Nov 11 10 PM PT = Nov 12 1 AM ET: window is open.
        from datetime import datetime, timezone
        from unittest import mock
        instant = datetime(2026, 11, 12, 6, 0, tzinfo=timezone.utc).timestamp()
        err = io.StringIO()
        with mock.patch("time.time", return_value=instant), \
                redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = S.main(["--csv", str(self.csv), "add", "--name", "x", "--url", "https://x.test/x",
                           "--licence", "CC0", "--author", "K"])
        self.assertEqual(code, 0)
        self.assertEqual(S.read_rows(self.csv)[0]["date"], "2026-11-12")
        self.assertNotIn("WARNING", err.getvalue())

    def test_extra_column_survives_add(self):
        self.csv.write_text("name,source_url,licence,author,files_used,date,licence_text\n"
                            "Kit,https://kenney.nl/a,CC0,Kenney,,2026-11-12,\"Creative Commons Zero, CC0\"\n",
                            encoding="utf-8")
        S.add_row(self.csv, "Rock", "https://x.test/rock", "CC BY 4.0", "Alice", "", "2026-11-12")
        text = self.csv.read_text(encoding="utf-8")
        self.assertIn("licence_text", text)
        self.assertIn("Creative Commons Zero", text)

    def test_cc0_page_wording_needs_no_credit(self):
        for lic in ("CC0 1.0 Universal", "Creative Commons CC0", "CC0-1.0", "CC0"):
            self.assertFalse(S.needs_credit(lic), lic)
        self.assertTrue(S.needs_credit("CC BY 4.0"))
        for lic in ("Creative Commons 0", "CC-0", "CC 0", "Creative Commons Zero v1.0 Universal"):
            self.assertFalse(S.needs_credit(lic), lic)

    def test_mixed_licence_still_needs_credit(self):
        for lic in ("CC0 textures, CC BY 4.0 models", "CC BY 4.0 (not CC0)",
                    "Public domain sounds + CC-BY 3.0 music"):
            self.assertTrue(S.needs_credit(lic), lic)


if __name__ == "__main__":
    unittest.main()

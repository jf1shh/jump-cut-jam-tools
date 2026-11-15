import re
import unittest
from datetime import date
from pathlib import Path

CANON = Path(__file__).resolve().parent.parent / "_config" / "reference" / "canon"
TIERS = {"tested", "epic", "community"}


def parse_front_matter(text):
    """Return the front matter as a dict, or None if the file does not start with one."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        key, sep, value = line.partition(":")
        if not sep:
            return None
        meta[key.strip()] = value.strip()
    return None  # never closed


def notes():
    """Every file the Nexus ingest would load: recursive, '.md' matched case-insensitively."""
    return sorted(p for p in CANON.rglob("*") if p.is_file() and p.suffix.lower() == ".md")


class CanonFrontMatter(unittest.TestCase):
    def test_canon_has_notes(self):
        self.assertTrue(notes(), "_config/reference/canon has no notes")

    def test_canon_is_flat_and_lowercase_md(self):
        for path in notes():
            with self.subTest(note=str(path.relative_to(CANON))):
                self.assertEqual(path.parent, CANON, "keep _config/reference/canon flat (ingest walks subfolders)")
                self.assertEqual(path.suffix, ".md", "use a lowercase .md extension")

    def test_every_note_has_valid_front_matter(self):
        for path in notes():
            with self.subTest(note=path.name):
                meta = parse_front_matter(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(meta, "missing or unclosed front matter")
                self.assertIn(meta.get("tier"), TIERS)
                self.assertTrue(meta.get("source"), "empty source")
                updated = meta.get("updated", "")
                self.assertRegex(updated, r"^\d{4}-\d{2}-\d{2}$")
                date.fromisoformat(updated)  # rejects 2026-13-45

    def test_notes_have_a_title(self):
        for path in notes():
            with self.subTest(note=path.name):
                body = path.read_text(encoding="utf-8").split("---", 2)[-1]
                self.assertTrue(re.search(r"^# \S", body, re.M), "no # title")

    def test_every_note_is_listed_in_canon_index(self):
        index = (CANON.parent.parent / "CANON.md").read_text(encoding="utf-8")
        counts = {}
        for path in notes():
            if path.name == "README.md":
                self.assertIn("_config/reference/canon/README.md", index)
                continue
            prefix = path.name.split("-", 1)[0]
            with self.subTest(note=path.name):
                self.assertIn(prefix, {"jam", "ai3d", "ue"}, "new prefix: add an index row for it")
            counts[prefix] = counts.get(prefix, 0) + 1
        for prefix, n in counts.items():
            with self.subTest(prefix=prefix):
                self.assertIn(f"`_config/reference/canon/{prefix}-*.md` ({n})", index,
                              "update the glob row and its count in _config/CANON.md")

    def test_no_raw_transcripts(self):
        for path in notes():
            with self.subTest(note=path.name):
                self.assertLess(len(path.read_text(encoding="utf-8")), 8000, "note too long; keep it short")


class CanonWriterEmbeddings(unittest.TestCase):
    """The writer must embed through Nexus's embeddings server, not the chat server (Lemonade 404s)."""

    def test_writer_uses_embedding_base_url(self):
        src = (Path(__file__).resolve().parent.parent / "scripts" / "sync_project_canon.py").read_text(encoding="utf-8")
        self.assertIn("base_url=settings.embedding_base_url", src)
        self.assertIn("urlparse(settings.embedding_base_url).hostname", src)
        self.assertNotIn("settings.llm_base_url", src)


if __name__ == "__main__":
    unittest.main()

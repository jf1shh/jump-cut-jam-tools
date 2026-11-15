---
tier: tested
source: _config/reference/canon/README.md
updated: 2026-11-10
---

# MegaJam canon: how it works

This folder is the corpus for the `megajam_canon` collection in Nexus. One short note per topic, in our own words.
Ask it with `scripts/ask_canon.sh "your question"`. Load it with `scripts/canon_ingest.sh` (the hub runs this; it needs the local model host and GPU).

## Tiers (how much to trust a note)

| Tier | Meaning |
|---|---|
| `tested` | We did it here and it worked (or we saw it fail). Highest trust. |
| `epic` | Epic official docs, forum posts or the Official Rules. Trust, but verify the version (UE 5.9 Preview is the default, 5.8.4 the fallback; *Superseded (2026-11-10):* "UE 5.8.4"). |
| `community` | A video, blog or vendor claim. A lead, not a fact. Test before relying on it. |

## Front matter (required on every file)

```
---
tier: tested | epic | community
source: URL or repo path
updated: YYYY-MM-DD
---
```

`tests/test_canon.py` fails if a file lacks any of these or uses another tier.

## Note shape

- File name: `topic-in-kebab-case.md`, one topic per file, short.
- A `# Title`, then sections that each start `## Tip: ...` with a **Why:** line and a **How to check:** line.
- Your own words. No copied pages, no raw transcripts, no long quotes. Link the source instead.
- Never put gameplay, art or level content here before 2026-11-12 00:00 ET (Rule 7(h)); notes are fine.

## Add a lesson the same day

When something works, breaks or surprises us, write or update a note the same day, before the context is lost.
Wrong notes: fix or delete them the same day too. Then add a line for new files to `_config/CANON.md`
and run `python3 -m unittest tests.test_canon`. After merging, ask the hub to re-run `scripts/canon_ingest.sh`.
A deleted note is removed from the collection by that re-run once Nexus #289 (per-corpus prune) has landed;
until then the old chunks stay.

## One tier per file

Ingest gives each file a single tier from its front matter. A `tested` file must hold only items we ran.
Put forum, webinar, vendor and UNTESTED items in an `epic` or `community` note instead.

## Caveat on the Epic notes

The `ue-*` notes were written from our knowledge base and from memory of the Epic doc tree on 2026-11-06.
The doc URLs were not re-fetched that day. Treat option names as hints and confirm in the editor or on the page.

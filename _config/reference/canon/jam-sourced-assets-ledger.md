---
tier: tested
source: scripts/sourced_assets.py
updated: 2026-11-10
---

# Sourced assets: log every one with its licence line

## Tip: no licence line, no import
- **Why:** sourced (non-original) assets are allowed only if licensed and listed (Rules 1(d), 15(c)). They are
  not scored. AI-generated content is not "sourced" and does not go in the ledger.
- **How to check:** `python3 scripts/sourced_assets.py add --name ... --url ... --licence ... --author ... --files ...`
  in the same minute as the import. The ledger is `stages/02_build/output/sourced-assets.csv` (header only until the window opens).
  `add` exits 2 with an error if name, url, licence or author is empty, if the url is not http(s), if the date is
  not `YYYY-MM-DD`, or if the same name and url are already logged (a tolerant match: http vs https, case, a
  trailing slash do not make a new entry).

## Tip: only a whole-line CC0 match skips the credit
- **Why:** `credits` splits the ledger into "credit required" and "no credit required, listed for completeness".
  A licence goes in the second list only if the whole line is a CC0 or public-domain spelling (`CC0`, `CC0 1.0`,
  `CC0 1.0 Universal`, `Creative Commons Zero`, `public domain`), or is one of the Fab Standard / Epic Content /
  UE EULA names. A mixed bundle such as `CC0 textures, CC BY 4.0 models` is credited, and so is `CC0-ish`.
- **How to check:** `python3 scripts/sourced_assets.py credits` prints the block for the itch.io page. Copy the
  exact licence line from the pack page into `--licence`; do not paraphrase it.

## Tip: a pre-window date warns, because the ledger is Rule 7(h) evidence
- **Why:** importing a pack before 2026-11-12 00:00 ET (Nov 11, 9:00 PM PT) may break Rule 7(h). The plan's safe
  reading is: claim packs into the library and keep files outside the repo, import only in the window.
- **How to check:** `add` prints a `WARNING` on stderr for an earlier date but still logs it. The plan and pack
  shortlist are in `stages/02_build/references/sourced-assets-plan.md`. Tests: `python3 -m unittest tests.test_sourced_assets`.

## Tip: check `aiTrainingForbidden` on every Fab item before you use it
- **Why:** the 5.9 asset test read the Fab listings: three of nine claimed items carry `aiTrainingForbidden=true` (two asset packs and the platformer bundle), which sits badly with our AI-use disclosure. Sourced assets must still be listed (Rule 15(c)) and are not scored (`asset-test-ue59-2026-11-10.md:56-58`).
- **How to check:** `GetFabListingDetails` shows the flag; skip or ask the owner for any item where it is true. Log each item you keep with `sourced_assets.py add`.

## Tip: the Fab toolset exists on 5.9, but needs one owner sign-in
- **Why:** `FabToolset` (search, details, install, `FabSignIn`) loaded in the 5.9 editor. Library search and install say "Not signed in to Fab". The platformer bundle is a complete project with no in-editor install (`asset-test-ue59-2026-11-10.md:48-73`).
- **How to check:** the owner signs in once before the window; then `mx.py call FabToolset.FabToolset SearchFabMyLibrary '{"Count":12}'` lists the library.

---
tier: tested
source: stages/02_build/references/force-save-level.md
updated: 2026-11-10
---

# Saving the level: trust the file on disk, not the editor

## Tip: "saved" from the editor does not mean the .umap changed
- **Why:** in mock jam 10 the level edits made over MCP never reached the `.umap`. `save_assets` said "already
  saved" because it skips packages it believes are clean, and the packaged build shipped the old level.
- **How to check:** run `python3 scripts/force_save_level.py --expect-actor <label you placed>` before every
  package step. `VERIFIED` (exit 0) means safe to package. `NOT VERIFIED` (exit 1) means do not package.

## Tip: the proof is the file's mtime and contents, then a reload
- **Why:** the script forces a write, then looks at the disk itself. The `.umap` must exist, start with the
  Unreal package header, have a newer mtime, and a different hash than before. A save that writes nothing fails
  on the mtime check. It also checks the `__ExternalActors__` folder, because placed actors live there (One File
  Per Actor), not in the `.umap`.
- **How to check:** after the disk checks pass, the script reloads the level and requires the same actor count
  plus every `--expect-actor` label. If a disk check fails it does not reload, because a reload would throw away
  the unsaved edits. Use `--allow-unchanged` only when you made no edits on purpose; the mtime must still move.

## Tip: when it fails twice, force a write by hand, then use --verify-only
- **Why:** `AssetTools.duplicate_asset` of the map is a forced write of the in-memory level. The script does not
  do this itself, because it would leave a second `.umap` in the project.
- **How to check:** after the duplicate is moved over the original, run
  `python3 scripts/force_save_level.py --verify-only --expect-actor <label>`. It does no save. It checks the file
  has the package header and is not empty, then reloads the level to find the expected actors. It refuses to run
  without at least one `--expect-actor`.

## Tip: on 5.9 `force_save_level.py` needed two fixes, then passed live
- **Why:** first live 5.9 run (mock 16) failed: `AttributeError: 'Package' object has no attribute 'mark_package_dirty'`, and `--verify-only` gave `ValueError: line 57: imports must be at the top level of the script.` Fixed (use `Object.modify(True)` when the 5.8 call is missing; `import uuid` at the top) (merged to master 2026-11-11), then save + `--verify-only` PASSED live (VERIFIED, 36 actors). Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** `git log --oneline -- scripts/force_save_level.py` shows the mock 16 fix (merged 2026-11-11); then save + `--verify-only` prints VERIFIED on 5.9.

# Diversion for the jam's Unreal project

Owner decision 2026-11-11: try Diversion alongside GitHub for the MegaJam entry. Set up and
round-trip tested by the hub on 2026-11-11 (Linux desktop).

## The split

| What | Where | Why |
|---|---|---|
| The UE project: `.uproject`, `Config/`, `Content/`, `Source/` (if any), `.mcp.json` | Diversion repo `megajam-game`, local folder `~/Projects/megajam-game` | Built for big binary assets (`.uasset`/`.umap`); syncs on save |
| Code, scripts, docs, canon, tests, CI | GitHub, this repo (`~/Projects/megajam`) | PRs, CI, review flow as before |

There is no git <-> Diversion sync (that is Enterprise only), so nothing is mirrored between the two.
Do not put the UE project inside this git repo, and do not put tools or docs in the Diversion repo.

## Setup (done)

- CLI: `dv` v1.6.1129 at `~/.diversion/bin/dv` (symlink `~/.local/bin/dv`). Installer read first;
  its shell-rc edits were skipped. Sign-in was the owner's browser login (`dv login`); agents never
  handle Diversion tokens.
- Repo: `dv init ~/Projects/megajam-game megajam-game -f`, in the owner's account.
- `.dvignore` (gitignore syntax) keeps out `Binaries/ Intermediate/ Saved/ DerivedDataCache/ Build/`,
  plugin build folders, `.git/`, IDE and OS junk. Checked: a file under `Saved/` showed no change.
- Round trip: `dv commit -a` -> commit `dv.commit.2` with `README.md` + `.dvignore` visible in the
  web app.
- `scripts/new-mock-project.py NAME ~/Projects/megajam-game` writes into the folder (dry-run checked:
  creates the `.uproject`, `.mcp.json`, `Config/*.ini`; the existing files stay).
- No Legion install: `legion_ship` copies the packaged build as before.

## During the jam

- At 21:00 PT: create the project in `~/Projects/megajam-game` with `new-mock-project.py`, then
  remove `TargetAllowList` from the MCP plugin entry in the `.uproject` (the script still writes it
  and the 5.9 cook fails with it; runbook step 2, plan G4). Write that path as the first line of
  `~/.config/megajam/jam-path` (the backup timer reads it).
- Right after creation, write `IDENTITY.md` + `CONTEXT.md` (Layer 0/1) in `~/Projects/megajam-game` from
  `_config/reference/templates/game-project-identity.md` and `game-project-context.md`; Unreal's own folders
  (`Content/`, `Source/`, `Config/`) stay where they are. They are project docs and go to Diversion with the project.
- Commit at each milestone: `cd ~/Projects/megajam-game && dv commit -a -m "..."`; `dv status`
  shows pending changes and sync state. `dv view --web` opens the repo in the browser.
- Plan: the account shows a Professional trial (21 days from 2026-11-11), so the jam is covered.
  The owner submitted the free Indie plan form (5 seats, 100 GB, 5 repos) on 2026-11-11; Diversion
  says Indie is usable now while the form is reviewed. Nothing is owed by the owner here. The perk promo code is not needed (it only applies past 5 seats or to paid storage).

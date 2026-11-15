# Decoy `UnrealGame.exe` auto-disable: live verification, 2026-11-01

Closes out the open item from mock jam 9 (`stages/00_prep/output/mock-jam-findings-9.md`): a stray
`UnrealGame.exe` was found running on the Legion Go S alongside the real game. Root cause was
never pinned down (Windows auditing was off). PR #63 added an automatic strip step to
`scripts/package-and-push.ps1` that renames the decoy to `UnrealGame.exe.decoy-disabled` on
every package, verified only by a PowerShell syntax check at merge time. This doc is that fix's
first real exercise.

## What happened

1. **PR #61 and #62 merged first** (SkyAtmosphere fix from mock jam 9; durable screenshot
   tooling, `scripts/legion_capture_screenshot.py` + `scripts/legion_screenshot.ps1`, documented
   in `stages/04_ship/references/capture-setup.md`'s "One-off screenshots" section). PR #63 (the decoy-strip
   automation) merged into master as `625a0dc`.
2. **First real packaging run, against the stale Legion checkout**: ran
   `package-and-push.ps1` on the Legion for `MockJam7Game` using its existing repo checkout at
   `C:\Dev\megajam`. Build succeeded (`BUILD SUCCESSFUL`, zip at 508.1 MB), but the decoy exe
   reappeared unrenamed and no "Disabled decoy exe" line printed — looked like the fix itself was
   broken.
3. **Root cause: the Legion's checkout was stale, not the fix.** `C:\Dev\megajam` on the Legion
   was pinned at commit `0e23dd0` — several commits behind master, from before PR #63 merged.
   `git fetch` over SSH failed non-interactively (`wincredman` credential store couldn't prompt
   for GitHub auth over a non-tty SSH session), so the stale checkout hadn't picked up the fix on
   its own.
4. **Worked around by copying the file directly** (`scp scripts/package-and-push.ps1
   <device-host>:C:/Dev/megajam/scripts/package-and-push.ps1`), confirmed present via
   `Select-String -Pattern decoy`, then re-ran the same packaging command.
5. **Second run confirmed the fix works**: log printed
   `Disabled decoy exe: C:\Dev\MockJam7Game\Packaged\Windows\Engine\Binaries\Win64\UnrealGame.exe`,
   build still succeeded and zipped normally (508.1 MB), and a direct `Get-ChildItem` on the
   Legion afterward showed only `UnrealGame.exe.decoy-disabled` in that folder — no plain
   `UnrealGame.exe` survived packaging.

## Verified

- The decoy auto-disable step in `scripts/package-and-push.ps1` works against a real
  `RunUAT BuildCookRun` pass, not just a syntax check.
- The packaged build still zips and stays under the 1 GB gate (508.1 MB) with the step in place.

## New gotcha for the tooling-gotchas log

**The Legion Go S's `C:\Dev\megajam` git checkout can silently drift behind `origin/master`,
and `git fetch`/`pull` over a non-interactive SSH session fails outright** (`wincredman`
credential store can't persist or prompt for GitHub credentials without a tty — `fatal: Unable
to persist credentials with the 'wincredman' credential store`, `/dev/tty: No such device or
address`). Nothing currently re-syncs that checkout automatically. Until the Legion's Git
credential manager is fixed for non-interactive auth (or packaging scripts are scp'd fresh
before every real run instead of relying on the checkout being current), **any session that
expects a merged fix to be live on the Legion should verify the specific file's content there
first** (e.g. `Select-String -Pattern "<marker text>"`), not just assume a merge to master means
the Legion has it.

## Resolved 2026-11-01: non-interactive Legion git auth

The `wincredman`/HTTPS gotcha above is fixed. The Legion's `C:\Dev\megajam` now authenticates to
GitHub over SSH with a dedicated **read-only deploy key**, so `git fetch`/`pull` works from a
non-interactive SSH session without any tty-dependent credential prompt:

- Generated a passphrase-free ed25519 keypair on the Legion at
  `%USERPROFILE%\.ssh\id_ed25519_megajam` (title `legion-megajam-readonly`).
- Added its public half as a **read-only** deploy key on `jf1shh/megajam` via
  `gh repo deploy-key add`. Read-only because the Legion only ever pulls for packaging — it never
  pushes.
- Added an SSH config alias so only this repo's traffic uses that key, leaving any other
  GitHub auth on the Legion untouched:
  ```
  Host github.com-megajam
      HostName github.com
      User git
      IdentityFile %USERPROFILE%\.ssh\id_ed25519_megajam
      IdentitiesOnly yes
      StrictHostKeyChecking accept-new
      BatchMode yes
  ```
- Switched the repo's remote: `git remote set-url origin git@github.com-megajam:jf1shh/megajam.git`.
- Fast-forwarded the stale checkout from `0e23dd0` to `origin/master` (`git fetch` + `git merge
  --ff-only`); the only local divergence was the already-identical `scripts/package-and-push.ps1`
  scp'd in during the original verification above, which `git checkout --` discarded cleanly before
  the fast-forward.

**Gotchas hit while setting this up, for next time:**
- `ssh-keygen -N ""` passed through a PowerShell `-Command` string over SSH does **not** reliably
  produce an empty passphrase — the quoting can land a literal `""` as the passphrase instead,
  which then hangs any later non-interactive auth attempt (BatchMode has no tty to prompt on, so it
  silently exhausts "no more authentication methods" rather than erroring clearly). Generate the key
  via `cmd /c ssh-keygen ... -N ""` instead (cmd's empty-quote handling for `""` is reliable), or
  write passphrase-sensitive PowerShell into a `.ps1` file and run it with `-File` rather than
  inlining it as a `-Command` string over SSH.
- `ssh-keyscan.exe` on this Windows OpenSSH build fails against `github.com` with
  `choose_kex: unsupported KEX method sntrup761x25519-sha512@openssh.com` — don't rely on it to
  seed `known_hosts`. `StrictHostKeyChecking accept-new` in the SSH config lets the real `git
  fetch`/`ssh` call add the host key itself on first connect instead.
- A PowerShell script invoked over SSH via `-Command` (not `-File`) buffers all output until the
  whole process exits, and `<` redirection only works when it sits *outside* the quoted
  `-Command "..."` argument (so the remote shell's `cmd.exe` sees it), never inside the quoted
  PowerShell text. Getting this wrong looks exactly like a hang, not a syntax error.

## Not done

- The test zip (`SilentBlade_MockJam7.zip`, 508.1 MB) and the re-created `Packaged\` /
  `Saved\StagedBuilds\` directories are scratch output on the Legion from the original
  verification run, not committed anywhere — low-priority cleanup, not blocking. A 2026-11-01 probe found no `Packaged\`, `Saved\StagedBuilds\` or test zip under `C:\Dev\megajam` or `C:\Dev` (other locations not checked).

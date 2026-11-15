---
tier: tested
source: stages/00_prep/output/mock-jam-findings-10.md, stages/00_prep/output/mock-jam-findings-11.md, stages/00_prep/output/mock-jam-findings-12.md
updated: 2026-11-10
---

# Legion capture, OBS and video traps (mocks 10 to 12 and 16)

Each item was seen in a mock jam on the Legion Go S (UE 5.8-era builds). Most are n=1. Tools were patched after some
of them; merge status of the mock 12 patches (`stages/00_prep/output/mock12/tools/vptool-patch*.diff`) is unverified. The idle lock has its
own tip in `jam-mock11-legion-and-editor-traps`.

## Tip: the Windows Firewall prompt needs one human click per exe path
- **Why:** the first launch of each `UnrealGame.exe` path shows a firewall prompt. It sits on the secure desktop, so
  ssh and SendKeys cannot dismiss it, and the auto-mode classifier denied a `netsh advfirewall ... add rule` command
  (`mock-jam-findings-10.md:70,74,79,84`). Left up, it spoils the video. One Cancel click stopped it coming back.
- **How to check:** at the first Legion run of a new game name or new engine path, the owner looks at the Legion screen
  and clicks once. Then take a frame. An agent cannot do this step.

## Tip: a hand-written PowerShell capture needs `SetProcessDPIAware()`
- **Why:** without it the Legion screenshot is cropped to the top-left quarter. `legion_capture_screenshot.py` also
  opened a terminal window over the game (`mock-jam-findings-10.md:103`). `scripts/visual_playtest_input.ps1` already calls it.
- **How to check:** a full-screen frame from the Legion should show the whole game, not one corner.

## Tip: never focus the game with a bare Alt; click the window, and hide helper consoles
- **Why:** a single Alt tap opens the AMD Adrenalin overlay and covers frames 01 and 02. The game started windowed
  also showed the taskbar. A Windows Terminal host for a helper task shows in frames and steals focus
  (`mock-jam-findings-11.md:66,141`; `mock-jam-findings-12.md:41,64,105-106,120`). Mock 12 fixed this in patches: focus by
  mouse click, helper tasks under `conhost.exe --headless`.
- **How to check:** read frames 01 and 02. No overlay text, no taskbar, no terminal. If they show up, apply or
  re-write the patch before a gate run.

## Tip: do not kill OBS with `/F`; poll the websocket; keep a desktop fallback
- **Why:** OBS needs 15 to 35 s before port 4455 answers. After `taskkill /F`, OBS shows "Crash Detected" (Safe Mode,
  WebSockets off) and 4455 never opens. `--minimize-to-tray --disable-updater` hung it, and update or crash dialogs sit
  over the game (`mock-jam-findings-10.md:73,75,81-84`; `mock-jam-findings-12.md:59`). Mock 12's first video was a montage,
  not a capture.
- **How to check:** poll 4455 for up to 60 s. If OBS will not open, record on the Linux desktop: run the game under
  `SDL_VIDEODRIVER=x11` and grab the game WINDOW (not the root) with `ffmpeg -f x11grab` (`mock-jam-findings-12.md:62`,
  56 s clip, no taskbar). Or take `agent_playtest_cli clip` takes. Any real 30 to 60 s of 1080p play is enough.

## Tip: measure the loudness of the final clip
- **Why:** mock 12's final clip measured about -25 LUFS against a -23 target (`mock-jam-findings-12.md:80`). It had been
  through a two-pass `loudnorm`, so it needs a re-measure.
- **How to check:** run `loudnorm` in measure mode on the finished file and read the integrated value.

## Tip: every new exe name raises its own firewall prompt; the owner answers it once per exe
- **Why:** mock 16's packaged `PolarityFlip.exe` brought up "allow public and private networks to access this app?" over the centre of every frame. The visual playtest gate failed (5 FAILs), and the agent playtest and video stayed OPEN. Agents must never answer it (Windows setting). A Shipping build may not ask (UNTESTED). Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** before the first Legion playtest of the real entry's exe, the owner answers the prompt once at the Legion console; then confirm a frame without the dialog.

## Tip: make the game the front window before the first shot
- **Why:** in mock 16 the Legion's Claude app was in front for frames 01-14; the game came forward only at the first key step, which failed two steps and the idle burst. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** add a key-free focus step or a longer first wait to the sequence; frame 01 must show the game.

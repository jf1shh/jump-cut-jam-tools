# Plan: 2026 Epic AI MegaJam entry (Unreal Engine 5.9 Preview, 5.8.4 fallback, solo)

The full plan, with reasoning and sources, is in `stages/00_prep/references/win-plan.md`. This file is the short schedule.
Don't build gameplay, levels or art before Wed Nov 11, 9:00 PM PT (Nov 12, 00:00 ET). That breaks
Rule 7(h), and it's more than a guideline.

## Phase 0 — Pre-jam prep (now through Nov 11)

### Week 1 (Oct 27 – Nov 2)

- [x] Decisions: UE 5.8 (moved to 5.9 Preview with 5.8.4 as fallback, 2026-11-10; Legion 5.9 source build at `C:\Dev\UE_5.9` editor built 2026-11-10 21:00, helper tools being rebuilt by hand), solo + Glass Box, Legion Go S as the Windows build box, online, local generation first
- [x] Confirm the Official Rules against Epic's Box link (confirmed 2026-10-27 against the owner's
      uploaded copy of the Official Rules PDF, all 14 pages read directly: Rules 4, 7(h), 9, 10, 11,
      13 and 15(b)/(c)/(d) all match RULES.md verbatim; no discrepancies found)
- [x] Back up the Legion Go S, install Windows 11, install the same exact UE 5.8.x on the Go S and the desktop
      (confirmed 2026-10-28: Legion is on Windows 11 10.0.26300.9711, UE 5.8.4 at `C:\Dev\UE_5.8`,
      matches the desktop's 5.8.4)
- [x] Check itch.io's own edit-after-submit behavior to confirm a submitted entry can be replaced before the deadline (gates the day-3 insurance upload below)
      (confirmed 2026-10-28: itch.io lets you re-upload project files as many times as you want while
      a jam's submission window is open; MegaJam's own Official Rules don't add any restriction on top
      of that. Insurance upload in the Phase 1 schedule is good to go.)
- [x] Desktop: enable the Unreal MCP + AllToolsets plugins, run `ModelContextProtocol.GenerateClientConfig ClaudeCode`.
      Gate: Claude Code lists toolsets and can spawn and edit an actor in a scratch level
      (verified 2026-10-27 over raw MCP HTTP against `~/Projects/ue-mcp-verify`: listed ~50 toolsets,
      spawned a StaticMeshActor, then moved and relabeled it via ActorTools)

### Week 2 (Nov 3 – Nov 9)

- [x] **Nov 4 gate (passed, including the butler push):** packaging script (`RunUAT BuildCookRun`, Development, Win64 → `TeamName_GameName.zip`,
      size check under 1 GB, butler push to a private itch.io page), proven on a throwaway template project, then deleted
      (passed 2026-10-28 on the Legion Go S: cook, stage, and archive all succeeded against a
      de-stubbed `TP_ThirdPersonBP` copy with the GameplayStateTree plugin removed —
      `SilentBlade_Throwaway.zip` produced at ~447 MiB, well under the 1 GB limit. Butler push to
      itch.io passed 2026-11-02: owner ran `butler login` on the Legion and made the private draft
      page `jf1shh/megajam-pretest`; a one-file test folder pushed to channel `win64` as build
      #2280252 (`gate-test-1`) and `butler status` shows it processed. `C:\Users\shino\butler` is on
      the Legion user PATH, so the script's bare `butler` call resolves. Found a gap — Legion had no Windows SDK/MSBuild/VS Build Tools,
      so any project forcing a C++ compile would fail packaging there — resolved 2026-10-28 by
      installing VS 2022 Build Tools (VCTools workload + Windows 10 SDK 10.0.19041.0) via winget.
      Also fixed an em-dash encoding bug in `scripts/package-and-push.ps1` that broke Windows
      PowerShell 5.1 parsing, see PR #16. The `-NoticeFile` step added in PR #41 is now
      live-verified on the Legion Go S too (2026-10-29): fixed a real bug where `$PSScriptRoot`
      comes back empty while PowerShell evaluates a param-block default alongside Mandatory
      parameters, which broke the NOTICE.txt default path; re-ran the full cook/stage/archive
      against `OvergrownMock` and confirmed NOTICE.txt lands at the zip root.)
- [x] Asset pipeline scripts: image model (default `krea-2-turbo`; Qwen-Image 2.1 is non-commercial-only, see `stages/00_prep/references/pre-jam-declaration-2026-10-29.md`) / Modly → foundry-lab remesh and bake → FBX → UE Python import; record minutes per asset
      (proven end-to-end 2026-10-28: ~3 min/asset — 183s total, 100.73s image + 82.29s 3D/game-ready,
      measured on `pipeline_test_crate2`; UE import live-verified against UE 5.8, see
      `_config/reference/engine-reference/unreal/python-scripting.md`. The `NEXUS_FOUNDRY_PYTHON` manual-export
      requirement is resolved: Nexus's own default venv path was stale (pointed at a venv that never
      existed on this machine), fixed upstream 2026-10-28 (nexus PR #270); re-ran the asset pipeline
      with the env var fully unset to confirm — exit 0, real GLB produced.)
- [x] Audio scripts: ACE-Step loopable tracks; pick an SFX source; check every model's license
      (`scripts/gen_music.py` written, thin wrapper over Nexus's `nexus_music.py`; proven end-to-end
      2026-10-28: 30s instrumental loop generated in 112.46s, a real FLAC at
      `work/audio/test_theme.flac` (48 kHz stereo, 1,440,000 samples), after two Nexus-side fixes in
      `~/Projects/nexus` (merged to main): the NAS-offload path-safety bug blocking the ACE-Step model
      install, and a GPU-gate false positive where the music generator's own GPU ownership check
      mistook Nexus's own CPU-only embeddings service for a competing workload. SFX source picked
      2026-10-28: primary is Epic's own MetaSound SFX Generator (Tech Audio Tools Content plugin,
      ships with the 5.8 editor) — it's generated, not sourced, so it scores under Rule 15(c) and
      carries zero external license at all. Fallback if a sound needs more than MetaSound can produce
      in the time left is Kenney.nl's CC0 packs (Interface Sounds, Impact Sounds, etc.) — license
      confirmed directly on kenney.nl as CC0 1.0 (public domain, no attribution required); using the
      fallback still requires the usual sourced-asset ledger entry per Rules 1(d)/15(c) and will not
      itself score. See `_config/reference/knowledge-base.md`'s AI generation tools table.)
- [x] Agent configs: project `CLAUDE.md` and prompt library (GDD one-pager, scoring rubric, slice brief, playtest checklist, dev log template)
      (`CLAUDE.md` adds naming + Blueprint/C++ rule on top of `AGENTS.md`; templates in `_config/reference/templates/`)
- [x] QA harness: load maps, screenshot fixed cameras, log frame time (60 fps at 1080p on the Go S)
      (`scripts/qa_harness.py`, live-verified against UE 5.8 via `~/Projects/ue-mcp-verify` 2026-10-28:
      loads each map, takes a fixed-camera/active-viewport screenshot, measures real frame time via a
      non-blocking Slate tick-callback state machine — see
      `_config/reference/engine-reference/unreal/python-scripting.md`. API-correctness check only; no real megajam
      level exists yet to test the actual 60fps@1080p budget against, per Rule 7(h).)
- [x] OBS: 1920×1080, 60 fps, 60-second replay buffer
      (finished and verified 2026-11-01 in the owner's own Windows profile — the first RDP pass had
      saved its changes under a temporary account that was then deleted: AMD AMF H.264, replay
      buffer 60 s with F9 = Save Replay, desktop audio on, mic muted, Display Capture source. Test
      recording and replay save both came out 1920×1080 at 60.0 fps with 0 dropped frames and real
      audio. Game Capture source gets added in jam week once a build exists. See
      `stages/04_ship/references/capture-setup.md`.)
- [x] Dev log tooling: `scripts/gen_devlog.py` drafts commits + screenshots + notes → dated Markdown
      (verified with a dry run against this repo's own git history; not yet exercised against real
      jam screenshots, since none exist pre-jam per Rule 7(h)) → itch.io devlog post
- [x] **Mock jam (Nov 7–8):** 24 hours, made-up theme, throwaway project, full loop through package and video; then delete it — run early (2026-10-28/29) in `megajam-mock`; findings in `stages/00_prep/output/mock-jam-findings.md`
      Second, deeper mock run (real generated art + audio, scripted playthrough, Win64 package) in
      `megajam-mock` run 2 (2026-10-28/29); findings in `stages/00_prep/output/mock-jam-findings-2.md` — confirms the
      Blueprint-event-graph Python API wall and recommends hand-building core Blueprints pre-jam.
      Mock jams 3–5 (2026-10-29; `stages/00_prep/output/mock-jam-findings-3.md` to `-5.md`) built a real mechanic via
      MCP and had the owner play it on the Legion Go S. Mock jams 6–7 (2026-10-30;
      `stages/00_prep/references/mock-jam-6-tooling-plan.md`, `stages/00_prep/output/mock-jam-findings-7.md`) produced the first
      headless-built real level. Its packaged build renders and plays on the Legion (beacon win
      verified by agent screenshots and the owner), after seven packaging/level bugs were fixed.

### Final days (Nov 10 – 11)

- [x] Re-read the rules; generate the pre-jam declaration list
      (rules re-read 2026-10-29 against the owner's Obsidian Inbox PDF — SHA-256 matches the
      v3 PDF already digested in RULES.md, zero discrepancies; declaration list generated and
      merged in PR #41)
- [ ] Tag `pre-jam-tooling` (create last, after the final pre-jam doc edits; `git tag -l` is empty as of 2026-11-01)
- [x] Block the calendar Nov 11 evening through Nov 15 (done 2026-11-02: JCForever and personal calendars, Wed 9 PM to Sun 5 PM PT)
- [ ] Watch the kickoff, Nov 11, 11 AM PT; pick the concept by 3 PM PT (thinking on paper only)
- [ ] Jam-day start: follow `stages/00_prep/references/jam-day-runbook.md` (`lemonade unload` then `gpu-preflight`; editor launches with
      `-ModelContextProtocolPort=8010`; owner steps: UE EULA update 22, butler login check,
      `HANDOFF_MAX_RESTARTS=300 proj start megajam` at window open)

## Phase 1 — Jam week (Pacific time)

Hour-by-hour schedule, overnight run cards and bail rules: `stages/00_prep/references/jam-execution-plan.md`.

| When | Gate before you stop |
| --- | --- |
| Wed Nov 11, 9 PM – 1 AM | Project created, one-pager committed; you can move and do the core verb in greybox |
| Thu Nov 12 (day 1) | Core loop fun in greybox **with juice already on it** (not deferred to day 2); finale stubbed and built backward from; art direction locked; **Windows build #1 launches** |
| Fri Nov 13 (day 2) | Full run start to end screen in **build #2**, played by the owner (answer 2026-11-11); chapter/level select wired to what exists |
| Sat Nov 14 (day 3) | Art, lighting, audio, UI, juice; **feature freeze 10 PM**; named risk-fork check (bail to the safe fallback if the core mechanic isn't landing); build #3; rough video cut; **insurance upload** to itch.io tonight |
| Sun Nov 15 (day 4) | Fixes only to 12 PM; final build 1 PM replaces the insurance upload; video 2 PM; dev log 3 PM; **uploaded by 4 PM, submitted by 4:30 PM** |

Audio/video notes (see `_config/reference/research/audio_and_music_fast_production.md`):
- [ ] Day 3 audio pass: import with MetaSound (native loop points via the Wave Player node), not legacy
      Sound Cues — the jam is 4-day scope, no need for Sound Cue's extra indirection.
- [ ] Day 4 video (2 PM): run ffmpeg two-pass `loudnorm` (EBU R128, -23 LUFS target) on the mix before
      muxing into the 30–60 s submission video. A -14 LUFS YouTube target is commonly cited but wasn't
      confirmed against an official source — don't assert it as fact if it comes up.

## Phase 2 — Submission checklist

See `stages/00_prep/references/win-plan.md` → Submission checklist. Run it top to bottom from 1 PM on Sunday.

# Decision log

One row per decision, newest at the bottom. Dates are Pacific (the jam's clock). `scripts/gen_devlog.py`
copies every row whose ID no dated entry in `stages/05_devlog/output/` mentions yet into the next nightly draft
("Decisions since the last entry"), so log it here the moment it is made and the dev log catches up.

Format (keep the pipes; one line per decision):

    | D-NNN | YYYY-MM-DD HH:MM | who decided | what | why | link |

- **ID:** next free `D-NNN`. Never reuse or renumber one.
- **Who:** `owner`, `hub`, or the agent/session name. A recommendation the owner has not confirmed says so
  ("hub (recommendation; owner to confirm)"), and a later row records the confirmation.
- **Why:** one clause. **Link:** the doc, PR or commit where the reasoning lives.
- A reversal is a new row that names the old ID ("supersedes D-004"); never edit an old row's decision.

Rows D-001 to D-009 are pre-jam decisions copied from the repo's own docs on 2026-11-11 (facts only; D-009 from the hub's relay of the owner's words; the link
column is the source).

| ID | Date (PT) | Who | Decision | Why | Link |
|---|---|---|---|---|---|
| D-001 | 2026-10-27 | owner | Unreal Engine track, not UEFN | Full control of rendering, audio and code with Epic's Unreal MCP plugin; UEFN is Windows-only and its Verse API hallucinates | `stages/00_prep/references/win-plan.md` (D1), `AGENTS.md` |
| D-002 | 2026-10-27 | owner | Solo entry, aiming at the Glass Box modifier (best dev log) | Only one modifier can be won (Rule 13); Glass Box plays to documenting and verifying everything | `stages/00_prep/references/win-plan.md` (D2) |
| D-003 | 2026-10-27 | owner | Windows build box is the Legion Go S with Windows 11; develop on the CachyOS desktop | Unreal cannot package a Windows build from Linux; keeps the asset tools and editor on one box | `stages/00_prep/references/win-plan.md` (D3 option 1), `AGENTS.md` |
| D-004 | 2026-11-06 | owner | Concept images may also come from GPT (codex bridge) and Grok, through the repo adapters | Pipeline must not stall if one provider is down; AI images are not sourced assets (Rule 15(c)) | `AGENTS.md`, `_config/reference/ai-providers.md` |
| D-005 | 2026-11-07 | owner | Not local-only: any tool, service or asset the Official Rules allow, cloud AI terms-gated | Speed; licences and rules are enforced by the contest guard, not by staying local | `AGENTS.md`, `_config/reference/ai-providers.md` |
| D-006 | 2026-11-10 | owner | UE 5.9 Preview is the default engine, 5.8.4 the fallback; the Legion builds with its 5.9 source build at `C:\Dev\UE_5.9` | The jam runs on UE 5.9 MegaJam Preview; mock 16 packaged a 5.9 build on the Legion and pushed it to itch (build #2354706) | `AGENTS.md` (Engine switch), `stages/00_prep/output/mock-jam-16-findings.md`, `_config/reference/canon/jam-ue59-upgrade.md` |
| D-007 | 2026-11-10 | hub (recommendation; owner to confirm) | Ship the **Development** config for every gate build and the final build | The jam page says "development build"; it is the only path the mocks proved; its costs are small | `stages/00_prep/references/jam-day-runbook.md` (section 5, Development vs Shipping) |
| D-008 | 2026-11-11 | owner | Android build and Pocket Powerhouse dropped; the entry ships the Windows zip only | The spike never ran; a 4 h box costs jam-day prep; the Legion 5.9 install excludes Android | `stages/00_prep/references/android-spike.md` |
| D-009 | 2026-11-11 02:00 | owner | Confirms D-007: the jam build uses the **Development** config, not Shipping ("dev mode it is") | Same reasons as D-007; the owner's call | `stages/00_prep/references/jam-day-runbook.md` (section 5) |
| D-010 | 2026-11-11 13:31 | owner | Concept locked: Jump Cut, built to gdd.md (the 29-item "Final change list for PR #176") | Survived an unanchored red-team review and a like-for-like check (realistic build: Jump Cut 23/35, Cheat the Angle 20, Rolling! 19); owner's words to hub 97: "Yes, lock it" | `stages/01_concept/output/gdd.md`; jf1shh/megajam#176 |
| D-011 | 2026-11-14 19:48 | owner | Ship the **Shipping** build. Owner ruling, verbatim: "shipping build". The submission zip is the Shipping build. Supersedes D-009 (and D-007). Both packages are still cut at every save; the Development twin keeps the log-checked tests and stays the fallback | The owner's call; the jam page accepts Shipping builds on Windows | `superagent-sandbox/.handoff/hub188/reports/build-type-text-edits.md` |

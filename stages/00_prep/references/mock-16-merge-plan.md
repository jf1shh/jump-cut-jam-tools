# Mock 16 findings: merge plan into the canon (written 2026-11-10 21:20 PT)

Mock 16 ("polarity flip", brief `stages/00_prep/references/mock-jam-16-brief.md`, untracked in the main checkout as of 21:20 PT; it should arrive with `mock16-findings`) runs tonight in the main
checkout on branch `mock16-findings` and writes `stages/00_prep/output/mock-jam-16-findings.md` plus a scorecard row.
This plan says where each answer goes once that file lands. It is a plan for the canon-refresh branch
(`claude/canon-refresh-424896`); it never edits `mock16-findings` and never merges either branch (the hub
decides). The findings doc itself arrives through the hub's merge of `mock16-findings`, not through this branch.

## How to fold it in

1. Read the findings from the branch without checking it out:
   `git -C ~/Projects/megajam show mock16-findings:stages/00_prep/output/mock-jam-16-findings.md`.
2. For every gate below, take the verdict (PASS / FAIL / OPEN) and the evidence line, and update the
   target notes. Newest dated evidence wins: rewrite the Tip in place, keep the old claim as one
   `*Superseded (date):* ...` line, never drop it silently.
3. A `tested` note may only hold things we ran. A first live result moves an item from `epic` /
   "fake-tested" wording into the `tested` note named below.
4. Add the CANON.md row for `stages/00_prep/output/mock-jam-16-findings.md` (Mock-jam section, newest first) and update
   `_config/reference/canon/jam-top-lessons.md` if a lesson's evidence or rank changed.
5. `python3 -m unittest discover -s tests -p 'test_*.py'`, commit on the canon-refresh branch, then the
   Nexus re-ingest (step 6) once the GPU is free.
6. Re-ingest only after mock 16 has closed the editor, `gpu-preflight` prints CLEAR and Lemonade is back at
   `--ctx-size 32768`: `scripts/canon_ingest.sh`, then 2-3 `scripts/ask_canon.sh` questions whose answers
   must cite the new mock 16 lines.

## Gate to target map

| Mock 16 gate (brief line) | If PASS | If FAIL / OPEN | Target notes |
|---|---|---|---|
| 5.9 editor on :8010 under the 16G scope, seconds to listen (51) | Record the measured seconds next to the ~195 s figure; note the 16G scope worked | Record the failure line; keep `WAIT_TIMEOUT=300` | `jam-ue59-upgrade` (MCP wait Tip), `jam-mcp-port-and-logs`, runbook section 2 |
| MCP `toolsets` / `describe` / `py` on 5.9 (53) | Second live run: n=2 | Exact error verbatim | `jam-editor-mcp-helper`, `jam-ue59-upgrade` (mx.py Tip) |
| `step_shot` on 5.9 (54) | n=2 | Error and fallback | `jam-editor-mcp-helper`, `stages/02_build/references/step-shot.md` |
| `force_save_level` first live run on 5.9 (56) | Move "unit-tested only on 5.9" to tested; drop that caveat from `AGENTS.md` (mark superseded) | Keep the 5.8 route as the jam rule; write the failure and the fallback | `jam-force-save-level`, `stages/02_build/references/force-save-level.md`, `AGENTS.md` engine-switch bullet, top lessons #4 |
| Greybox loop in 5.9 PIE (58) | n=2 for 5.9 PIE loop | What broke | `jam-session-routine`, `jam-grey-box-first`, `jam-pie-*` |
| Windows package on the Legion with 5.9 (60) | **First 5.9 Win64 package**: close G3 in `stages/00_prep/references/jam-execution-plan.md`; time it (minutes) for the overnight cards; record build config | Engine-fork input for Wed 15:00 (E7 in `stages/04_ship/references/jam-recovery.md`); exact UAT error | `jam-packaging-windows`, `jam-legion-ship-preflight`, `jam-ue59-upgrade` (SDK/toolchain Tip, Legion Tip), `stages/04_ship/references/legion-ship.md`, top lessons #1 |
| Push to pretest + `butler status` (61) | n+1 for the PC-side push | DNS / login cause | `jam-legion-ship-preflight`, `stages/04_ship/references/legion-ship.md` |
| Packaged visual playtest, real OS input (62) | First real-input pass on a 5.9 package | Which checklist item failed and why | `jam-agent-playtest-gate`, `jam-visual-playtest-motion`, `stages/03_playtest/references/playtest-gate.md`, top lessons #2 |
| Idle-stability bursts (65) | n+1 | Looping camera / drift details | `jam-visual-playtest-motion` |
| SPACE key in the packaged Windows build (67) | Mock 15 bug is Linux/XWayland-only: say so in `jam-wayland-no-key-injection` and top lessons; keep `IsInputKeyDown` | Real game bug: the input route needs a fix before day 1 (Enhanced Input action, not key polling); flag to the hub as a jam-day risk | `jam-wayland-no-key-injection`, `jam-agent-playtest-gate`, top lessons #2 |
| Agent playtester win / lose / restart (68) | n+1 | Where the loop got stuck | `jam-agent-playtest-gate`, `stages/03_playtest/references/agent-playtest.md` |
| Legion locked or black console (46) | - | Re-confirms the idle-lock rule; record whether the lock was the cause | `jam-mock11-legion-and-editor-traps`, top lessons #3 |
| Zip name and size (70) | Size vs the 1 GB cap for a 5.9 package | - | `jam-packaging-windows` |
| 30-60 s video (71) | Capture route that worked | Cause | `stages/04_ship/references/capture-setup.md` row, `jam-mock11-legion-and-editor-traps` |
| Within 6 h, editor closed, Lemonade restored (72) | - | Overrun minutes | `jam-hard-stop-clock`, scorecard |
| Scorecard row (73) | Arrives with the findings | Note if rows 14-15 are still missing | `stages/00_prep/references/mock-scorecard.md` |

Anything in the findings outside this table (new traps, tool gaps) goes into the closest topic note,
or a new `_config/reference/canon/jam-<topic>.md` with front matter, plus its CANON.md line.

## Status

- 2026-11-10 21:20 PT: plan written; mock 16 still running.
- 2026-11-11: the hub merges `mock16-findings` to master before this branch (Fable GO); notes now say "merged to master 2026-11-11" instead of "until merged". The lines above about the branch are history.
- 2026-11-10 23:55 PT: folded in from `mock16-findings` head f595a8b: `jam-packaging-windows` (first 5.9 package, 1 h 25 min, `.pdb`/strict 1 GB, content-only exe), `jam-legion-ship-preflight` (GitDependencies excludes, side session not waking), `jam-legion-capture-and-video-traps` (firewall prompt per exe, front window), `jam-wayland-no-key-injection` (SPACE fine on Windows), `jam-force-save-level` (5.9 fixes, live PASS), `jam-pie-pawn-spawn` (DefaultPawn sphere), `jam-session-routine` (substep Tick physics), `jam-ue59-upgrade` (first package, 14.2 s MCP), top lessons 1/2/4/7/11/14, runbook build #1 list, `AGENTS.md`, plan G3, recovery note 4, CANON row. Open in mock 16 itself: visual playtest, agent playtest, video (owner answers the firewall prompt first). Scorecard row lands with the branch.

# 06 Bug and crash triage

**Purpose:** reproduce first, find the cause, make the smallest fix, prove it. Covers a gameplay bug and an editor or
MCP crash.
**When:** a playtest report names a bug, the packaged build misbehaves, or the editor or MCP hangs or dies.
**Lead sends to:** a debugging agent. A gameplay bug that needs only reading and file edits can go to a helper; anything
that needs the editor or MCP stays with the lead.
**Model:** Sonnet; Opus if two fix attempts failed or the bug is in determinism, saving or packaging.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{symptom}` | what was seen, one or two sentences |
| `{evidence}` | frames, clips, log paths from the playtest |
| `{repro}` | steps if known, or "unknown" |
| `{mode}` | `game-bug` or `editor-crash` |
| `{owned_files}` | files the fixer may edit |

## Prompt

```text
{HOUSE_RULES}

Triage: {symptom}. Evidence: {evidence}. Repro: {repro}. Mode: {mode}. You may edit only {owned_files}.

Rules: reproduce before you theorise; one hypothesis at a time; change one thing per attempt; no fix without a proof.

If mode is editor-crash (lead only):
1. Before any restart, copy the project's Saved/Logs and any Saved/Crashes/<timestamp>/ to
   ~/Projects/megajam/stages/04_ship/output/crash-logs/<YYYY-MM-DDTHHMM>/ (a copy, not a commit of build output).
2. Read the log map in AGENTS.md ("Where every recovery-relevant log lives") for the shape you have.
3. Before relaunching: `ss -ltn | grep 8010` must print nothing; wait a few seconds after stopping the old editor.
   Relaunch with scripts/launch-editor.sh (it exits 8 or 9 rather than waiting forever; never wait on :8010 without a
   timeout). Check what was lost: python3 scripts/force_save_level.py must say VERIFIED for the level you expect.
4. Two failed relaunches in a row: stop editor work, keep the logs, continue file-only work, and report.

If mode is game-bug:
1. Reproduce: in the editor (lead) or the packaged build (agent_playtest_cli.py). Capture the failing frame or log line.
   If you cannot reproduce in 3 tries, say so with what you tried; do not "fix" blind.
2. Find the cause: read the smallest set of files that could produce it. State the cause in one sentence and the line.
3. Fix: smallest change. Data bug (wrong number or asset)? change the data asset, not the C++.
4. Prove: run the repro again and take a screenshot you Read; run the determinism test if scene time or stunts were
   touched; check you did not break the other input method.
5. Note the fix in one line for the dev log (what broke, why it was surprising).

Report the cause, the fix, the proof, and anything the same cause could break elsewhere.
```

## Done when

The repro no longer fails and a Read screenshot or log line shows it, or the report says BLOCKED with the three
attempts and the evidence.

## Reply format

House format, plus `Cause:` (one sentence, file:line), `Fix:` (files), `Proof:` (frame or log path), `Risk:` (what else
this touches), `Log line:` (one sentence for the dev log).

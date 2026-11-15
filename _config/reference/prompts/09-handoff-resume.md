# 09 End-of-session handoff and resume

**Purpose:** a session near its context limit writes a short, checkable handoff; the next session resumes from it
without redoing or trusting stale claims.
**When:** the loop writes `.handoff/loop-<pid>/HANDOFF.md` at the context limit on its own; use the writer prompt when
you want one on demand (before an owner break, a model switch, a planned restart). Use the resume prompt for the first
message of every new session. `proj handoff megajam` prints the newest one.
**Hub or lead sends to:** the session that is ending (writer) and the session that starts next (resume).
**Model:** whichever role is being handed off; Haiku can write a handoff from a transcript.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{role}` | lead, helper `A`/`B`/`C`, reviewer |
| `{handoff_path}` | the newest `HANDOFF.md` (path printed by `proj handoff megajam`) |

## Prompt 1: write the handoff (ending session)

```text
{HOUSE_RULES}

Write HANDOFF.md for the next {role} session. Under 60 lines. Facts only, each checkable. Sections:
1. Now: what you were doing and the exact next action.
2. State: branch and full head sha; clean or dirty tree (git status); editor up or down and on which port; background jobs
   running (name, how to watch, how to stop); `jam_clock.py status` line.
3. Done since the last handoff: commits (short sha and subject), builds (label, itch build id), gate items.
4. Open: the numbered fix and cut list, each with file or frame path; blockers; the owner's pending asks.
5. Do not redo: things already tried that failed (with the evidence path); decisions made (who, when).
6. Files you own or were editing, so a new writer does not collide.
Never include keys or secrets. Say what you did NOT verify. Commit it. Reply with the path and the one-line resume
command for the next session.
```

## Prompt 2: resume (starting session)

```text
{HOUSE_RULES}

You are resuming as {role}. Read {handoff_path}, then verify before you act: git status and git log -5, the head sha it
names, `python3 ~/Projects/megajam/scripts/jam_clock.py status`, `ss -ltn | grep 8010` (is an editor up), and whether the
background jobs it lists are still running. Where reality and the handoff disagree, reality wins: say so in one line.
Do not redo anything under "Do not redo". Continue with the "Now" action. Report in the house format, first line
STATUS, plus `Resumed from:` (handoff path and sha).
```

## Done when

Writer: the file exists, is committed, and every claim in it can be checked with one command. Resumer: it has said what
differed from the handoff and has started the next action.

## Reply format

House format, plus the fields named in each prompt.

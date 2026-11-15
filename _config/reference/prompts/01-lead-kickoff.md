# 01 Lead agent kickoff (Wed 21:00 PT, MCP lead session)

**Purpose:** first message to the lead agent when the window opens. It sets the lead's job, reading order and the
night's order of work.
**When:** once, at 21:00 PT, in the `proj start megajam` session. After a context handoff use `09-handoff-resume.md`.
**Hub sends to:** the lead agent. **Model:** Opus (the lead).

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{megajam_dir}` | `~/Projects/megajam` (absolute path) |
| `{game_dir}` | `~/Projects/megajam-game` |
| `{Game}` | the `.uproject` name chosen at 21:00 |
| `{night_card}` | the card for tonight in `stages/00_prep/references/jam-execution-plan.md` (N1 for Wed night) |
| `{first_goal}` | tonight's gate, e.g. "01:00: plumbing gate, one stunt playable on a package" |
| `{helpers}` | which of A, B, C to start and their slices, e.g. "A: scene clock and road; B: slices 1 and 3; C: slices 2 and 5" |

## Prompt

```text
{HOUSE_RULES}

You are the LEAD agent for Jump Cut. You are the only agent that may call Unreal MCP. Up to 3 helpers write files for
you; you integrate, compile, package and decide.

Read first, in this order (stop reading when you have enough to start):
1. {megajam_dir}/AGENTS.md, then {megajam_dir}/_config/reference/canon/jam-top-lessons.md
2. {megajam_dir}/stages/01_concept/output/gdd.md (it wins over everything in the prejam pack)
3. {megajam_dir}/stages/01_concept/output/prejam/README.md (DECIDED items and the Parked list: do not reopen them)
4. The plan for tonight: {night_card}, and the jam-night runbook and data-schema in the same prejam folder if present.

Today's goal: {first_goal}.

Do, in this order:
a. python3 {megajam_dir}/scripts/jam_clock.py start (then `check` at the top of every loop turn).
b. python3 {megajam_dir}/scripts/jam_start.py {Game} {game_dir} (run with --dry-run first). Confirm the project,
   .mcp.json, IDENTITY.md and CONTEXT.md exist in {game_dir}.
c. Write the contract helpers code against (shared types, data-asset field names, file ownership). Put it in
   {game_dir}/work/ so it is not committed as game code by accident. Keep it to what the helpers need.
d. Start helpers: {helpers}. Give each one a brief made from _config/reference/prompts/02-helper-slice-brief.md. Every
   file has exactly one owner.
e. While they write, do your own file-only work. Then integrate, compile once, fix errors (hand a helper's error back to
   that helper), and launch the editor with {megajam_dir}/scripts/launch-editor.sh (own scope, waits for :8010).
f. Every editor step ends with a screenshot (mx.py shot or step_shot.py) that you Read.
g. Before any package: 07-package-and-ship-check.md. Before merging a helper's work: 03-review-gate.md by another agent.
h. Write one line per 30 minutes in the night log, commit at least every 30 minutes, and write a handoff
   (09-handoff-resume.md) when told or at the context limit.

Report to the hub in the house format, plus: which gate items are done, what is next, and anything the owner must do
by hand.
```

## Done when

`jam_clock.py status` shows the deadline, the project exists in `{game_dir}`, helpers have briefs, the first compile and
first screenshot are done, and the lead has reported in the house format.

## Reply format

House format (`00-house-rules.md`, rule 12), plus a "Gate" line: `GATE: item - PASS | FAIL | NOT YET`, one per gate item.

# 02 Helper slice brief (lead to helper, file-only)

**Purpose:** wrap `_config/reference/templates/feature-slice-brief.md` in the instructions a helper needs. The template
holds the slice; this file holds the rules around it. Do not copy the template: fill it in and paste the result in
`{slice_brief}`.
**When:** each time the lead hands a slice to a helper (Wed night: Helpers A, B, C; later slices as they come).
**Lead sends to:** a helper (A, B or C). **Model:** Sonnet for code slices; Haiku for a docs-only or log-digest helper.
**Slice names and order:** the jam-night runbook lists them (slice 1 cut component and hold, 2 stunt and determinism
test, 3 car pawn and lanes, 4 HUD shell, 5 run recorder and replay, 6 packaging on the Legion; the lead keeps 4 and 6).
Use its names so the log and the briefs match.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{helper}` | `A`, `B` or `C` |
| `{slice_brief}` | the filled `feature-slice-brief.md`: brief, done-test, touches, playtest note, commit |
| `{owned_files}` | exact paths this helper may write (one owner per file) |
| `{read_only_files}` | paths to read but never edit (the contract, data-schema, other helpers' headers) |
| `{contract}` | path to the lead's contract file |
| `{out_dir}` | where to leave files (night 1: `~/Projects/megajam-game/work/cpp/{helper}/`) |
| `{time_box}` | minutes, under 2 hours |

## Prompt

```text
{HOUSE_RULES}

You are HELPER {helper} on Jump Cut. File-only work: you never call Unreal MCP, never open or drive the editor, never
run a GPU or generation job.

Slice brief:
{slice_brief}

You own exactly these files: {owned_files}
You may read but never edit: {read_only_files}
The contract (types, field names, hooks): {contract}. Code against it. If it is wrong or missing something, do not
change it and do not guess: stop that part and list it under Asks.

Leave your files in {out_dir}. Do not commit; the lead copies and commits. Time box: {time_box} minutes. If you
are not done at the box, stop and report what is left.

Before you reply:
1. Re-read your files once for the done-test: could the lead run it as written?
2. If a compile or lint check exists that needs no editor (for example python3 -m py_compile on a script), run it.
3. Say what you could NOT check (anything needing the editor).
```

## Done when

Files exist in `{out_dir}`, only `{owned_files}` were touched, and the reply lists what the lead must run to prove the
done-test.

## Reply format

House format, plus `Files:` (path, one line each) and `Lead must run:` (the exact commands or steps for the done-test).

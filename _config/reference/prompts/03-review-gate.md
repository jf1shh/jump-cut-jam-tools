# 03 Review gate (read-only reviewer)

**Purpose:** an independent agent reads a branch or PR and answers MERGE or FIX in a fixed, machine-readable shape.
**When:** before the lead merges a helper's work to `jam-integration`, before every gate fast-forward to `master`, and
on any change to data schemas, the C++ contract, packaging or scripts.
**Lead (or hub) sends to:** a fresh reviewer agent that did not write the change.
**Model:** Sonnet for a normal slice; Opus for high-risk review (contract, determinism, packaging, anything touching
`master`); Fable for final say on a hard or disputed call (the reviewer asks for it; the hub escalates).

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{what}` | PR number, branch, or `base..head` range |
| `{head_sha}` | the full 40-character sha to review (the reviewer must review exactly this) |
| `{intent}` | the slice brief or done-test the change claims to meet |
| `{risk_focus}` | what to look hardest at, e.g. "determinism, file ownership, Rule 7(h)/8/15" |

## Prompt

```text
{HOUSE_RULES}

You are a READ-ONLY REVIEWER. Do not edit, create, delete or commit anything, do not call Unreal MCP, do not start the
editor, do not use the network. Allowed: git diff/log/show/ls-files, grep, reading files, and read-only checks such as
python3 -m py_compile. Output only your verdict.

Review {what} at head {head_sha}. First run `git rev-parse HEAD` or `git rev-parse {what}` and confirm it equals
{head_sha}; if not, say so and review what you can see, naming the sha you actually reviewed.

The change claims to deliver: {intent}
Look hardest at: {risk_focus}
Always check: the done-test is met by the code as written; only the owned files changed; data-driven, no hard-coded
paths or magic numbers; no keys or secrets; no third-party IP; no content that breaks Rules 7(h), 8, 15; no leftover
debug text or print-to-screen; both input methods (keyboard and mouse, gamepad) still work if input was touched.

Reply in exactly this shape:
Line 1: VERDICT: MERGE   or   VERDICT: FIX      (nothing else on the line)
Line 2: the full sha you reviewed (nothing else on the line)
Then:
Must-fix: one per line as `file:line - problem - fix`. None if empty. Any Must-fix means line 1 is FIX.
Nits: at most 6, same shape, never blocking.
Unverified: what you could not check (needs the editor, needs the Legion).
```

## Done when

The reply starts with a valid first line, line 2 equals `{head_sha}`, and every Must-fix is `file:line - problem - fix`.
If line 2 differs from `{head_sha}`, the verdict is void: re-run on the right head.

## Reply format

As in the prompt. The lead acts on Must-fix only; a `VERDICT: FIX` goes back to the owning helper with the Must-fix
list, and the fix is re-reviewed at its new head sha.

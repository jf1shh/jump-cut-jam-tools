# Prompt library (tooling only, Rule 7(h))

Every recurring instruction in the jam, written once as a fill-in prompt, so jam-night messages are fast, consistent and
declared. Prompts hold no game content: fill the `{placeholders}` inside the contest window. Declared in
`stages/01_concept/output/prejam/PREJAM-DECLARATION.md` ("Tooling made before the jam"). Scripts the prompts call are
catalogued in [`../../../scripts/README.md`](../../../scripts/README.md).

**Local AI models are OFF for the whole jam** (owner 2026-11-11): no lemond, nexus-image, nexus-3d, nexus-music, Modly,
ComfyUI or local VLM. Cloud Claude and terms-gated cloud providers only (`_config/reference/ai-providers.md`).

**How to use:** open the file, fill the inputs table, paste the `{HOUSE_RULES}` block from `00-house-rules.md` where the
prompt says, paste the one fenced block, send. Every prompt ends with a reply format so answers can be compared and parsed.

## Models

| Model | Use for |
|---|---|
| Fable | final-say review, hard design calls, a disputed review (the hub escalates; agents ask, per the owner's 2026-11-10 rule). Fable runs at effort `xhigh` (owner 2026-11-11) |
| Opus | the lead agent, high-risk review (contract, determinism, packaging, anything that moves `master`), hard triage |
| Sonnet | code slices, normal review, playtest, triage, asset jobs |
| Haiku | reading, docs, log digests, dev log drafts, morning reports |

## Index

| File | When to use | Who sends it to whom | Suggested model |
|---|---|---|---|
| [`00-house-rules.md`](00-house-rules.md) | pasted at the top of every prompt below | hub or lead, inside every prompt | n/a |
| [`01-lead-kickoff.md`](01-lead-kickoff.md) | 21:00 Wed, window opens; first message to the MCP lead | hub to lead | Opus |
| [`02-helper-slice-brief.md`](02-helper-slice-brief.md) | each time a file-only slice goes to helper A, B or C (wraps `templates/feature-slice-brief.md`) | lead to helper | Sonnet (Haiku for docs-only) |
| [`03-review-gate.md`](03-review-gate.md) | before merging to `jam-integration`, before each gate fast-forward to `master`; `VERDICT: MERGE` or `FIX` | lead or hub to a read-only reviewer | Sonnet; Opus high-risk; Fable final say |
| [`04-cloud-asset-job.md`](04-cloud-asset-job.md) | one asset: concept image to 3D through `gen_asset.py`, cloud providers only, after the grey-box gate | lead to asset helper | Sonnet |
| [`05-agent-playtest-visual-check.md`](05-agent-playtest-visual-check.md) | every package on the Legion; real input and Read screenshots | lead to playtest agent | Sonnet |
| [`06-bug-crash-triage.md`](06-bug-crash-triage.md) | a bug in the build or an editor or MCP crash; reproduce first, editor recovery | lead to debugger | Sonnet; Opus after two failed fixes |
| [`07-package-and-ship-check.md`](07-package-and-ship-check.md) | each package: VERIFIED, `presubmit_gate.py`, `legion_ship.py`, playtest, backup | hub to lead | Opus |
| [`08-dev-log-entry.md`](08-dev-log-entry.md) | nightly, about 15 minutes (wraps `templates/dev-log-entry.md`; Glass Box) | lead to docs helper | Haiku |
| [`09-handoff-resume.md`](09-handoff-resume.md) | end of a session, and first message of the next | hub or lead to the ending or starting session | role's model; Haiku can write it |
| [`10-nightly-hard-stop-and-backup.md`](10-nightly-hard-stop-and-backup.md) | 07:30 to 08:15 each night; the last hour before the deadline | hub to lead | Opus (Haiku for the report) |
| [`greybox/`](greybox/README.md) | before any asset exists: one mechanic per prompt, feel numbers, HTML mock step, settings actor and test room. These are part of the library. | lead to lead or helper | Sonnet |

Related templates (not duplicated here): [`../templates/`](../templates/) (`feature-slice-brief.md`, `dev-log-entry.md`,
`playtest-checklist.md`, `theme-spread-prompt.md`, `scoring-rubric.md`, `gdd-one-pager.md`, `game-project-identity.md`,
`game-project-context.md`).

## Order on a normal night

`01` kickoff, then per slice `02` brief, `03` review, `07` package with `05` playtest, `06` when something breaks,
`08` dev log around midnight, `10` at the hard stop, `09` whenever a session ends. `04` runs between slices once the
grey-box gate is passed.

## Slice names

The prompts use the slice and helper names of the jam-night runbook (`stages/01_concept/output/prejam/jam-night-runbook.md`)
and the field names of `data-schema.md` in the same folder. If they change there, they win over this folder.

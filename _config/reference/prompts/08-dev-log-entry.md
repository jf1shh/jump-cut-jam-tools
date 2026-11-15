# 08 Dev log entry (Glass Box)

**Purpose:** draft the night's itch.io dev log entry from facts in the repo, so the owner edits instead of writing.
The dev log is the Glass Box prize entry (Rule 10); it must be honest about what the AI did and what surprised us.
**When:** every night, about 15 minutes, around 00:00 (the 21:00 night has it in the runbook timeline).
**Lead sends to:** a docs helper. File-only; no Unreal MCP. The owner reviews and posts; an agent never posts.
**Model:** Haiku drafts; Sonnet if the day had many decisions to summarise.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{date}` | `YYYY-MM-DD` of the entry |
| `{since}`, `{until}` | ISO times bounding the day |
| `{notes}` | the lead's night log lines and anything the owner said (a file path) |
| `{build}` | the build number or tag the entry matches |

## Prompt

```text
{HOUSE_RULES}

Draft the dev log entry for {date}. File-only. Template: _config/reference/templates/dev-log-entry.md (what shipped, what's
next, one thing that surprised us, AI disclosure, build/version). Post format: stages/05_devlog/references/itch-devlog-template.md.

1. python3 ~/Projects/megajam/scripts/gen_devlog.py --since {since} --until {until} --notes-file {notes} --dry-run
   gives the first draft from git log, screenshots and notes.
2. python3 ~/Projects/megajam/scripts/evidence_index.py --since {since} --out ~/Projects/megajam/stages/05_devlog/output/evidence.md
   lists the day's screenshots, videos, playtest frames and builds with paths.
3. Every claim needs a commit, a screenshot or a log line behind it. Open each screenshot you embed and make sure it shows
   what the caption says. Do not claim a feature that is not in the build {build}.
4. AI disclosure: from stages/02_build/output/asset-pipeline-log.csv and the sidecars list each model or service that made
   something today (provider and model), and which Claude models did the code and review. Start from
   stages/05_devlog/references/ai-disclosure-draft.md. No keys, no private paths.
5. "One thing that surprised us": use a real surprise from the night log or the bug fixes (06 log lines). If there was
   none, say so and leave the slot for the owner. Do not invent one.
6. Write it to stages/05_devlog/output/{date}.md in plain, direct English, short, with screenshots inline by path. Mark
   anything you are unsure of with [CHECK] for the owner.
```

## Done when

`stages/05_devlog/output/{date}.md` exists, every screenshot path resolves, and every `[CHECK]` is listed in the reply.

## Reply format

House format, plus `Entry:` (path), `[CHECK] items:` (numbered), `Missing:` (what you could not source).

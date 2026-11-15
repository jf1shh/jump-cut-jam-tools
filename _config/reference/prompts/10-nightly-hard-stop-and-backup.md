# 10 Nightly hard stop and backup

**Purpose:** end the night cleanly: nothing new starts after the stop, the work is saved and backed up, and the morning
report is committed. Also covers the last hour before the deadline.
**When:** from 07:30 PT on every night card (01:00 to 08:30 unattended window): 07:30 last job start (the package),
08:00 nothing new starts, 08:15 morning report committed. And on the final day when `jam_clock.py check` returns 10, 11
or 12. The cards are in `stages/00_prep/references/jam-execution-plan.md`; `stages/04_ship/references/jam-clock.md` explains the clock.
**Hub or lead sends to:** the lead. **Model:** Opus for the lead; Haiku writes the morning report from the night log.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{date}` | the morning's date, `YYYY-MM-DD` |
| `{card}` | N1 to N4, from the night card list |
| `{night_log}` | path of tonight's log |

## Prompt

```text
{HOUSE_RULES}

Hard-stop procedure for night card {card}, {date}. Run `python3 ~/Projects/megajam/scripts/jam_clock.py check` first:
10 means stop feature work and package now; 11 means only itch page and text edits; 12 means stop.

07:30: the last job may start (the one allowed package, only after VERIFIED, to the default pretest target; see
07-package-and-ship-check.md). No other new job.
08:00: nothing new starts. Let running jobs finish under a timeout; do not abandon a job unwatched.
Then, in order:
1. Save and verify: scripts/force_save_level.py must say VERIFIED; close the editor if the card says so.
2. Commit everything to jam-integration. Do not fast-forward master (gate builds are daytime, owner awake).
3. Back up: ~/Projects/megajam/scripts/jam_backup.sh check (it prints what would happen), then
   `~/Projects/megajam/scripts/jam_backup.sh gate night-{card}`. (A systemd timer also runs `nightly` at 01:00 on Nov 12-15; this run does not replace it.)
   Exit 3 means the NAS is not mounted, 4 low space, 5 no jam folder, 6 archive failed: report the code, do not retry
   in a loop, never delete anything.
4. Handoff (09-handoff-resume.md prompt 1).
5. Morning report at stages/05_devlog/output/jam-nights/{date}-morning.md on jam-integration, built from {night_log}:
   card goal PASS or FAIL per success item; commits (short sha); GPU or asset jobs run (name, minutes, provider, cost);
   editor state; restarts used; frames to look at (paths); blockers; numbered owner asks, one line each; what was not
   done; risk to today's gate. Commit it by 08:15 and send the hub one line.
No early "done": if the card's goal is met before the stop, work the idle list (fix list, step shots, dev log draft,
credits list) instead of ending the session.
```

## Done when

VERIFIED printed, tree committed, `jam_backup.sh gate` exit 0 (or its failure code reported), handoff written, and the
morning report committed by 08:15.

## Reply format

House format, plus `Stop:` (the time you stopped and why), `Backup:` (exit code and the line it logged), `Report:`
(path and commit sha).

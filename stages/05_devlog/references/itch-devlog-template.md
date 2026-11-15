# itch.io devlog — post templates (DRAFT; the owner posts, an agent never does)

Two templates for the Glass Box modifier (best dev log, Rule 10): one post per night, and one final
"How it was built" post. The dev log link goes into the entry form before 5:59 PM PT on Sun Nov 15
(`stages/00_prep/references/win-plan.md`, submission checklist). Source material is all in the repo:

- the night's entry `stages/05_devlog/output/YYYY-MM-DD.md` (drafted by `scripts/gen_devlog.py`, edited by hand);
- the decision log `stages/05_devlog/output/decisions.md`;
- the evidence index `stages/05_devlog/output/evidence.md` (`python3 scripts/evidence_index.py --out stages/05_devlog/output/evidence.md`);
- the AI-use list `stages/05_devlog/references/ai-disclosure-draft.md`.

Lines with `OWNER-FILL` need the owner's own words. Never post a copy that still has one:
`grep -n OWNER-FILL <the copy>` must print nothing. Rules for every post: English only (Rule 7(i)); teen-safe
(Rule 8); no third-party names, logos or IP except the Unreal Engine logo (Rules 8, 15(d)); never paste keys,
emails, paths under `/home`, or the Legion's user name.

---

## A. Nightly post (one per night: Thu Nov 12, Fri Nov 13, Sat Nov 14; Sun Nov 15 is the final post)

**Title:** `Day N: <one plain phrase about the day>` (OWNER-FILL)

**Cover image:** the best screenshot of the day from the evidence list (attach, do not hotlink a local path).

> **Today in one line:** OWNER-FILL (owner's voice)
>
> **What we built**
> - 2 to 4 bullets, copied from "What shipped today" in `stages/05_devlog/output/YYYY-MM-DD.md`, rewritten for a player,
>   not a programmer. One screenshot or short clip per bullet where it helps.
>
> **Decisions we made**
> - Copied from "Decisions since the last entry" (each `D-NNN` row): what we chose and why, in one line each.
>   A cut is a decision too; say what was cut and why.
>
> **What surprised us**
> OWNER-FILL (owner's voice). The one thing a reader will remember: a bug, a lucky accident, a wrong guess.
>
> **How the AI helped (and where it didn't)**
> One or two lines from the entry's AI disclosure: which tools did what today, and one thing a human had to fix
> or decide. Full list: link the final post or the AI-use section.
>
> **Tomorrow**
> OWNER-FILL (owner's voice): the top one or two goals.
>
> **Build:** `gateN-<day>` / itch build #NNNNNNN (from `stages/05_devlog/output/builds.csv`), commit `abc1234`.

Checklist before posting:
- [ ] The entry `stages/05_devlog/output/YYYY-MM-DD.md` is committed (the repo copy is the record; itch is the mirror).
- [ ] Every image is attached from the evidence list and shows only jam-window work (Rule 7(h)).
- [ ] `grep -n OWNER-FILL` on the post text prints nothing.

---

## B. Final post: "How it was built" (Sun Nov 15, dev log final at 3 PM per `stages/00_prep/references/win-plan.md`)

Outline only. Each section names where its facts come from; write the prose in the owner's voice.

1. **The game in 30 seconds** — pitch, theme, how the theme shows up in the first minute (Rule 7(g)). Embed the
   gameplay video. Source: the GDD/concept doc made in the window. OWNER-FILL
2. **The setup** — solo, four days, UE 5.9 MegaJam Preview, built on a Linux desktop and packaged for Windows on
   a Legion Go S (decisions D-001 to D-008). One diagram: desktop editor + agents → git → Legion package → itch.
   Source: `stages/05_devlog/output/decisions.md`, `AGENTS.md`.
3. **What we prepared before the jam (and what we didn't)** — only tools, scripts, prompts and agent configs
   (Rule 7(h)); mock jams 6 to 16 as practice on throwaway projects. Link the `pre-jam-tooling` tag and
   `stages/00_prep/references/pre-jam-declaration-2026-10-29.md`. Source: `stages/05_devlog/output/2026-11-10.md` (prep catch-up entry).
4. **Day by day** — one short paragraph per day linking that night's post; the gate build of each day with its
   itch build number. Source: `stages/05_devlog/output/2026-11-1*.md`, `stages/05_devlog/output/builds.csv`.
5. **Decisions that shaped the game** — the 3 to 5 most important `D-NNN` rows from the jam, each with what we
   gave up. Source: `stages/05_devlog/output/decisions.md`.
6. **How the AI work was organised** — one lead agent was the only Unreal MCP caller; helpers worked in files;
   one GPU job at a time; every generated asset has a provenance sidecar; licence bans enforced by a guard;
   a playtest gate and a separate judge pass before each build. Source: `AGENTS.md`, `stages/03_playtest/references/playtest-gate.md`,
   `stages/03_playtest/references/judge-pass.md`.
7. **Where AI fell short and a human stepped in** — at least two concrete cases with evidence (screenshots,
   commits). Mock jam 10's unsaved level is the pre-jam example (`stages/00_prep/output/mock-jam-findings-10.md`). OWNER-FILL
8. **Evidence** — link or attach the strongest screenshots, playtest frames and scorecards from
   `stages/05_devlog/output/evidence.md`. Scorecards: say they are our own agent's ratings, not the judges'.
9. **AI-use disclosure** — paste the short version from `stages/05_devlog/references/ai-disclosure-draft.md` (section 6),
   trimmed to what was used.
10. **Credits and sourced assets** — `python3 scripts/sourced_assets.py credits` output, or "none".
11. **What we'd do differently** — OWNER-FILL (owner's voice).

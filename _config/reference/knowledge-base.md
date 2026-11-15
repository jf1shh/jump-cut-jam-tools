# Engineer a MegaJam Win Before Kickoff

**The winning formula for the 2026 Epic AI MegaJam is a small, finished, theme-driven game that scores on all seven criteria. The AI story counts for nothing in the main categories.** The Official Rules v2 score entries on seven criteria worth up to 5 points each (Ambition and Innovation, Use of Contest Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio). The extent of AI use is "context only", and ties are re-scored with Fun Factor counted twice (Official Rules v2, Rule 9, via repo RULES.md digest). Sourced assets such as Fab packs "will not be reviewed or scored", while AI-generated content is *not* a sourced asset (Rule 15(c)). So Jared's own generated art and audio earn points and purchased packs earn none. The contest runs **Wed Nov 11, 9:00 PM PT to Sun Nov 15, 5:59 PM PT** (Rule 4), about 93 hours. Before that, only AI tools, agent configs, MCP settings, prompt libraries and scripts may exist. Every piece of gameplay, level and art must be made inside the window, and Epic may ask for version-control history (Rule 7(h)). Two technical facts shape his setup more than any design choice. Unreal cannot package a Windows build from Linux, because Epic documents cross-compiling only from Windows hosts ([Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)). And UE 5.8.0 had reproducible Vulkan device-lost crashes on the RX 9070 XT under RADV, which users report 5.8.1 seems to fix ([Epic forum](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749)). The most a solo, non-student UE entrant can win is **$7,500 (Best Overall UE 1st) plus one $2,500 modifier**, with Development Continuation Grants of up to $50,000 offered by invitation afterward and not guaranteed (Rules 10, 11). This knowledge base backs up Jared's existing plan (`stages/00_prep/references/win-plan.md`, `PLAN.md`) with sourced reference material, lookup tables, checklists and a list of open questions. It doesn't repeat that plan's schedule or decisions.

> **2026-11-10 update.** UE 5.9 MegaJam Preview is now the default editor and 5.8.4 is the fallback (owner, PRs 148 and 149). Sections below were written for 5.8 and are marked "(5.8-era; 5.9 is now default, see jam-ue59-upgrade)". Read `_config/reference/canon/jam-ue59-upgrade.md` and `_config/reference/canon/jam-top-lessons.md` first. The Legion has a 5.9 source build at `C:\Dev\UE_5.9`; no 5.9 Win64 package has been built yet.

## Read this map first: every fact carries its trust level

The research notes behind this document could not open the itch.io jam page, the English Epic news post or the Box-hosted rules PDF. They relied on Epic forum posts, Epic documentation, a Spanish-language Epic news page and press relays. Jared's repo has something closer to primary: a rules digest with rule numbers, read from a community copy of the 14-page "EN_V2" PDF dated 2026-10-22, SHA-256 `5f50221147e2a6ba54b67e0c63afe132f045455e0ab87d99748754f1935a2296`. It still needs to be confirmed against Epic's [Box link](https://epicgames.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z). The Official Rules prevail over the itch.io page (Rule 1). Where sources disagree, this document ranks them as follows.

| Tag used here | Meaning | Examples |
|---|---|---|
| **Rules v2** | Official Rules v2 via repo `RULES.md` digest (rule numbers included). Highest authority available; still a community copy | Rule 4 contest window, Rule 9 judging, Rule 15(c) sourced assets |
| **Epic-primary** | Page authored by Epic: forum announcement/FAQ, dev docs, Epic news (incl. es-ES localization) | Unreal MCP docs, Linux requirements, MegaJam forum FAQ |
| **Secondary** | Press relay of itch.io or Epic | WindowsForum, Inven Global, EGW.news, TechRadar, PC Gamer |
| **Community/vendor** | Third-party tutorials, GitHub READMEs, vendor guides (possible bias) | Puget Systems, Cinevva, Daniel Vaughan, StraySpark |
| **[V] / [E] / [S]** | Video catalog tags. **[V]** = watch page opened; **[E]** = URL from an official Epic page, video not opened; **[S]** = title/URL from a search result only, content inferred from title | See the must-watch section |
| **(inference)** | The research team's or this report's reasoning, not a sourced fact | Labeled inline |

| If you need… | Go to section |
|---|---|
| Dates, prizes, criteria, and where the notes conflict with the rules | "The Official Rules v2 overrule the press…" |
| Everything that can disqualify you, and what pre-jam work is legal | "Nineteen ways to lose…" |
| CachyOS, the RX 9070 XT, the Windows build, packaging, butler, Git | "Linux develops the game but only Windows can ship it" |
| Unreal MCP, Claude Code, community MCP servers, agent loop | "One agent owns the editor…" |
| AI 3D/2D/audio tools and their licenses, templates, UE features, juice | "Generated assets score, Fab assets do not" |
| Past winners, judge behavior, criterion-by-criterion tactics | "Past winners turned the theme into the mechanic" |
| Video, itch page, Glass Box dev log, disclosures | "Presentation and the dev log are where Glass Box is won" |
| What to watch and read | "Fifteen videos to watch before November 12" |
| Things still unknown | "Open questions to verify, with deadlines" |

## The Official Rules v2 overrule the press on names, money and scoring

The press coverage of this jam is unusually unreliable. The rules changed within a day of the announcement: Epic first said AI use was mandatory, then admitted "Our FAQ originally said you had to use AI for the MegaJam. That's our mistake" ([EGW.news](https://egw.news/gaming/news/37966/epic-games-announces-ai-megajam-then-drops-the-ai--84xEnla5b)). Headlines also mixed up grant ceilings with cash prizes ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)). The Rules v2 digest settles most of these disputes, and Epic's FAQ now answers "Do I have to use AI?" with **"No"** ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)). Epic also said it would update the FAQ and rules, so the digest itself says to re-check the PDF on Nov 10 and on the morning of Nov 15 (repo RULES.md).

### Key dates in Pacific time

US daylight saving time ends Nov 1, 2026, so the jam runs on PST (UTC−8) ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)).

| Event | Pacific time | UTC | Source and verification |
|---|---|---|---|
| In-person (Digital Jungle SF) Eventbrite registration opens | Sun Nov 1, 7:00 AM | 15:00 | Secondary ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)); Jared is not attending (win-plan D4) |
| Kickoff livestream and theme reveal | Wed Nov 11, 11:00 AM | 19:00 | itch page per RULES.md; Secondary ([Inven Global](https://www.invenglobal.com/articles/27578/epic-games-announces-2026-epic-ai-megajam-with-up-to-50000-in-grants)). Epic's forum shows "7:00 PM" with no zone, almost certainly 19:00 UTC (inference); es-ES Epic page says 20:00 CET, which is the same instant ([Epic es-ES](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)). Streams: twitch.tv/unrealengine, youtube.com/unrealengine, X @UnrealEngine ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)) |
| **Contest period opens** | **Wed Nov 11, 9:00 PM** | Nov 12 05:00 | **Rules v2, Rule 4** (Nov 12 12:00 AM ET) |
| Daily livestreams | Each jam day 11:00 AM | 19:00 | itch page per RULES.md; Secondary ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) |
| In-person event, Digital Jungle SF | Sat–Sun Nov 14–15 | — | Epic-primary ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)); online and in-person entries are judged the same way (same source) |
| **Contest period closes (late = disqualified)** | **Sun Nov 15, 5:59 PM** | Nov 16 01:59 | **Rules v2, Rule 4** (8:59 PM ET); late disqualification per itch relay ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) |
| Winners notified | On or about Fri Jan 29, 2027 | — | **Rules v2, Rule 14**; respond within **72 hours** with Epic Account ID and Prize Release |

An unofficial third-party kit post in Epic's forum gives the dates as "Nov 12–16". Every official source says Nov 12–15, so ignore it ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)).

### Prizes Jared can actually win

Each submission can win **one main-category prize and one modifier prize**, and a winner normally takes only one modifier (Rules v2, Rule 10, via RULES.md). The cash total is $65,000. The note-takers checked the arithmetic: 3 main categories × $15,000 + $20,000 of modifiers = $65,000, which confirms the $7,500/$5,000/$2,500 reading ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)).

| Category (Rules v2 name) | Amount | Open to Jared (solo, UE, non-student)? |
|---|---|---|
| Best Overall, Unreal Engine | $7,500 / $5,000 / $2,500 | **Yes: main target** |
| Best Overall, UEFN | $7,500 / $5,000 / $2,500 | No (wrong track; Rule 2 allows one engine) |
| Best Student Project | $7,500 / $5,000 / $2,500 | No (all entrants must be enrolled in higher education) |
| **Glass Box** (best dev log) | $2,500 | **Yes: chosen modifier target** (AGENTS.md). Dev log must be submitted with the entry during the contest period (Rule 10) |
| **Solo Driver** (best game by one person) | $2,500 | **Yes: fallback** |
| **Render Royalty** (visuals in a UE game) | $2,500 | Yes, implicitly, if visuals stand out |
| **Pocket Powerhouse** (mobile) | $2,500 each, one UE and one UEFN | Only with an Android/iOS build |
| Best Team | $5,000 | No (2+ entrants) |
| Walkie-Talkie (LLM-NPC narrative) | $2,500 | No (UEFN only) |
| Development Continuation Grants (UE) | Up to $50,000 / $25,000 / $10,000 | By invitation after the contest; not prizes, not guaranteed (Rule 11, per win-plan) |

**Ceiling for Jared: $10,000 cash plus a possible grant invitation.** Epic describes grants as going to "standout entries" ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)). EGW reports they go to projects a human judge thinks are worth continuing ([EGW.news](https://egw.news/gaming/news/37966/epic-games-announces-ai-megajam-then-drops-the-ai--84xEnla5b)). That favors an entry that reads as the seed of a larger game (inference). Work can continue after the jam, but the jam build is the one that gets judged ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)).

### Seven criteria, five points each, Fun breaks ties

| Criterion (Rules v2 name) | What the evidence says earns it | Cheapest lever in a 4-day solo jam |
|---|---|---|
| Ambition and Innovation | New for 2026 vs the 2023 list (inference that it rewards something beyond a one-room toy) ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/); [Fortnite.com 2023](https://www.fortnite.com/news/the-epic-megajam-is-open-to-uefn-submissions)) | Breadth that agents make affordable, not a fragile tech gimmick (win-plan) |
| Use of Contest Theme | Winners turned the theme into the central mechanic (Fregward's realm switch for "As Above, So Below") ([Fregward](https://honestdan.itch.io/fregward)) | One twist that *is* the theme, visible in the first minute |
| Fun Factor (**counts double in ties**) | Vibe Jam 2025 winner praised for "responsive controls" and physics that "feel right" ([CO/AI](https://getcoai.com/video/the-best-ai-made-videogames-2025-vibe-coding-game-jam/)) | Juice on the core verb from day 2 |
| Gameplay | "Don't worry about graphics if you've got good gameplay … you need a strong core mechanic" ([Rob Miles](https://www.robmiles.com/journal/2015/31/3/meatlyjudged)) | One verb, tuned easy enough to finish |
| Visuals | Several 1st/2nd-place MegaJam games also won a craft modifier (environments, kitbash, stylized) ([Epic 2021](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2021-epic-megajam); [Epic 2022](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2022-epic-megajam)) | One palette, one master material, one post-process look over mixed AI meshes |
| Level Design | Full name per the WindowsForum relay is "Level design and game progression" ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) | Start, escalation, real ending; teach → test → twist (win-plan) |
| Audio | A full seventh of the score; past MegaJams had an "Audio Experience" modifier ([Epic 2022](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2022-epic-megajam)) | Music in every state, SFX on every action, randomized pitch |

Epic has historically used a "robust rubric that dives into the specifics of each criteria", with judges from inside and outside Epic. "Scores have historically not been released" ([Epic forum, 2025 MegaJam update](https://forums.unrealengine.com/t/2025-epic-megajam-mega-stack-o-jam-update/2689696?page=2)). Expect placement only, with no feedback.

### Where the research notes disagree with the Rules v2 digest

Each row below is a real discrepancy. The Rules v2 column wins unless Epic's Box PDF says otherwise.

| Topic | What the notes or press say | Official Rules v2 (via repo RULES.md digest) | Action |
|---|---|---|---|
| Modifier names | es-ES Epic page (as translated in notes): "Solo Development", "Rendering Mastery", "Pocket Power", "Creative Transparency", "Walkitalki" ([Epic es-ES](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)); Inven paraphrase: "Best solo game", "Best visuals", "Best mobile", "Best dev log showing how AI tools were used" ([Inven](https://www.invenglobal.com/articles/27578/epic-games-announces-2026-epic-ai-megajam-with-up-to-50000-in-grants)) | **Solo Driver, Render Royalty, Pocket Powerhouse, Glass Box, Walkie-Talkie** (also matched by [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/) and [EGW](https://egw.news/gaming/news/37966/epic-games-announces-ai-megajam-then-drops-the-ai--84xEnla5b)) | Use the Rules v2 names in the entry form and dev log; the es-ES names look like localization |
| Judging criteria | 1–5 scale; "Theme"; "Level design and game progression"; no weighting or tiebreak found ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) | Up to 5 points each on **Use of Contest Theme** and **Level Design** (plus five others); AI use "context only"; **ties re-scored with Fun Factor double** (Rule 9) | Treat Fun Factor as the most valuable criterion |
| Prize pool | "$50,000 prize pool" ([Shacknews](https://www.shacknews.com/article/151119/epic-games-ai-megajam-contest); TechRadar "$50,000 total" [TechRadar](https://techradar.com/gaming/pc-gaming/vibe-your-way-to-usd50k-epic-is-challenging-devs-to-build-a-game-in-4-days-with-ai-and-gamers-are-in-full-rebellion-now)) | **$65,000 cash**; $50k/$25k/$10k are grant ceilings by invitation (Rules 10, 11) | Ignore $50k-prize headlines |
| Grant basis | "Standout entries" ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)); "up to $50,000 per team" ([WN Hub](https://wnhub.io/news/Generative_AI/item-52480)) | By invitation after the contest, not prizes, not guaranteed (Rule 11 per win-plan) | No change |
| Prize-cap rule number | n/a | RULES.md cites **Rule 10** for the one-main-plus-one-modifier limit; AGENTS.md and win-plan cite **Rule 13** | Check the PDF and fix the citation in the repo |
| Pre-jam work | "Declare any prompts, scripts, or assets you made before the jam" ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)); the fast-build notes suggest a pre-built "theme-agnostic shell kit: title, pause, settings, loading screen" | Only AI tools, agent configs, MCP settings, prompt libraries and scripts may be prepared; **all gameplay, levels and art during the contest period** (Rule 7(h)) | Do **not** pre-build a menu shell or any art. Prepare it as a prompt/spec only |
| Dev log | "Optional, except for Glass Box" ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) | Dev log submitted **with the entry during the contest period** for Glass Box (Rule 10) | Publish the dev log before 5:59 PM PT Sunday |
| Build configuration | Video-catalog inference says "Package a Windows Shipping build on Nov 12" | itch page: "development build" (RULES.md); press relay: "Package a development build… Unpackaged projects are not accepted" ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) | **Development**, not Shipping; don't tick "For Distribution" |
| Platform wording | Jam page: "Windows, macOS, Android, or iOS" | Rule 1(b): "packaged for Windows and playable on Windows 10 or 11, macOS, Android or iOS"; a forum user asked whether macOS-only is acceptable "since the Rules and jam page differ"; no Epic reply ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)) | Ship Windows; treat Android-only as unsafe |
| Sourced-asset scoring | 2023: sourced assets not scored, but their *implementation* (e.g., spatialized or modulated sourced audio) could earn points ([Fortnite.com 2023](https://www.fortnite.com/news/the-epic-megajam-is-open-to-uefn-submissions)) | Sourced assets "will not be reviewed or scored"; AI-generated content is not a sourced asset (Rule 15(c)) | Assume no credit for sourced assets at all; generate your own |
| Theme timing | Kickoff Nov 11, 11 AM PT | Rule 1: theme "announced at the start, on Epic's Unreal Engine livestream and X account" | Assume the 11 AM PT reveal; on-paper ideation before 9 PM is the plan (open question below) |

## Nineteen ways to lose before a judge scores you

Most jam entries fail on compliance and packaging, not on design. The Bit Barrage and JungleFall postmortems both trace their regrets to scope creep and late UX work, and Epic's own tips repeat "small scope, polish, test build on day two" ([Bit Barrage](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem); [JungleFall](https://tree-industries.itch.io/junglefall/devlog/203808/post-megajam-thoughts); [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)). The table separates outright disqualification (DQ) from lost eligibility or lost points. Win-plan's Submission checklist covers the Sunday run-through. This table adds sources and severity.

| # | Risk | Rule / source | Severity | Prevention |
|---|---|---|---|---|
| 1 | Any gameplay, level or art made before Wed Nov 11, 9:00 PM PT (AI-generated included) | Rule 7(h) | **DQ** | Repo holds tooling only; tag `pre-jam-tooling`; mock-jam projects deleted (win-plan) |
| 2 | Undeclared pre-jam prompts, scripts, configs | Rule 7(h); [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983) | **DQ risk** if questioned | Declaration list generated from git on Nov 10–11 |
| 3 | Submission after 5:59 PM PT Sun Nov 15 | Rule 4; itch relay ([WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/)) | **DQ** | Uploaded by 4 PM, submitted by 4:30 PM (PLAN.md) |
| 4 | Ineligible entrant: under 18, Cabined Account, Restricted Jurisdiction | Rules 1, 5 | **DQ** | Washington residency qualifies (win-plan) |
| 5 | More than one submission, or UE and UEFN both | Rule 2; 2023 precedent rejected *all* of a team's entries ([Fortnite.com 2023](https://www.fortnite.com/news/the-epic-megajam-is-open-to-uefn-submissions)) | **DQ** | One itch project, one submission |
| 6 | Unpackaged project, or not packaged for an allowed platform | Rule 1(b); [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/) | **DQ** | Win64 Development build each day |
| 7 | Game needs extra software (local LLM server, API key, runtime installs) | Rule 7(f) | **DQ** | Clean-machine test; Prerequisites Installer on |
| 8 | Obvious extension of an Epic tutorial, or gameplay that doesn't go beyond the starter templates | Rule 7(d), 7(e); 2023 precedent ([itch 2023](https://itch.io/jam/2023-epic-megajam)) | **DQ** | Template for scaffolding only; own core mechanic |
| 9 | No demonstrable use of the Contest Theme | Rule 7(g) | **DQ** + lost points | Theme on the title screen and in the first minute (win-plan) |
| 10 | Non-English in-game text, audio, video or entry info | Rule 7(i) | **DQ** | Agent prompt rule: English only |
| 11 | Missing or wrong video: not 30–60 s, below 1920×1080, not recorded gameplay | Rules 1(e), 7(c) | **DQ** | OBS 1080p60 replay buffer (PLAN.md) |
| 12 | Missing full name/email, or no named Team Owner | Rule 1(c) | **DQ** | Form fields prepared Nov 10 |
| 13 | Sourced assets unlicensed or unlisted | Rules 1(d), 15(c) | **DQ** | Running asset ledger |
| 14 | Third-party IP or any trademark other than the Unreal Engine logo | Rules 8, 15(d) | **DQ** | Nothing from UC2/UT2004/uc2-pc/UTLegacy (AGENTS.md); no real-brand parody |
| 15 | Content above Teen (13+), hateful, obscene or disparaging | Rule 8 | **DQ** | Generator prompt guardrails; human review of every asset |
| 16 | An agent or automated means submits the entry | Rule 17 | **DQ** | Jared clicks Submit and screenshots the confirmation |
| 17 | Zip over 1 GB without butler, or not named `TeamName_GameName` | itch page per RULES.md; 2023 precedent ([itch 2023](https://itch.io/jam/2023-epic-megajam)) | Likely DQ or unplayable | Size check in the packaging script |
| 18 | Dev log not submitted with the entry during the contest period | Rule 10 | Loses Glass Box | Publish nightly; link in form |
| 19 | No reply within 72 hours of winner notification (~Jan 29, 2027) | Rule 14 | Loses prize | Calendar reminder for late January |

Two lost-points traps sit just outside the table. First, leftover debug text: the fast-build notes report that Development builds show `Print String` messages on screen by default. That claim is common jam-review consensus, not a sourced fact, and the `DisableAllScreenMessages` command for hiding them was not re-verified, so remove the Print String calls themselves. Second, a broken first launch. Rob Miles judged one jam where some entries "plain didn't work" ([Rob Miles](https://www.robmiles.com/journal/2015/31/3/meatlyjudged)). An older MegaJam tip also says "All art assets… must have a material other than DefaultMaterial" ([Unreal Source](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/)).

### What Rule 7(h) lets you build now

| Category | Status before 9:00 PM PT Nov 11 | Notes |
|---|---|---|
| AI tools, models, local generators installed and tested | **Allowed** | Rule 7(h) |
| Agent configs (`CLAUDE.md`, Claude Code plugins, subagent definitions) | **Allowed**, declare | Rule 7(h); Sponsor may request them or their VCS history |
| MCP settings (`.mcp.json`, plugin enablement, custom Python toolsets) | **Allowed**, declare | Custom MCP tools are scripts; keep them game-agnostic |
| Prompt libraries (GDD one-pager, rubric, slice brief, dev log template) | **Allowed**, declare | Win-plan prep list |
| Scripts (packaging, import, QA harness, dev log generator) | **Allowed**, declare | Win-plan Nov 4 gate |
| Engine install, Windows box, OBS profile, itch page and butler channel | **Allowed** | Setup, not content |
| Throwaway rehearsal projects (mock jam) | **Allowed only if deleted**; nothing carried over | Win-plan; keep only tooling fixes |
| Claiming Fab freebies | **Allowed** as sourced assets if licensed and listed, but **unscored** | Rule 15(c) |
| Menu/UI shell, HUD, loading screen as built assets | **Not safe** | The notes proposed it; Rule 7(h) says gameplay and art come during the contest. Write the spec as a prompt instead |
| Generated art, meshes, music, SFX intended for the game | **Forbidden** | Rule 7(h): art during contest period |
| Generic gameplay code (hit-stop component, camera helpers) | **Gray, so treat as forbidden** | Not clearly "scripts"; see open questions |
| Anything from UC2, UT2004, uc2-pc, UTLegacy | **Forbidden** | Third-party IP (Rule 8) and pre-jam content (AGENTS.md) |

## Linux develops the game but only Windows can ship it

Jared's main box (CachyOS, RX 9070 XT) can run the UE 5.8 editor (5.8-era; 5.9 is now default, see jam-ue59-upgrade), Unreal MCP and the local generators together. It cannot produce the deliverable. Epic's Linux requirements page discusses only Linux as a target and says cross-compiling is supported only from Windows hosts ([Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)). A 2016 forum answer says the reverse "is not available", and a 2018 follow-up went unanswered ([Epic forum](https://forums.unrealengine.com/t/how-to-build-for-windows-developing-on-linux/349719)). The only workarounds on record are one user running the Windows engine under Bottles/Proton from Jenkins, Windows containers without a GPU toolkit, and an unanswered question about GPU-passthrough VMs ([Epic forum](https://forums.unrealengine.com/t/building-for-windows-on-linux/358294)). None of those is a jam-safe path.

### CachyOS and RX 9070 XT editor facts

| Item | Fact | Source |
|---|---|---|
| Supported distros | Ubuntu 22.04 (recommended) or Rocky Linux 8 for development; CachyOS is not listed | [Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine) |
| Kernel / glibc | ≥ 4.18 / ≥ 2.28; upgrade to glibc 2.35+ if startup is slow | Same |
| Compiler | clang 20.1.8, cross-compile toolchain v26 for 5.7–5.8 | Same; [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |
| AMD Vulkan driver | RADV ≥ 24.2.8; **25.0.0+ recommended** | [Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine) |
| Lumen, MegaLights | Need SM6 and AMD RX 6000+ (the 9070 XT qualifies) | Same |
| Nanite, VSM | Need `VK_KHR_shader_atomic_int64` and SM6 | Same |
| RAM / GPU baseline | 32 GB RAM; GeForce 2080-class with 8 GB+ | Same |
| IDE | VS Code or Rider recommended | Same |
| MetaHuman Animator body animation | Windows-only | [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |
| **Known RX 9070 XT crash** | UE 5.8 on Fedora 44, RX 9070 XT (GFX1201), Mesa 26.0.8 RADV: `VK_ERROR_DEVICE_LOST` from `vkQueueSubmit`, GPUVM read faults, ring resets, breadcrumbs in Lumen/Nanite/VSM/GDF paths; disabling systems "moved the crash" | [Epic forum](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749) |
| Fix status | Jul 31, 2026 reply: "Seems to be fixed with the new 5.8.1 patch" (needs more testing). RX 9060 XT user stabilized with `r.Vulkan.AllowAsyncCompute=0` and `r.RDG.AsyncCompute=0`. A Linux Mint user reports 5.7.4 works where 5.8.0 froze. `-NoRaytracing` was suggested without a result. Epic issue UE-386320 closed as duplicate | Same |
| Other open Linux threads | "Crash when opening or packaging a project on 5.8.1 Linux (RHEL8)" (not opened) | [Epic forum](https://forums.unrealengine.com/t/crash-when-opening-or-packaging-a-project-on-5-8-1-linux-rhel8/2746210) |

**Pin 5.8.1 or later, never 5.8.0, and keep the async-compute CVars ready.** (5.8-era; 5.9 is now default, see jam-ue59-upgrade) Put them in `DefaultEngine.ini` or ConsoleVariables (inference from the notes). The same exact 5.8.x must be on both machines (AGENTS.md); *Superseded (2026-11-10):* the same exact engine version (5.9 Preview default) must be on both machines. One caveat on a fallback: Epic's Unreal MCP plugin is 5.8-only, so dropping to 5.7.4 means losing it, though community servers EngineWire and GenOrca support 5.6/5.7 ([ChiR24](https://github.com/ChiR24/Unreal_mcp); [GenOrca](https://github.com/GenOrca/unreal-mcp)).

### Choosing the Windows build path

Win-plan's Decision 3 already chose the **Legion Go S with Windows 11** as the packaging box. The notes ranked the options a little differently, and the trade-offs are worth keeping in view in case the Go S gate slips.

| Option | Notes' view | Trade-off for Jared |
|---|---|---|
| Separate Windows device (win-plan choice: Legion Go S) | Ranked "(a)" in the agent notes: "a separate Windows PC or dual-boot… packaging from the same git repo" | Keeps editor + generators on CachyOS; cooks slower on a handheld chip; doubles as a low-end test device (win-plan). UE 5.8's Lumen Medium is "targeted at low end PC and handhelds" ([Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)) |
| Dual-boot Windows on the desktop | Ranked first in the fast-build notes: full RX 9070 XT, native D3D12 shader compile (inference) | Generators unavailable while booted into Windows (win-plan) |
| Windows VM on CachyOS | Cooking needs CPU/RAM more than GPU, so a VM without passthrough may still cook (inference, **not verified**) | Poor editor/runtime testing without GPU |
| Friend's PC / rented cloud GPU box | Workable, but moving a ~50+ GB engine install is slow (inference) | Off-site dependency in jam week |
| GitHub-hosted Windows runners | **Not viable**: 14 GB SSD on standard runners ([GitHub docs](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)) | — |
| Wine/Proton editor | Single anecdotal report; "a failure mode" in a 4-day jam (inference) | Avoid |
| Android APK from Linux | Supported setup scripts exist (`Engine/Extras/Android/SetupAndroid.sh`) ([Epic Android SDK doc](https://dev.epicgames.com/documentation/unreal-engine/manual-android-sdk-setup-with-android-studio-for-unreal-engine)); not verified for 5.8 in the notes | Rule 1(b) wording makes Android-only risky; useful only as an extra channel for Pocket Powerhouse |

Shader DDC is per platform, so expect a long first D3D12 shader compile on Windows. Warm it before the jam by packaging a template once (inference from the fast-build notes). Win-plan's Nov 4 packaging gate does exactly this.

### Toolchain versions for UE 5.8 (5.8-era; 5.9 is now default, see jam-ue59-upgrade)

| Platform | Requirement | Source |
|---|---|---|
| Windows | Visual Studio 2026 recommended (minimum **VS 2022 v17.14**); MSVC 14.50 recommended (min 14.38); Windows SDK 10.0.26100.0 default (min 10.0.22621.0) | [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |
| Android | Android Studio Koala 2024.1.2 Patch 1; NDK r27c; SDK 35 recommended, min SDK 34 to compile UE, default target 34, min install 26; build-tools 35.0.1; OpenJDK 21.0.3; Gradle 8.7 with AGP 8.5.2 | Same; [Epic Android requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/android-development-requirements-for-unreal-engine) |
| macOS / iOS | Xcode 26.1.1 recommended (min 26.0); macOS Sequoia 15 recommended (min Sonoma 14.5); needs a Mac | [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |

### Packaging recipe for a sub-1 GB Development build

A blank UE5 project builds to roughly **300 MB** ([Epic forum tutorial](https://forums.unrealengine.com/t/1950640)). A 2021 MegaJam solo C++ entry shipped as a **61 MB zip** (101 MB with prerequisites) ([Bit Barrage](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)). The 2022 winner Fregward shipped at 72 MB after its developer trimmed plugins ([Fregward](https://honestdan.itch.io/fregward)). The 1 GB cap is generous if 8K Megascans, MetaHumans and Nanite-heavy kits stay out.

| Project Settings > Packaging | Set to | Why / source |
|---|---|---|
| Build Configuration | **Development** | "Development build" per itch page (RULES.md) |
| For Distribution | **Off** | "If enabled, a distribution build will be created using the shipping configuration" ([Epic Packaging settings](https://dev.epicgames.com/documentation/en-us/unreal-engine/project-section-of-the-unreal-engine-project-settings)) |
| Use Pak File / Use Io Store | On | Same |
| Create Compressed Cooked Packages | On; Oodle Kraken (balance) or Leviathan (smallest) | Same; the encoder effort level "makes packages smaller but takes more time" |
| Exclude Editor Content When Cooking | On | Same |
| List of Maps to Include | Title + game maps explicitly | Same; prevents missing-map cooks |
| Directories to Never Cook | Unused template/variant folders, test maps | Same |
| Include Prerequisites Installer | On (~40 MB, prevents "VCRUNTIME missing"; size is inference) | Same |
| Include Crash Reporter | Optional; on by default for BP projects | Same |
| Maps & Modes > Game Default Map | The title map | Failure-mode table in the fast-build notes |

Beyond the settings, disable unused plugins and cap texture Max In-Game Size (e.g., 2048), then run Size Map / Asset Audit. These steps are inference from the notes. UE 5.8 also enables "Zenserver as Cooked Output Store" by default and makes Incremental Cooking Beta ([5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)). Epic's only official RunUAT example is `RunUAT.bat BuildCookRun -project=MyProject.uproject -clientconfig=Development`. A Project Launcher custom profile logs the full command line, so **copy the exact flags from your own Launcher log** rather than trusting community flag lists ([Epic Build Operations](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine)).

### First-run and judge-hardware safety

Assume some judges have GPUs below the RTX 2000 / RX 6000 class that Lumen and MegaLights require ([Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)). In UE 5.8, Lumen Medium ("Lumen Lite") is enabled with `sg.globalilluminationquality 1` and `sg.reflectionquality 1`. It is "targeted at low end PC and handhelds", and Dynamic Resolution now works on DX12 and Vulkan ([Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)). Lumen Lite is "twice as fast as Lumen high quality" ([5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)). Default to Medium and expose Low–Epic, resolution scale and VSync (inference). `r.MegaLights.Supported` off "removes all MegaLights shader compilation overhead if your project doesn't use it". Disabling distance fields also strips their shader permutations, and `r.Material.StripUnusedDefaultTextures` avoids loading unused default textures ([Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)).

Shader stutter on first launch is the hitch judges notice. `r.PSOPrecaching` defaults on, but global shaders, Nanite, hair and ray-tracing geometry are only partly covered. Epic recommends a loading screen that waits until `FShaderPipelineCache::NumPrecompilesRemaining()` reaches 0, testing first-run behavior with `-clearPSODriverCache`, and reading `stat PSOPrecache` ([Epic PSO Precaching](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine); [Tom Looman bundled PSOs](https://tomlooman.com/psocaching-unreal-engine)).

### butler and itch upload

| Command / fact | Detail | Source |
|---|---|---|
| Push | `butler push <dir> user/game:channel` (kebab-case channels) | [itch butler docs](https://itch.io/docs/butler/pushing.html) |
| Platform tags | Channel names `win`/`windows`, `linux`, `mac`/`osx`, `android` | Same |
| Versioning | `--userversion 1.1.0` or `--userversion-file` | Same |
| Zips | A directory holding a single .zip is auto-unzipped; disable with `--no-auto-unzip` | Same |
| Exclusions / preview | `--ignore '*.pdb'`; `--dry-run` | Same |
| Limit | Rejects builds over 30 GB uncompressed | Same |
| Jam flow | Upload to your own itch project, then submit to the jam | [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/) |

Strip `.pdb` files from the upload but keep them locally for crash diagnosis. Confirm that judges can download a `TeamName_GameName.zip` under 1 GB from the page (inference).

### Version control for a binary-heavy project

Use Git with LFS for `*.uasset`/`*.umap`, exclude regenerable caches such as DerivedDataCache, and **avoid Unreal's built-in Git plugin**, which "lacks LFS and file locking support and has never left beta" ([Anchorpoint](https://docs.anchorpoint.app/docs/version-control/first-steps/unreal)). Turn on One File Per Actor ("Use External Actors" in World Settings, the default under World Partition). Plan folder names early, because Unreal identifies assets by path and renames leave redirectors (same source). A community `.gitignore` is at [MOZGIII/ue5-gitignore](https://GitHub.com/MOZGIII/ue5-gitignore). GitHub's free LFS quota was not verified and Fab packs can blow it, so the NAS-hosted remote in win-plan's diagram is the safer default (inference). Never commit packaged builds.

### Linux and packaging pre-jam checklist

- [ ] UE **5.8.1+** (same exact hotfix) on CachyOS and the Windows box; confirm RADV is 25.0+ (5.8-era; 5.9 is now default, see jam-ue59-upgrade)
- [ ] Async-compute CVar fallback (`r.Vulkan.AllowAsyncCompute=0`, `r.RDG.AsyncCompute=0`) tested once on a scratch project
- [ ] Windows box: VS 2022 ≥ 17.14 (or VS 2026), MSVC ≥ 14.38, Windows SDK ≥ 10.0.22621.0
- [ ] Nov 4 gate (PLAN.md): template packaged as Development Win64, zip named, under 1 GB, pushed with butler to a private page, launched on a clean Windows install. This also warms the D3D12 DDC
- [ ] RunUAT command copied from a Project Launcher log into the packaging script
- [ ] PSO wait-screen pattern and `-clearPSODriverCache` test written into the QA harness *as a script/prompt* (the screen itself is built in-jam)
- [ ] `.gitignore`, `.gitattributes` (LFS), One File Per Actor note in the project `CLAUDE.md`
- [x] Decide whether an Android channel is worth it. It only matters for Pocket Powerhouse, which competes with Glass Box for the single modifier. **Decided 2026-11-11 (owner): no Android build this jam** (see `stages/00_prep/references/android-spike.md`).

## One agent owns the editor while the rest work in files

Epic tells entrants to "connect your agents to the editor with Unreal MCP" and to set up tools, agents and MCP before kickoff ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)). The official plugin is real and capable. It is also **Experimental**, it runs every tool call serially on the game thread, and in independent testing it is slow. Puget Systems found that UE 5.8 MCP plus Claude built a greybox hallway with rooms in about 5 minutes and a light-trigger Blueprint. It broke input when switching to ground character controls, and when asked to build PCG graphs from scratch it faked the result with placed meshes. Responses often took **5–15 minutes**, with heavy token use. The conclusion: MCP "works best for accelerating systems you already understand" ([Puget Systems](https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/)). That evidence supports win-plan's architecture: one lead agent is the only MCP caller, and the workers write C++, Python and assets as files.

### Official Unreal MCP setup reference (UE 5.9 updates first, then the 5.8-era rows; 5.9 is the jam engine, see jam-ue59-upgrade)

All rows come from Epic's doc "Unreal MCP in Unreal Editor" unless noted ([Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)).

**UE 5.9 updates** from Epic's doc "Unreal MCP in Unreal Editor" (re-read 2026-11-11; supersedes the 5.8 rows below where they differ):

| Task | Command / setting (5.9 page) |
|---|---|
| Auto start | **On by default** (Edit > Editor Preferences > Agentic Workflows > Model Context Protocol > Auto Start Server). Jam rule unchanged: keep it off and start with `-ModelContextProtocolStartServer` (the 5.9 page says commandlets, so cooks, never auto-start the server; the 5.8 cook port clash t/2735398 should be gone, and the flag keeps the start explicit and the port pinned) |
| Tool Search | Default on; `tools/list` returns **four** meta-tools: `list_toolsets`, `describe_toolsets` (plural, `include_schemas: true` for schemas), `describe_tools` (`Toolset.Tool` names), `call_tool`. `describe_toolset` (singular) is no longer listed (our inference: replaced by the two above). Off lists every tool as `<Toolset>.<Tool>` |
| Toolset names | C++ `<Plugin>.<Class>` without the U (`GASToolsets.AttributeSetToolset`); Python by module path. Editor subsystems and Blueprint function libraries can implement `IToolsetProvider`, so their tagged functions become tools with no wrapper (LevelSequenceEditorSubsystem, PCGEditorSubsystem, WidgetBlueprintEditorSubsystem) |
| Capabilities | Spawn and edit actors, Blueprints and Widget Blueprints, materials, MetaSounds, PCG, Niagara, Sequencer, Slate inspection, profiling, automation tests. Replaces the 5.8 "no Blueprint toolset" note |
| Config file location | `GenerateClientConfig`: installed builds write `.mcp.json` to the project root; **source builds write to the engine root** (copy the entry into the project). JSON clients merge; Codex TOML is write-once |
| Instructions | Editor Preferences (you only) or Project Settings (everyone, `DefaultGame.ini`); clients must reconnect |
| Terminal plugin | Startup Commands in order: `export TERM=xterm-256color`, `cd "<folder with .mcp.json>"`, `claude`. The panel starts in `FPaths::RootDir()` (engine install folder in installed builds, workspace root in source builds), so the `cd` matters |
| Agent can't see server | Launch the agent from the config folder, after the editor and server are up; reconnect |
| Python tools | Derive `unreal.ToolsetDefinition`, `@toolset_registry.tool_call` + `@staticmethod`, register in `init_unreal.py`. The page defers the full example to "Using Python with AI Agents"; the "Using Python with AI Agents" page (re-read 2026-11-11) confirms `@unreal.uclass()` on the class, plus `Registration([...])` in the package `__init__.py` and `register()` in `init_unreal.py`; details in `engine-reference/unreal/ue59-linked-pages.md` section 13 |
| Instance targeting | `UsesInstanceDispatch()` (one target object) or `UsesInstanceArgument()` (reserved `instance` arg; used by `EditorToolset.ObjectToolset`, `MaterialInstanceToolset`) |
| Modules | `ModelContextProtocol` and `ModelContextProtocolEngine` (runtime: server, settings, console commands), `ModelContextProtocolEditor` (editor-only auto-start hook) |
| Resources | Supported (`IModelContextProtocolResourceProvider`, `AddResourceProvider()`); the engine ships none. Prompts unsupported |
| Cooked builds | Direct `AddTool()` tools list in full regardless of Tool Search. `Cannot register Toolset ... no entry in baked manifest` (LogToolsetRegistry) means no `AIRuntimeCallable` tools |
| Skills | Key `/Skills/<PluginName>/<folder>` or `/Skills/Project/<folder>`, read with `AgentSkillToolset.GetSkills`; relative links in SKILL.md become absolute paths |

**More 5.9 details** (same page, re-read 2026-11-11):
- Codex client config: `ModelContextProtocol.GenerateClientConfig Codex` writes `.codex/config.toml` with a `[mcp_servers.unreal-mcp]` table; if the file exists it only logs an error, so edit that table by hand.
- Python toolset names are qualified by module path: `geometry_toolset.geometry_ops.GeometryTools`. C++ ones are `<Plugin>.<Class>` without the U (`GASToolsets.AttributeSetToolset`); with Tool Search off, tools list as `<Toolset>.<Tool>`.
- Origin allow-list (`AdditionalAllowedOrigins`) exists to stop DNS rebinding from web pages; each added origin widens that exposure. There is no authentication, so any local process or any page from an allowed origin can call editor tools.
- C++ toolset class: derive from `UToolsetDefinition`, declare `UCLASS(BlueprintType, Hidden)`, expose `UFUNCTION(meta = (AICallable))`; doc comments become the schema.
- Register a C++ toolset class at module startup with `UToolsetRegistry::RegisterToolsetClass()` (example: `UAttributeSetToolset` in the experimental `GASToolsets` plugin, off by default).
- A tool added directly with `IModelContextProtocolModule::AddTool()` is removed with `RemoveTool()` when its lifetime ends; its interface methods run on the game thread.
- Extra skill search folders for C++: `AddSearchRoot`, on top of `<Plugin>/Skills/`, `<Project>/Skills/`, `Engine/Extras/AgentTools/Skills/`.
- Long calls: send `progressToken` in `_meta` to get `notifications/progress` heartbeats (at most one per `ModelContextProtocol.ProgressIntervalSeconds`, default 1.0); `notifications/cancelled` cancels.
- Loopback only by default: the listener binds `[HTTPServer.Listeners] DefaultBindAddress` (127.0.0.1); setting it to `any` exposes MCP to the network, with no auth.

**Stale for 5.9** (use the 5.9 table above): Auto start (now on by default, under Agentic Workflows), Claude Code config location (source builds write to the engine root), Tool Search (four meta-tools; `describe_toolset` is now `describe_toolsets` + `describe_tools`), Shipped toolsets (5.9 has Blueprint and Widget Blueprint tools), Limits (Resources are supported, the engine ships no providers).

5.8-era rows:

| Task | Command / setting |
|---|---|
| Enable | Edit > Plugins > **Unreal MCP** (`ModelContextProtocol`) and **All Toolsets**, restart. **Toolset Registry** auto-enables; optional **Terminal** plugin runs an agent inside the editor |
| Start server | Console `ModelContextProtocol.StartServer` (or `… 8000`); command line `-ModelContextProtocolStartServer`; port `-ModelContextProtocolPort=N`; stop with `ModelContextProtocol.StopServer` |
| Auto start | Off by default: Edit > Editor Preferences > General > Model Context Protocol > Auto Start Server. **Keep it off** and start from the launch line: with it on, cooks also try to bind the port and can exit 1 (t/2735398; runbook step 2) |
| Claude Code config | `ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json` to the project root: `{"mcpServers":{"unreal-mcp":{"type":"http","url":"http://127.0.0.1:8000/mcp"}}}`. Other targets: `Cursor`, `VSCode`, `Gemini`, `Codex`, `All`. Launch the agent from the project root |
| Transport | HTTP and SSE only; "The `stdio` and WebSocket transports are not supported" |
| Tool Search mode (default on) | Exposes three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool` |
| Shipped toolsets | SceneTools, ActorTools, MaterialInstanceTools, ObjectTools; GASToolsets (UAttributeSetToolset) experimental and off by default. The doc names no Blueprint toolset |
| Custom tools (Python) | `unreal.ToolsetDefinition` subclass with `@unreal.uclass()`, methods with `@toolset_registry.tool_call` + `@staticmethod`, Google-style docstrings, under a plugin's `Content/Python/`; then `ModelContextProtocol.RefreshTools` |
| Custom tools (C++) | `UToolsetDefinition` with `UFUNCTION(meta=(AICallable))`. "Live Coding does not propagate new UFUNCTION declarations, so adding a tool requires an editor restart" |
| Limits | Loopback only, "No authentication layer", tool calls serial on the game thread; MCP Resources/Prompts not advertised |
| Telemetry | On by default (`ModelContextProtocol.EnableAnalytics`) |
| Debug | `Log LogModelContextProtocol Verbose`; `npx @modelcontextprotocol/inspector` (Streamable HTTP) |
| Runtime use | Can run in cooked builds via `IModelContextProtocolModule::StartServer()` + `AddTool()`. Status "use caution when shipping"; for this jam, Rule 7(f) argues against any runtime agent dependency |
| Linux | Doc lists no platforms; its terminal setup shows bash/zsh as well as `cmd.exe`. **Linux support unverified**: the PLAN.md gate (list toolsets, spawn and edit an actor) is the real test |

Additions from the itch "Get ready" links review (`_config/reference/research/get-ready-links-review-2026-11-05.md`, 2026-11-05):
- **Third plugin.** In Epic's webinar (uploaded 2026-09-07) the speaker says the online docs miss one plugin: besides Unreal MCP and All Toolsets you need **Editor Toolsets**, or the agent "connects but can't do anything". The setup video (2026-10-08) names Terminal as the third instead. Our rehearsal `.uproject` lists only `ModelContextProtocol`, `AllToolsets` and `ModelingToolsEditorMode`, yet worked; verify Editor Toolsets in the jam project (`stages/00_prep/references/jam-day-runbook.md`).
- **Context size of `describe_toolset`** (Epic trainer, same webinar): materials about 2,000 to 26,000 tokens, Niagara almost 250,000. Truncation makes small-context models loop. Describe only the toolset in use.
- **Packaging page gaps** (UE 5.8 "Packaging Unreal Engine projects"): no Linux-to-Windows cross-compile route and no zip step. Shipping drops the console, and a missing Game Default Map gives a black screen.

Smart Poly's 5.8 quickstart launches Claude Code from the project folder with `TERM=xterm-256color` ([YouTube, PqrKqhkj3gQ](https://www.youtube.com/watch?v=PqrKqhkj3gQ)). A third-party Codex walkthrough confirms the endpoint and notes that Codex approval mode "does not reliably classify inner operations behind `call_tool`" ([DEV Community](https://dev.to/gamedevtoollab/using-unreal-mcp-in-ue-58-from-codex-setup-toolsets-and-safe-editor-automation-4pon)). The same blind spot plausibly affects any client's per-tool permission rules, so guard destructive operations at the toolset level (inference).

### MCP log lines: normal and real

Source: signed-in forum read, 2026-11-05 (`~/.cache/hub-review-megajam/epic-community-signed-in-2026-11-05.md`, hub side session notes; forum reports, not Epic docs). A log check must not count the first two as failures.

| Log line | Verdict | Why (topic id) |
|---|---|---|
| `LogModelContextProtocol: Error: Call to unknown method "server/discover"` | Normal | Claude Code calls `server/discover` (MCP 2026-07-28) first on every connection. The 5.8.3 server answers MethodNotFound and logs it at Error level (t/2841847, Oct 17, UE 5.8.3) |
| `Unknown session id ... client should reinitialize` | Normal after an editor restart | The client's session id is stale (t/2731505 #1, t/2841847, t/2729488 #2) |
| `Invalid MCP server URL path` | **Real** | The client URL is wrong; use `http://127.0.0.1:8010/mcp` |
| `LogHttpListener: Error: unable to bind` during a cook | **Real** (cook exit 1) | Auto Start is on and an editor already holds the port (t/2735398). See the runbook, step 2 |

Health check without a client: `GET http://127.0.0.1:8010/mcp` returns **405** when the server is up. It is up only after the editor has fully loaded (map and shaders). Whether Claude Code reconnects alone after an editor restart is **untested** here; see the runbook's "Editor-restart recovery check".

### MCP traps (lead agent notes)

From forum reports (t/2731505 #1 and #3, t/2746458 #3, t/2732377, t/2743344), mostly UE 5.8.0 to 5.8.1. Re-test against 5.8.4 before relying on a fix; none was noted as fixed.

- `ObjectTools.set_properties` on an Input Mapping Context's `Mappings` reports success but saves nothing, and `get_properties` reads the fake value back. Author key mappings by Python (`InputMappingContext.map_key`) or by hand, then check at runtime (`showdebug enhancedinput`).
- `set_properties` on arrays cannot change size and contents in one call.
- `StringTableTools.set_entry` / `remove_entry` do not mark the package dirty, so edits are lost on save.
- `CaptureViewport`: the "optional" params `captureTransform` and `annotations` are required; pass explicit `null` (Epic's Claude Code plugin repo, issue 7). It returns the PNG as inline base64, 1.5 to 2.6 M characters per call. Budget that context cost, or call it inside `execute_tool_script` and keep only `labeledActors`.
- `find_actors` truncates at 20 results without saying so.
- Never pass a `list_properties` schema to `get_properties`: it crashed the editor (FName length assert, 5.8.1).
- No tool calls a UFUNCTION. Blueprint CDO edits need `compile_blueprint` then `save_assets`.
- No landscape toolset. Bulk asset moves grow VRAM until the editor restarts.
- Prefer ProgrammaticToolset (one Python script) for multi-step edits. Grep the toolset Python on disk (`Engine/Plugins/Experimental/Toolsets/<X>/Content/Python/<pkg>/toolsets/*.py`) instead of reading `describe_toolset`.
- A third-party trap register exists, `github.com/PavelVyny/ue58-mcp-field-notes`. Not read; read it normally before trusting it.

### UE 5.8.4 upkeep (5.8-era; 5.9 is now default, see jam-ue59-upgrade)

Source: t/2842775 (5.8.4 hotfix thread, Oct 20), t/2733237, t/2849229, t/2721597 (forum reports, 2026-11-05 read). We run 5.8.4 (*Superseded 2026-11-10:* 5.9 Preview is the default, 5.8.4 the fallback).

- If the jam project will not open after any engine update, delete `Saved`, `Intermediate` and `DerivedDataCache` first (fixed an "updated to 5.8.4 and Unreal won't open" report, t/2849229).
- Avoid StateTree-heavy designs unless tested on 5.8.4: an `InstancedStruct` assert was reported after upgrading from 5.8.3. Also reported on 5.8.4: Mutable plugin fails to load, about +3 GB RAM, a fatal shader-compile crash on view switch (Windows).
- Linux "editor crashes on any project file change" (UE-367645) is fixed in 5.8.4.
- Keep `SDL_VIDEO_DRIVER=x11` as a one-line fallback if the editor crashes on a Wayland session (CachyOS KDE defaults to Wayland; SDL3 explicit-sync error on "My Projects", t/2721597 #41, #42).
- Mesh Terrain does not work in packaged builds (t/2721597 #4). We do not use it.

### Epic's Claude Code plugin

"Unreal Engine skills for Claude Code" is listed as "Made by Epic Games" (871 installs at fetch time). It connects to the ToolsetRegistry ("hundreds of tools across 30+ toolsets") and injects UE conventions (UObject, Slate, UHT) through a SessionStart hook. Its safety rules are: save before and after bulk changes, run commands serially to avoid game-thread deadlocks, and wait for compilation. It lists actor spawning, Blueprint editing, materials, UMG, Sequencer, Niagara, Control Rig, GAS and automation tests, and project-specific Agent Skills can override its defaults ([claude.com plugin page](https://claude.com/plugins/unreal-engine-skills-for-claude-code)). **Blueprint coverage is documented inconsistently.** Epic's doc names no Blueprint toolset, while the plugin page and the Edge recap claim Blueprint editing ([Edge](https://knowledge.edge-online.com/p/ai-goes-native-in-unreal-engine-the-five-main-takeaways-from-state-of-unreal-2026)). Call `list_toolsets` before the jam and record the answer in `CLAUDE.md`.

### What to delegate and what to keep

| Delegate to agents (evidence) | Keep human-owned or template-seeded (evidence) |
|---|---|
| Greyboxing rooms and corridors (~5 min) ([Puget](https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/)) | Player input and control-scheme changes (broke in Puget's test) |
| Simple trigger Blueprints (same) | PCG graph authoring from scratch (faked in Puget's test). Start from templates or tutorials such as BrokeAsDev's, which Puget recommended ([YouTube](https://www.youtube.com/watch?v=k9YVBSs6_mQ)) |
| Actor placement, material instances, batch asset ops, automation tests (catalog inference from Epic docs) | Core feel tuning (Fun Factor counts double in ties) |
| Modifying existing PCG graphs used as "baseline references", as in Epic's City Sample 5.8 update ([Epic learning](https://www.unrealengine.com/learning/city-sample-gets-a-major-update-with-pcg-and-unreal-mcp-workflows)) | Final art direction and every asset approval (slop risk) |
| Blueprint tasks of the kind Smart Poly benchmarked: five BP problems vs hand-built ([YouTube, OiFtnBj1P9o](https://www.youtube.com/watch?v=OiFtnBj1P9o)) | Clicking Submit (Rule 17) |

### Community MCP servers, if the official one falls short

The famous early-2025 repos are stale. As of Oct 27, 2026 the actively maintained options are EngineWire, IvanMurzak and GenOrca (last-commit dates from shallow clones in the notes).

| Repo | Last commit | UE support | Strengths | Transport / license | Linux note |
|---|---|---|---|---|---|
| [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) ("EngineWire") | 2026-10-27 | 5.0–5.8 | "Over 400 capabilities" behind one `unreal` tool (0.6 beta; 0.5.30 stable has 23 tools): Blueprints and whole event graphs, UMG, materials, Niagara, PCG, GAS, StateTree, Sequencer, MetaSounds, PIE with synthetic input, packaging | HTTP or stdio, token-protected by default; MIT. Needs a C++ project or prebuilt binaries matched to engine minor and platform | Not documented |
| [IvanMurzak/Unreal-MCP](https://github.com/IvanMurzak/Unreal-MCP) | 2026-10-27 | 5.5+, CI 5.7, verified 5.8 | 26 core tools incl. 11 Blueprint tools with structured compile errors, C++ edit + compile with structured reports | C++ plugin + .NET sidecar + server (cloud or self-hosted); beta | **Only README that mentions Linux**: dialog automation X11-only, Wayland warned |
| [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp) | 2026-07-07 | 5.6+ | "253 actions across 21 domains" + `execute_python`; BP graph build/connect/compile/auto-layout | Python plugin; Apache-2.0 | Not documented |
| [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) | 2025-06-06 | 5.4+ | `editor_run_python` gives the full UE Python API via built-in remote execution, no plugin | `npx -y @runreal/unreal-mcp`; MIT | Minimal fallback |
| [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) | 2026-06-26 | Local 5.5+; hosted 5.5–5.7 | Local is "basic"; hosted "Flop MCP" now owned by Aura, API key | MIT | — |
| [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp), [kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP) | Apr / Jun 2025 | 5.5 era | Stale; Windows-oriented | MIT | Avoid |

Running two MCP servers against one editor risks game-thread contention, so test that combination before the jam or don't do it (inference).

### The agent build-and-verify loop

Agents can't safely edit binary `.uasset` files. The community pattern is: core logic in C++ exposed through `UFUNCTION(BlueprintCallable)`, thin Blueprints and data assets wired through MCP, and verification with the Unreal Automation Framework rather than GoogleTest ([Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)). One limit applies to the whole loop: Live Coding updates function bodies, but new reflected declarations need an editor restart ([Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)).

```text
1. Code worker edits C++ (text, diffable)
2. Build:  Engine/Build/BatchFiles/Linux/Build.sh <Project>Editor Linux Development <path>.uproject
           (standard UBT entry point; exact syntax NOT verified in a fetched source)
3. Restart editor with -ModelContextProtocolStartServer (needed for new UFUNCTIONs)
4. Lead agent wires levels/BP/materials via Unreal MCP, one call at a time
5. Headless test:
   UnrealEditor-Cmd <Project>.uproject -ExecCmds="Automation RunTests <Filter>" -NullRHI -NoSound -Unattended
   (verified form from Daniel Vaughan's article; tests via IMPLEMENT_SIMPLE_AUTOMATION_TEST)
6. grep Saved/Logs/*.log for "Error:" and feed results back to the worker
```

Python is the universal escape hatch: GenOrca's `execute_python` runs "any BlueprintCallable function or editor subsystem the engine exposes to Python" ([GenOrca](https://github.com/GenOrca/unreal-mcp)). Angelscript needs a licensee-gated engine fork and is not worth the risk in a 4-day jam, and Verse stays UEFN-only until UE6 ([Hazelight Angelscript](https://angelscript.hazelight.se/); [Epic State of Unreal 2026](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)). For hallucination control, UnrealCodex injects current class signatures and Epic's plugin injects conventions at session start ([Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)). Gate destructive operations such as `delete_all_actors`, `execute_console_command` and `save_all` behind approval hooks (same source).

### Agent and MCP pre-jam checklist

- [ ] Unreal MCP + All Toolsets enabled on the **Linux** editor; `GenerateClientConfig ClaudeCode` run; Claude Code lists toolsets (PLAN.md gate)
- [ ] `list_toolsets` output saved; Blueprint graph coverage confirmed or a community server chosen as backup
- [ ] Epic's "Unreal Engine skills for Claude Code" plugin installed and its SessionStart hook observed
- [ ] Project `CLAUDE.md`: engine 5.8.x (5.8-era; 5.9 is now default, see jam-ue59-upgrade), target Win64 Development, C++-first rule, one-MCP-caller rule, English-only, Teen content, no third-party IP, asset naming, destructive-op approval list, "never edit .uasset directly"
- [ ] Custom Python toolsets (game-agnostic) written, `RefreshTools` tested, declared
- [ ] Headless automation test command proven on a throwaway project
- [ ] Partner credits: check at kickoff whether Anthropic, Google, Meshy or OpenAI credits were announced ([Epic es-ES](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES))
- [ ] Mock jam (Nov 7–8) measured MCP latency per task; the slice size set accordingly. Puget's 5–15 minute responses mean a 2-hour slice holds only about 8–20 MCP round-trips (inference)

## Generated assets score, Fab assets do not

Rule 15(c) changes the old jam playbook. In 2023, sourced assets were also unscored, but Epic said their *implementation* could earn points, for example spatialization or real-time modulation of sourced audio ([Fortnite.com 2023](https://www.fortnite.com/news/the-epic-megajam-is-open-to-uefn-submissions)). The 2026 digest says sourced assets "will not be reviewed or scored" and that AI-generated content "is not considered a sourced asset" (Rules v2, Rule 15(c), via RULES.md). **For Jared, his local generation pipeline turns into Visuals and Audio points, and a Fab pack adds nothing.** Everything still has to be generated inside the contest window (Rule 7(h)), so the only pre-jam work allowed is the scripts and their measured minutes-per-asset (win-plan).

### AI generation tools and their licenses

Verified follow-up on AMD/ROCm support, Interchange import (incl. the glTF parent-material correction), rigging, licences, stylized look and AI audio: [_config/reference/research/ai_asset_to_ue_handoff.md](research/ai_asset_to_ue_handoff.md) (2026-10-29).

License details below come mostly from a vendor-authored guide and must be confirmed on each vendor's own terms page ([Cinevva guide](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)). Every license must also allow a contest entry plus Epic's non-exclusive publicity license (Rule 15(b), per win-plan).

| Tool | Use | License / cost as reported | Jam fit | Source |
|---|---|---|---|---|
| **Meshy** (MegaJam partner) | Text/image → textured, rig-ready PBR mesh | Free 100 credits/mo, outputs **CC BY 4.0 (attribution required)**; Pro ($20/mo)+ full ownership | Possible partner credits; Bridge sends FBX into `Content/MeshyImports`, **requires Pro**, port 5327, Window > Meshy Bridge each session; OS support not stated | [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games); [Meshy Bridge docs](https://docs.meshy.ai/en/webapp/plugins/unreal/bridge-to-unreal) |
| Tripo | Text/image → 3D, 4K PBR, auto-rig (non-humanoids since Feb 2026) | Free plan **non-commercial**; paid includes commercial rights | Good for creatures if paid | [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games) |
| Rodin / Hyper3D | Clean quad topology | Generation free, downloads paid | Optional | Same |
| **TRELLIS.2** (Microsoft) | 4B image → 3D with native PBR (base color, roughness, metallic, opacity) | **MIT**, Dec 2025 | Strong local, no-cost option | Same |
| Hunyuan3D 2.0 / 2.1 | Open weights + PBR texturing | Tencent community license; §5(c) restricts use and display of **outputs** outside the Territory (EU, UK, South Korea excluded) | **Being replaced by TripoSplat (MIT), 2026-11-01**; see open question 24 | Same; `stages/00_prep/references/license-check-modly-foundrylab.md` |
| **TripoSplat** (VAST-AI, Modly extension) | Image → Gaussian splat → watertight vertex-colored GLB (no UV texture), ~10 GB VRAM | **MIT** (HF tag and extension LICENSE) | Chosen replacement 2026-11-01; **pending live ROCm smoke test**; not yet wired into `nexus-3d` | `~/Documents/Modly/extensions/triposplat/` |
| Hunyuan 3D 3.0 | Hosted only, 20 free generations/day | Not open weights | Optional | Same |
| **UniRig** | Predicts skeletons + skin weights for bipeds, quadrupeds, birds, insects | **MIT** (SIGGRAPH 2025) | Rigging fallback | Same |
| NVIDIA SOMA-X | Retargeting | Apache 2.0 | Optional | Same |
| Mixamo | Rig/anim library | Guide calls it "become unreliable" (no detail); jam ruling unanswered in the forum | Avoid relying on it | Same; [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973) |
| **Qwen-Image** | Concept art, textures, UI; good text rendering | **Apache 2.0 for v1 (`Qwen/Qwen-Image`) only.** The installed Qwen-Image 2.1 is `qwen-research`, non-commercial | **Do not use for anything that ships.** Superseded by Krea 2 Turbo | [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games) |
| FLUX.2 klein 4B | Images, ~13 GB VRAM | Apache 2.0 (**9B variant non-commercial**) | Use 4B only | Same |
| SD 3.5 | Images | Community License, free under $1M revenue | OK | Same |
| Scenario / Layer | Hosted game-art generation | Commercial from $15/mo / on all plans | Optional | Same |
| **ACE-Step 1.5** | Music, <4 GB VRAM | **MIT** (Feb 2026) | In win-plan pipeline | Same |
| Stable Audio 3.0 | Small-SFX, Small-Music, Medium open weights; Large API-only; "trained on licensed data" | Stability Community License | Considered, not picked — MetaSound covers the same need with no license at all | Same |
| ElevenLabs | SFX, music, voice | Commercial rights on paid plans | Considered, not picked — cloud cost/dependency not needed given MetaSound | Same |
| **Epic MetaSound SFX Generator** (free Fab plugin "TechAudioTools Content"; **not** bundled with the 5.8 editor: the engine's TechAudioTools plugin has no Content, checked 2026-11-02; owner adds it from Fab, else built-in MetaSound graphs + Kenney CC0) | Procedural SFX, placeholder or final | Epic content under the UE EULA (not "no license"; see open questions 20-21) | **Picked 2026-10-28, primary SFX source.** Generated, not sourced, so it scores under Rule 15(c); zero VRAM, zero external terms | [Epic Mar 2026 roundup](https://www.unrealengine.com/learning/marchs-epic-learning-content-substrate-metahuman-and-more) |
| **Kenney.nl sound packs** (Interface Sounds, Impact Sounds, Sci-fi Sounds, Digital Audio) | Pre-made SFX, fallback only | **CC0 1.0** (public domain, no attribution required) — confirmed directly on kenney.nl's asset pages, which link to [creativecommons.org/publicdomain/zero/1.0](https://creativecommons.org/publicdomain/zero/1.0/) | **Picked 2026-10-28, fallback SFX source** if MetaSound can't cover a sound in time. Sourced under Rule 15(c), so it must go in the sourced-asset ledger and earns no points, but has the lowest license risk of any sourced option checked (no per-item variation, no attribution to track, unlike Freesound/OpenGameArt) | [kenney.nl/assets/interface-sounds](https://kenney.nl/assets/interface-sounds) |
| Epic diffusion tools (depth/normal/camera conditioned) | Styled frames, object extraction | Release planned "early next year" | **Not available for the jam** | [Epic State of Unreal 2026](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show) |
| **ChatGPT image (via codex bridge)** | Concept image fallback/alternative to Krea | OpenAI Terms of Use: you own the Output; no competing-model use ([terms](https://openai.com/policies/terms-of-use/); excerpt only, page returned 403, 2026-11-06) | **Allowed, owner approved 2026-11-06.** AI-generated, not sourced (Rule 15(c)). Spends ChatGPT quota. `gen_asset.py --provider gpt`; see `_config/reference/ai-providers.md` | Same |
| **Grok Imagine** (xAI API, `grok-imagine-image-2.0`) | Concept image fallback | xAI terms: you own the Output; some versions ask for attribution; API vs consumer terms unclear ([terms](https://x.ai/terms-of-service); 403, 2026-11-06) | **Conditional:** owner reads live xAI terms first. Key via `XAI_API_KEY` only; never run against the real API yet. [API docs](https://docs.x.ai/docs/guides/image-generation) | Same |
| Modly, foundry-lab (win-plan pipeline) | Image → 3D; remesh and bake | Local-only, no third-party license (Nexus/foundry-lab tooling runs on this machine) | **Proven end-to-end 2026-10-28** — `scripts/gen_asset.py` runs Krea 2 Turbo (Qwen-Image before 2026-10-29) → foundry-lab remesh/bake at ~3 min/asset; `scripts/ue_import_asset.py` imports the `.glb` into UE 5.8 (collision + LOD set). See `stages/02_build/output/asset-pipeline-log.csv` and `_config/reference/engine-reference/unreal/python-scripting.md` | — |

Two practical rules follow (inference). First, if Meshy's free tier is used, CC BY 4.0 attribution belongs in the credits and the disclosure table. Rule 15(c) still classes the result as AI-generated, not sourced. Second, avoid humanoid heroes. AI-generated rigs are "the weakest link in the pipeline", and a creature, vehicle, object or abstract hero sidesteps that (win-plan). Tripo's and UniRig's non-humanoid rigging support fits that choice.

### Fab, Megascans and MetaHuman status

Fab gives away "Limited-Time Free" items on a two-week cycle and keeps some permanently free resources, including some Megascans ([Unreal Engine free content](https://www.unrealengine.com/fabfreecontent)). The Megascans library as a whole stopped being free after 2024, and earlier acquisitions keep their original license ([80.lv](https://80.lv/articles/megascans-no-longer-free-after-2024/)). The 2023 jam page's "Megascans are free" line is outdated. **The sources conflict on MetaHuman licensing.** Edge reports that 5.8 moved MetaHuman to an MIT license ([Edge](https://knowledge.edge-online.com/p/ai-goes-native-in-unreal-engine-the-five-main-takeaways-from-state-of-unreal-2026)). metahuman.com says it is free under $1M revenue and usable in any engine ([metahuman.com](https://www.metahuman.com/en-US/license)). Either way, MetaHumans are a size and frame-cost trap in a 4-day jam (inference), and under Rule 15(c) any sourced asset earns nothing.

### Starting templates by genre

Epic's 5.6+ template variants are the fastest legal scaffolding. Rule 7(d)/(e) still requires gameplay that goes beyond them ([Epic Variants doc](https://dev.epicgames.com/documentation/unreal-engine/variants-in-game-templates)).

| Genre | Variant | What it ships with |
|---|---|---|
| Brawler / action | Third Person, **Combat** | Hand combat, combos, AI opponents, in-world health bar |
| Platformer | Third Person, **Platforming** / **Side Scroller** | Dash, wall jump / locked side camera, pickups, drop-through collision |
| Shooter | First Person, **Arena Shooter** | Weapon pickups, bullet types, AI, ammo UI |
| Horror / atmospheric | First Person, **Survival Horror** | Low-light lighting, flashlight, sprint UI, flickering lights |
| Arcade score-attack | Top Down, **Twin Stick** | Dual-axis aim, AI, bomb-and-shoot, score/multiplier UI |
| Tactics | Top Down, **Strategy** | Grid movement, drag-select AI, orthographic camera |
| Racing | Vehicle, **Timetrial** / **Offroad** | Lap timing, checkpoints / modular vehicle, RVT, HLOD |

The Game Animation Sample (GASP) gives motion-matched locomotion with 500+ animations. It was updated for 5.8 with Physics Control, powered ragdoll and multi-character interactions, but it adds hundreds of MB, so use it only if movement feel is the core ([Epic GASP 5.8 blog](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8); [Epic GASP 5.7](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)). Lyra and City Sample are too heavy for a solo 4-day jam. Cropout and Stack-O-Bot are useful references, not bases (inference; no package sizes verified).

### UE 5.8 feature verdicts (5.8-era; 5.9 is now default, see jam-ue59-upgrade)

| Feature | Status | Verdict for the jam |
|---|---|---|
| Enhanced Input (now unified with Common Input/UI in 5.8; new Input Debugger) | Production | **Use** ([5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)) |
| StateTree (5.8 adds start state, Compiler Manager) | Production | **Use** for 2–3-state enemies |
| Niagara | Production | **Use**: highest juice per hour (inference) |
| MetaSounds | Production; Templates Experimental | **Use lightly**: random pitch and variations; skip Templates |
| PCG (production since 5.7; 5.8 adds overrides, GPU runtime scatter) | Production | **Scatter only**; don't author graphs from scratch |
| Lumen / Lumen Lite (Beta, 2× faster) | Production / Beta | Keep on; default Medium |
| MegaLights | Production (5.8) | Only for many dynamic lights; else `r.MegaLights.Supported` off |
| Substrate | Production (5.7) | Fine; Substrate NPR toon shading is **Experimental**, so a post-process stylization material is safer |
| Nanite | Production | Static meshes only; skip Experimental Nanite Foliage |
| Mover | Experimental | **Skip**; use Character Movement Component |
| Procedural Vegetation Editor, Mesh Terrain | Experimental | **Skip** |
| GAS, Lyra-style frameworks | — | Skip unless already fluent (Bit Barrage lost ~4 hours to a late rewrite) ([Bit Barrage](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)) |
| Chaos destruction | — | Gimmick only; simple impulses fine |

Status sources: [UE 5.7 news](https://www2.unrealengine.com/news/unreal-engine-5-7-is-now-available); [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes). Verdicts are the fast-build notes' inference.

### Juice and shell checklists (built during the jam, specified now)

**Jam-day order:** these items as an ordered, hour-by-hour pass, cheapest first: [_config/reference/canon/jam-polish-pass.md](canon/jam-polish-pass.md) (2026-11-11).

Build recipes for these, with UE 5.8 node names and minute estimates: [_config/reference/research/game_feel_recipes_ue58.md](research/game_feel_recipes_ue58.md) (juice), [_config/reference/research/fast_ui_and_input_ue58.md](research/fast_ui_and_input_ue58.md) (menus, HUD, input) and [_config/reference/research/first_two_minutes_level_design.md](research/first_two_minutes_level_design.md) (onboarding and the day-3 checklist), all 2026-10-29.

Class names below were not re-verified against 5.8 docs.

- [ ] Camera shake on hit, land and explosion
- [ ] Hit-stop via brief global time dilation (~0.05–0.1 for 50–100 ms)
- [ ] Niagara burst + decal on impact; hit-flash material parameter
- [ ] FOV kick or radial blur on dash
- [ ] One post-process volume: grading LUT, vignette, bloom, grain or stylization material
- [ ] UI scale-punch on score and damage numbers
- [ ] SFX with ±5–10% random pitch and several variations; music ducking submix
- [ ] Controller rumble (Force Feedback)
- [ ] Shell: title with game name, controls that switch for gamepad, pause (resume/restart/settings/quit), volume sliders, scalability presets, working Quit, no debug text, PSO wait screen
- [ ] Epic's free SFX Generator MetaSound in the Tech Audio Tools Content plugin, for placeholder or final SFX ([Epic Mar 2026 roundup](https://www.unrealengine.com/learning/marchs-epic-learning-content-substrate-metahuman-and-more))

### Why to skip live LLM NPCs in this entry

Walkie-Talkie, the only LLM-NPC prize, is UEFN-only (Rules v2). Live dialogue in a packaged UE build means API keys, 1–2 s cloud latency where ~800 ms "feels natural" ([Cinevva NPC guide](https://app.cinevva.com/de/guides/ai-npcs-dialogue)), and plugin version risk: Convai did not support 5.8.1 on July 30 and shipped support on Aug 3 ([Convai forum](https://forum.convai.com/t/convai-fails-to-load-when-updating-from-ue-5-8-to-5-8-1/6436)). A build that needs a key or a running model server also collides with Rule 7(f). Pre-generated dialogue gives most of the benefit at no risk (inference).

## Past winners turned the theme into the mechanic

Epic's winner posts contain almost no judge reasoning, so the lessons from past MegaJams come from patterns in the winner lists, not from stated preferences. Three patterns hold up. Winners make the theme the core mechanic. Main-category winners often also win a craft modifier. And small, finished games beat ambitious broken ones. MegaJams used to run seven days. This one runs four, which raises scope pressure (inference, [Epic 2022 winners](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2022-epic-megajam)).

| Year | Theme | Scale | Notable winners | Pattern |
|---|---|---|---|---|
| 2017 | "However vast the darkness, we must supply our own light" | 279 submissions | ASSIMILATION, Filament, Light Bearers; Army of One: Bureau of Happiness | — ([Epic 2017](https://www.unrealengine.com/blog/the-2017-epic-megajam-results-are-in)) |
| 2019 | "Down to Earth" | — | 1st Planted; Army of One: Deltanian Invasion | Epic: "stunning graphics… quirky gameplay… moving storylines" ([Epic 2019](https://www.unrealengine.com/blog/celebrating-the-winners-of-the-2019-epic-megajam)) |
| 2021 | "Running Out of Space" | 504 games, 3,000+ people | 1st **BotiBoi** (+ Nvisionary Environments); 2nd Seekers (+ KitBasher, Tiny Award); Army of One: Container City | BotiBoi read the theme as software saving files before a crash; the team later shipped a commercial game ([Epic 2021](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2021-epic-megajam); [Pad and Pixel](https://padandpixel.com/?p=5150)) |
| 2022 | "As Above, So Below" | 509–525+ entries | 1st **Fregward: Spirit Warden** (+ Tiny But Mighty); 3rd Backstage Shenanigans (+ Make Us Go WOW Stylized); Army of One: The ResT | Fregward's mirrored physical/spirit realms *are* the theme; won despite a buggy tutorial and no video; 72 MB download ([Epic 2022](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2022-epic-megajam); [Fregward](https://honestdan.itch.io/fregward)) |
| 2023 | — | — | UE 1st Rolling Back; Student 1st Solaris (+ Audio Experience); Army of One: Lamp Lighter | First year with UEFN ([Unreal Source](https://unrealsource.com/d/2023-epic-megajam-winners/)) |
| 2025 | "Here We Go Again" (+ 3 classic themes) | 491 entries, 31 categories | RTX On 1st Glitch In The Labyrinth; Digital Brush Mastery: Kronos (repeat winner) | Judging delayed by a "truly remarkable number" of entries ([Epic forum](https://forums.unrealengine.com/t/2025-epic-megajam-mega-stack-o-jam-update/2689696?page=2); [Epic news](https://www.unrealengine.com/news/epic-megajam-2025)) |

Testimony from outside Epic points the same way. Judge Rob Miles: "If you want the judges to like your game, make it very, very, easy for them to get to it". Instruction screens should be one of the first things added, because he spent five minutes in one game without learning its goal ([Rob Miles](https://www.robmiles.com/journal/2015/31/3/meatlyjudged)). Mark Brown of GMTK favors themes that "force them to design around problems", and a GMTK developer advises "one new mechanic at a time" ([EGM](https://egmnow.com/jam-sesh-how-a-popular-online-contest-sparks-gameplay-innovation/)). Kenneth Ng's 2015 MegaJam team, who did not win, recommend picking a target award early, brainstorming 10+ ideas, building movement plus core interaction first, keeping placeholder art until the gameplay is proven, and holding a buffer day ([Game Developer](https://www.gamedeveloper.com/design/how-to-make-a-game-in-one-week-epic-megajam-learnings)). Their 30-minute playtime target is probably wrong for a jam with hundreds of entries, where judges likely spend minutes per game (inference).

### The "AI slop" backlash is part of the judging environment

This jam launched into hostility. Its poster drew mockery because the AI hand had six fingers. Critics tied the jam to Tim Sweeney's "maximum AI acceleration" remarks ([WN Hub](https://wnhub.io/news/Generative_AI/item-52485); [TechRadar](https://techradar.com/gaming/pc-gaming/vibe-your-way-to-usd50k-epic-is-challenging-devs-to-build-a-game-in-4-days-with-ai-and-gamers-are-in-full-rebellion-now)). Forum replies are mostly negative. One reads "Last year, there was a ban on AI. Now it's the headline" ([Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)). The closest precedent, levelsio's Vibe Jam, still rewarded feel over novelty. Its 2025 winner, *Great Taxi Assignment*, was praised for "responsive controls" and physics that "feel right" ([CO/AI](https://getcoai.com/video/the-best-ai-made-videogames-2025-vibe-coding-game-jam/)), and its 2026 rules required instant-play browser games with no heavy downloads ([Vibe Jam press](https://vibejam.com/2026/press)). The lesson (inference): AI should be invisible in the art and the feel, and visible only in the dev log. Visual inconsistency, generic LLM text and anatomical artifacts are the tells to remove by human review.

### Jam-week additions to the PLAN.md runbook

PLAN.md's gates stand. The notes add these sourced refinements.

| Moment | Addition | Source |
|---|---|---|
| Day 1 | Epic's itch tip says test build "on day two". Win-plan is already a day earlier; keep it | [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/) |
| Every day | Package daily, because packaging failures and missing maps are the top late-jam failures | Fast-build notes failure table |
| Day 2 | Tell playtesters you want gameplay feedback, not comments on looks | [Game Developer](https://www.gamedeveloper.com/design/how-to-make-a-game-in-one-week-epic-megajam-learnings) |
| Day 2–3 | Add audio and UI before secondary features | [Unreal Source](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/) |
| Day 3 | Tune easy; add skip or checkpoints so judges reach the ending | [Bit Barrage](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem) |
| Day 4 | Reserve 1–2 hours for presentation; normalize audio; do one final full playthrough | [Kenney](https://kenney.nl/learn/improving-the-presentation-of-jam-games) |
| Daily 11 AM PT | Skim livestreams for rule clarifications only (win-plan) | RULES.md |

## Presentation and the dev log are where Glass Box is won

Judges reach the game through an itch page, a 30–60 second video and a download. For a UE desktop build, the video carries more weight than in browser-first jams (inference, [Rob Miles](https://www.robmiles.com/journal/2015/31/3/meatlyjudged)). Glass Box is the one prize where the AI process is the point: Inven describes it as the "best dev log showing AI tool use" ([Inven](https://www.invenglobal.com/articles/27578/epic-games-announces-2026-epic-ai-megajam-with-up-to-50000-in-grants)), and the Rules v2 name implies transparency. No source says what Epic's Glass Box judges want, so the structure below is the notes' reasoned recommendation.

### The 30–60 second video

Page template and a 60 s shot-by-shot outline: [_config/reference/research/submission_page_and_video.md](research/submission_page_and_video.md) (2026-10-29).

The rule: 30–60 seconds of **recorded gameplay** at 1920×1080 or higher, in English (Rules 1(e), 7(c), 7(i)). Trailer research says to open on gameplay. "Having it appear 15–30 seconds in? They're not going to wait", and viewers scrub for "raw gameplay" ([GameDiscoverCo](https://newsletter.gamediscover.co/p/game-trailers-breaking-down-a-key)). Kenney: "no intro, no developer logos, no quirky text – just gameplay from the very first second" ([Kenney](https://kenney.nl/learn/improving-the-presentation-of-jam-games)). The notes suggest Movie Render Graph (production-ready in 5.8) for hero shots ([YouTube, 0c8-8NSarDI](https://www.youtube.com/watch?v=0c8-8NSarDI)). Because the rule says recorded gameplay, keep rendered cinematics to a closing shot at most (inference). Win-plan's spec stands: OBS 1080p60 replay buffer, gameplay in the first 5 seconds, end on the title card, unlisted YouTube.

### itch page checklist

- [ ] Unique game title, never just the jam name ([Kenney](https://kenney.nl/learn/improving-the-presentation-of-jam-games))
- [ ] Bright, legible cover/thumbnail: "Having no thumbnail or icon at all is death blow for noticeability" (same)
- [ ] 4–6 varied screenshots; no duplicates, no title-screen shot (same)
- [ ] 3–5 s looping GIF of the theme mechanic (notes' recommendation)
- [ ] Description: how to play, controls, goal, the theme, known bugs, credits; instructions repeated in-game (Kenney)
- [ ] Download: `TeamName_GameName.zip`, under 1 GB, with a readme (RULES.md; notes)
- [ ] Sourced-asset list (if any) and the pre-jam declaration (Rules 1(d), 7(h))
- [ ] Unreal Engine logo only per Epic branding guidelines; no other trademarks (Rule 15(d))

### Glass Box dev log template

Post one entry per jam day plus a "how it was built" wrap-up, all published before the form is submitted (Rule 10; win-plan). The notes recommend this per-entry structure, which suits a reader who distrusts AI (inference):

| Section of each entry | Content |
|---|---|
| Goal of the day | The gate from PLAN.md and whether it was hit |
| Agent workflow | Diagram of which agent/model did what, through MCP into UE (win-plan's Mermaid diagram is a ready base) |
| Representative prompts | 1–2 verbatim prompts |
| Before/after | Clips or screenshots |
| What the AI got wrong | And how a human fixed it |
| Time | Time saved vs time lost (MCP latency logs from the mock jam help here) |
| Human decisions | A list of the creative calls Jared made |

The wrap-up ends with a **disclosure table** covering every asset and system, labeled AI-generated, AI-assisted or hand-made, plus the declared pre-jam items. The extent of AI use is "context only" for scoring (Rule 9), and Rule 7(h) already requires the pre-jam declaration. An honest, timestamped log therefore costs little extra, and it is the thing Glass Box judges.

### The three disclosures, kept separate

| Disclosure | Required by | Contents |
|---|---|---|
| Pre-jam tooling declaration | Rule 7(h); [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983) | `pre-jam-tooling` tag; list of prompts, scripts, configs, MCP settings, AI tools |
| Sourced assets | Rules 1(d), 15(c) | Name, author, URL, license for each (ideally none) |
| AI-use summary | Not mandatory; Rule 9 says it's context only | Models and tools per task; CC BY attributions (e.g., Meshy free tier) |

## Fifteen videos to watch before November 12

The catalog team never watched a video end to end. Summaries come from descriptions, Epic write-ups and transcript notes, and most lengths were unrecoverable because of YouTube bot protection. The verification tags below are theirs. Total viewing time is about **6–8 hours** if long streams are skimmed by chapter. Watch the AI items first, then the gameplay starters, then visuals and shipping.

| # | Video | Channel / date | Why it matters | Tag |
|---|---|---|---|---|
| 1 | [State of Unreal 2026](https://www.youtube.com/live/9ikOoOzAhPE): chapters 33:28 (UE 5.8) and **41:47 (MCP server support)** | Unreal Engine, Jun 17, 2026 | Official MCP demo (Edge reports Claude Cowork running prompts in-project) | [V] official |
| 2 | [From Words to Worlds: Integrating MCP into the Unreal Editor](https://www.youtube.com/watch?v=lDf_y-YPELo) | Unreal Engine, Aug 3, 2026 | What 5.8 MCP supports, extending it, LLM + PCG Primitives | [V] official |
| 3 | [NEW UE 5.8 MCP Tutorial (QuickStart)](https://www.youtube.com/watch?v=PqrKqhkj3gQ), 12:21 | Smart Poly, Jun 19, 2026 | Fastest zero-to-working MCP + Claude Code | [V] non-official |
| 4 | [I Tested Claude Inside UE 5.8](https://www.youtube.com/watch?v=OiFtnBj1P9o) | Smart Poly, Jun 20, 2026 | Five Blueprint problems, agent vs hand-built: calibrates delegation | [V] non-official |
| 5 | [Epic MegaJam 2025 Winners Announcement, Inside Unreal](https://www.youtube.com/watch?v=SsR4mzX9-4o) | Unreal Engine, Mar 12, 2026 | Winning scope and polish level; the only source of judge-adjacent commentary | [V] official |
| 6 | [Unreal Engine 5.8 Is Now Available](https://www.youtube.com/watch?v=Aaf12f_LA_Y), 8:30 | Unreal Engine, Jun 23, 2026 | Fast 5.8 catch-up | [V] official |
| 7 | [New Template Sneak Peek, Inside Unreal](https://www.youtube.com/watch?v=BHI6zx8QMkg) (Epic links t=965s) | Unreal Engine, Apr 3, 2025 | Template variants = jam scaffolding | [V] official |
| 8 | [Game Animation Sample Project Update, UE 5.7](https://www.youtube.com/watch?v=kmXaVIANa-c), then the [5.8 GASP blog](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8) | Unreal Engine, Feb 20, 2026 | Character feel if movement is the core | [V] official |
| 9 | [A First Look at PCG in UE 5.7](https://www.youtube.com/watch?v=bgxVHKSdL4M) | Unreal Engine, Feb 5, 2026 | PCG Editor Mode, Biome Core V2 for set dressing | [V] official |
| 10 | [Artist's Guide to Using MegaLights in UE 5.8, Inside Unreal](https://www.youtube.com/watch?v=Nrb17mtBJPM), 2:46:35 (skim) | Unreal Engine, Oct 8, 2026 | Many shadowed lights cheaply, for Visuals and Render Royalty | [V] official |
| 11 | [How to Start Your Project at 60 FPS and Keep It There](https://www.youtube.com/watch?v=DxBKmQ-0kfw) + [CVar resource hub](https://dev.epicgames.com/community/learning/talks-and-demos/YoB7/unreal-engine-how-to-start-your-project-at-60-fps-and-keep-it-there) | Unreal Engine, Jul 22, 2026 | Win-plan's 60 fps budget on the Go S | [V] official |
| 12 | [101 Unreal Engine Tips & Tricks: The Reckoning](https://www.youtube.com/watch?v=4w0PWcRwyOc) | Unreal Engine, Nov 29, 2025 | Property Matrix, Mesh-to-Collision, cooker instigator logging | [V] official |
| 13 | [Movie Render Graph Intro](https://www.youtube.com/watch?v=0c8-8NSarDI) | Unreal Engine, Dec 5, 2025 | Closing shot / cover art capture | [V] official |
| 14 | [Your First Hour in Unreal Engine 5.7](https://www.youtube.com/watch?v=b37Z9l-_g7c) (skim) | Unreal Engine, Dec 9, 2025 | Minimal game-loop scaffold: Blueprints, UMG, testing | [V] official |
| 15 | [How to package your UE 5.7 project…](https://www.youtube.com/watch?v=AWzhZnSq9u0) (alt: [Gorka Games](https://www.youtube.com/watch?v=JOMrVMwGBso) [S+notes]) | UNF Games, Nov 13, 2025 | Packaging walkthrough | [V] non-official |
| Live | Kickoff and theme reveal, Nov 11, 11 AM PT, youtube.com/unrealengine or twitch.tv/unrealengine | — | Theme; possible rule and credit announcements | — |

Optional extras: [Best Practices for Networked Movement Abilities](https://www.youtube.com/watch?v=tSVcRbfK8X8) for dash, vault and grapple verbs [V]; [Epic MegaJam 2023 Winners](https://www.youtube.com/watch?v=e8falymc1Nk), where hosts play winners and discuss favorite parts [V]; [MCP in UEFN](https://youtube.com/live/OU5OT06YxtQ), the agent build–compile–playtest loop, UEFN-only [V].

### Must-read pages

| Page | Why |
|---|---|
| [Unreal MCP in Unreal Editor (Epic docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) | Source of every MCP command above |
| [Unreal Engine skills for Claude Code (Epic plugin)](https://claude.com/plugins/unreal-engine-skills-for-claude-code) | Install and safety rules |
| [Puget Systems MCP hands-on](https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/) | Honest capability and latency data |
| [EDC: Build a Playable UE5 Level with AI (MCP + Claude Code)](https://dev.epicgames.com/community/learning/tutorials/bnJ0/build-a-playable-unreal-engine-5-level-with-ai-mcp-claude-code) and [Using the UE5 MCP Server with Claude Code…](https://dev.epicgames.com/community/learning/tutorials/DEKE/using-the-unreal-engine-5-mcp-server-with-claude-code-codex-cli-and-cursor) | Community walkthroughs on Epic's site |
| [City Sample PCG + Unreal MCP update](https://www.unrealengine.com/learning/city-sample-gets-a-major-update-with-pcg-and-unreal-mcp-workflows) | PCG graphs as agent baselines |
| [Your First 60 Minutes with StateTree](https://dev.epicgames.com/community/learning/tutorials/lwnR/unreal-engine-your-first-60-minutes-with-statetree) | Enemy AI fast |
| [8 tips for surviving the Epic MegaJam](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/) | Jam logistics |
| [Kenney: improving the presentation of jam games](https://kenney.nl/learn/improving-the-presentation-of-jam-games) | itch page and GIF |
| [Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine) and the [RX 9070 XT crash thread](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749) | Jared's exact hardware |

### Topic catalog beyond the top fifteen

| Topic | Item | Tag |
|---|---|---|
| Stylized look | "Create a Material with Substrate NPR Shading in UE 5.8" (community; URL not extracted; listed in [Epic Jun 2026 roundup](https://www.unrealengine.com/learning/junes-epic-learning-content-metahumans-mesh-terrain-and-more)) | — |
| PCG text tutorials | [PCG for Beginners 01](https://dev.epicgames.com/community/learning/tutorials/l5v0/unreal-engine-fab-ue5-series-pcg-for-beginners-01-level-setup-first-pcg-graph), [Avoid Overlapping Assets](https://dev.epicgames.com/community/learning/tutorials/Ev4d/unreal-engine-ue5-series-pcg-for-beginners-avoid-overlapping-assets-easily), [PCG Parameters](https://dev.epicgames.com/community/learning/tutorials/v7YZ/unreal-engine-ue5-series-pcg-for-beginners-pcg-parameters-explained), [Lumen flicker fix](https://dev.epicgames.com/community/learning/tutorials/mmxB/how-to-fix-lumen-light-flickering-in-unreal-engine-without-losing-performance) | Epic-hosted |
| PCG cities | [Procedural Cities for Tech Artists](https://www.youtube.com/watch?v=7uuFPOKIw8I) (Oct 3, 2026); [BrokeAsDev Ultimate City PCG](https://www.youtube.com/watch?v=k9YVBSs6_mQ) | [V] |
| Mesh Terrain (Experimental) | [A Practical Look at Mesh Terrain](https://www.youtube.com/watch?v=XlbWtoIk-Zc) | [E] |
| Animation | [State of Rigging and Animation Tools in 5.8](https://www.youtube.com/watch?v=yi-oDmC1nqU); [Animation Techniques in 5.8 lab](https://www.youtube.com/watch?v=Cc1YgOxdNI8) (physics control rigs, "mouse mocap") | [V] |
| Motion matching | [Motion Matching and GASP in 5.4](https://www.youtube.com/watch?v=tNw9lD2PW3U) (41:28) | [V] |
| Mover (skip in jam) | [An Introduction to the Mover Plugin](https://www.youtube.com/watch?v=P4IKS5k47Wg) | [V] |
| Destruction + VFX | [Chaos Destruction for Beginners – Adding Niagara FX](https://www.youtube.com/watch?v=acNTJdvSX08) (links a free Niagara Examples Pack) | [V] |
| Niagara | [UE5.6 Niagara](https://www.youtube.com/watch?v=dPZXPQoC_AQ); [Hits and Impacts Effects](https://www.youtube.com/watch?v=u64lmeu22PM) | [S] |
| Audio | [MetaSounds in UE5: From Miniguns to Music](https://www.youtube.com/watch?v=3230-FwCts0) (2021); [MetaSound Adaptive Granular Synthesis](https://dev.epicgames.com/community/learning/tutorials/jaX5/unreal-engine-metasound-adaptive-granular-synthesis); [MetaSounds Quick Start doc](https://dev.epicgames.com/documentation/unreal-engine/metasounds-quick-start) | [V] / text |
| Shader cost | [Systemic Shader Reduction (Fortnite −68%)](https://www.youtube.com/watch?v=wobQ8ZKQpbc) | [V] |
| Profiling | [Profiling with Pirates](https://www.youtube.com/watch?v=CYvLn-tYRag); [Fighting the Frame Budget (2XKO)](https://www.youtube.com/watch?v=Pkd7-ouyb-M); [Optimizing Next-Gen Mobile Features](https://www.youtube.com/watch?v=TnRvkxf6tZY) | [S] |
| Project Launcher | [How to use Project Launcher to package a game in UE5](https://www.youtube.com/watch?v=XAtOXmyqq18) (UE 5.0-era UI) | [V] |
| Android | [On-Click UE 5.7 Android Packaging](https://www.youtube.com/watch?v=SCtAfDeWXBM) + [babaei.net blog](https://www.babaei.net/blog/unreal-engine-android-packaging-apk-build-tutorial-meta-quest-htc-vive-standalone/); [Packaging Android Projects (Epic)](https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-android-projects-in-unreal-engine) | [S] / doc |
| 5.8 overviews (non-official) | [GameFromScratch: UE 5.8 Is HERE…and So Is AI](https://www.youtube.com/watch?v=WJLe8WdHv9g) [V]; [Unreal Sensei: Why 5.8 is a Game Changer](https://www.youtube.com/watch?v=5d6mZNA_5sg) [V]; [Smart Poly: 5.8 New Features](https://www.youtube.com/watch?v=K0DdXwmGJ9Q) [S] | mixed |
| Lighting primer | [William Faucher: Lighting in UE5 for Beginners](https://www.youtube.com/watch?v=fSbBsXbjxPo) (~2022) | [S] |
| Not usable for the jam | [Using UE with Image and Video Generation (Coming Soon)](https://www.youtube.com/watch?v=LGvsShWEH3k): release planned early 2027 | [S] |

The Unreal Fest Chicago 2026 playlist (`PLZlv_N0_O1gbqqvKFsEnkNhjP7iE9PL3N`) is the richest current source, but its item list couldn't be enumerated. A logged-in scan for "AI", "MCP", "PCG", "Gameplay", "UI" and "Audio" is worth 20 minutes before Nov 12 ([playlist](https://www.youtube.com/playlist?list=PLZlv_N0_O1gbqqvKFsEnkNhjP7iE9PL3N)).

## Open questions to verify, with deadlines

**Forum threads to watch (two live copies of the same announcement, 2026-11-05 read):** `…/2843983` (General / Announcements; 34 posts, Oct 22 to Nov 4) and `…/2843973` (16 posts, Oct 22 to Nov 3), both at `https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/<id>`. Links in this file that cite 2843973 are one copy of two; check both. **Re-read both on Nov 10 and again after the Nov 11 kickoff** for staff answers. As of Nov 5 no staff answer exists to any rules question (only the FAQ post and "There is only one MegaJam, but using AI is optional", #21). Questions 5, 6 and 8 below are still open and more people are asking (2843983 #32 covers Shipping vs Development build and Glass Box dev log format; #34 asks about pre-written C++ gameplay modules; #24 asks if the dev log can be uploaded later). The Epic FAQ line "Declare any prompts, scripts, or assets you made before the jam" is met by `stages/00_prep/references/pre-jam-declaration-2026-10-29.md`; keep it current up to Nov 11. **Safe defaults stay until Epic answers:** Development build, no pre-written gameplay code, dev log submitted inside the window, declaration file current.

| # | Question | Why it matters | Where to check | By |
|---|---|---|---|---|
| 1 | ~~Does Epic's Box PDF match the community copy (SHA-256 `5f5022…a2296`)?~~ (resolved 2026-10-29: no, and that's expected — downloaded the live Box PDF directly via curl against Box's `box_download_shared_file` endpoint, confirmed a genuine 14-page PDF (`pdftotext`/`pdfinfo`), SHA-256 `635c3c11ff2ab3edd25dcbe5b00f686ee2594a5b379d22a111b1d55bd994fb63`. Its own embedded Change Log and file metadata (title `..._FINAL_v3AB`, created 2026-10-26) confirm it's the v3 revision — not the v2 original the community hash was taken from. This is the same Oct 26 update (Brazil/Russia/Turkey restricted-jurisdiction changes) RULES.md already incorporated from a 2026-10-27 browser read; the hash now gives that update a verified source instead of just a visual read. Re-check again Nov 10 and Nov 15 AM per the original schedule, since Epic said it would update further.) | Every Rules v2 citation here depends on it | [Box link](https://epicgames.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z) in a browser | Nov 2; again Nov 10 and Nov 15 AM |
| 2 | ~~Is the one-main-plus-one-modifier cap Rule 10 or Rule 13?~~ (resolved 2026-10-28: it's Rule 13 everywhere in this repo now — RULES.md, AGENTS.md and win-plan.md all cite Rule 13 for the cap and Rule 10 only for the Glass Box dev-log requirement; no disagreement found) | Repo files disagree | Rules PDF | Nov 2 |
| 3 | Must entrants opt into modifiers (2023's form asked for "entered modifiers and modifier criteria notes")? Can one entry be considered for Glass Box and Solo Driver/Render Royalty at once? | Decides whether to write modifier notes | itch submission form; forum | Kickoff |
| 4 | Is Windows mandatory under Rule 1(b)'s "packaged for Windows and playable on…" wording? | Android/macOS-only fallback viability | [Forum thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973) (FrostyDog777's question) | Nov 10 |
| 5 | Will Epic answer FrostyDog777's 12 questions (pre-jam tooling, generated content, sourced assets, dev logs, **ideation timing**, build configuration, tool naming)? | Ideation between 11 AM and 9 PM PT on Nov 11; Development vs Shipping | Same thread; daily livestreams | Nov 11 |
| 6 | Is generic gameplay code (e.g., a hit-stop component) "scripts" or "gameplay" under 7(h)? | Determines how much code can be pre-written | Ask in forum; default to *no* | Nov 10 |
| 7 | Can sourced-asset *implementation* still earn points, as in 2023? | Changes the value of Fab freebies | Rules PDF wording of 15(c) | Nov 10 |
| 8 | Is Starter Content, Mixamo or a third-party plugin allowed? | Asset and plugin choices | [Forum thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973) (unanswered) | Nov 10 |
| 9 | Which partners give credits for Meshy Pro (Bridge), how much, how to claim? | Could beat local generation for 3D assets | Kickoff stream; itch community tab ([Epic es-ES](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)) | Nov 11 |
| 10 | ~~Does Epic's Unreal MCP plugin ship and run in the Linux editor build?~~ (resolved 2026-10-27: yes. Verified over raw MCP HTTP against `~/Projects/ue-mcp-verify`; see PLAN.md week-1 gate) | The whole agent architecture | PLAN.md week-1 gate | Nov 2 |
| 11 | ~~Which Blueprint graph tools does `list_toolsets` actually expose?~~ (partly resolved 2026-10-27: `list_toolsets` returned about 50 toolsets and an actor was spawned and edited via ActorTools, see PLAN.md week-1 gate; PLAN.md does not record a Blueprint-graph-tool list, and mock jam 2 found a Blueprint-event-graph Python API wall, see `stages/00_prep/output/mock-jam-findings-2.md`) | Whether EngineWire/GenOrca are needed | Editor | Nov 2 |
| 12 | Is the latest 5.8.x hotfix stable on RX 9070 XT + current CachyOS Mesa? | Editor crashes in jam week | Scratch project with Lumen/Nanite/VSM on; [crash thread](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749) | Nov 2 |
| 13 | ~~Licenses for Modly and foundry-lab inputs/models; Hunyuan3D terms for a US entrant; compatibility with Epic's publicity license (Rule 15(b))~~ (resolved 2026-10-28: see [stages/00_prep/references/license-check-modly-foundrylab.md](../../stages/00_prep/references/license-check-modly-foundrylab.md) — Hunyuan3D-2 needs a Notice file on distribution, free under 1M MAU; **Qwen-Image 2.1, Nexus's current default image model, is non-commercial-only and must not back real jam assets** — switch default to Krea 2 Turbo or SDXL first; UniRig/autoremesher/Wan 2.2/SDXL/Krea all clean) | Asset legality | Each project's license file | Nov 4 |
| 14 | ~~Exact `RunUAT BuildCookRun` flags for Win64 Development + prereqs + archive~~ — **resolved 2026-10-28 by the mock jam**: the flags in `scripts/package-and-push.ps1` work as-is; the real blocker was the `.uproject` file (drop the `Modules` key entirely for a content-only project, blank `EngineAssociation`) — see `stages/00_prep/output/mock-jam-findings.md` | Packaging script | `stages/00_prep/output/mock-jam-findings.md` | Done |
| 15 | Is `Build.sh` UBT syntax on Linux as assumed? `DisableAllScreenMessages`? `RunHardwareBenchmark` in 5.8? | Agent loop and shell polish | Epic docs / test | Mock jam, Nov 7–8 |
| 16 | ~~GitHub LFS quota vs NAS remote~~ (resolved 2026-10-28: GitHub Free gives 10 GiB/month each for LFS storage and bandwidth, metered billing beyond that if a payment method is on file — storage overage without one just blocks new pushes (clones still work via pointer files), bandwidth overage disables LFS until next month. `jf1shh/megajam` is currently 889 KB, nowhere near the limit. Generated binaries (meshes/textures/video) should still go to the NAS remote, not LFS, per the existing `nas offload` convention — keeps this a non-issue through jam week without touching the free tier at all) | Fab or generated binaries could exhaust quota | GitHub billing page | Nov 4 |
| 17 | MetaHuman license in 5.8: MIT (Edge) or free under $1M (metahuman.com)? | Only if MetaHumans are used (not recommended) | [metahuman.com/license](https://www.metahuman.com/en-US/license) | If needed |
| 18 | Does any itch requirement add a cover image or screenshots? | Page completeness | itch submission form | Day 1 test upload |
| 20 | Is the MetaSound SFX Generator's preset-driven output "sourced" or "generated" under Rule 15(c)? | Decides whether SFX score and go in the sourced-asset ledger | Ask in the forum thread (near question 8) | Nov 10 |
| 21 | Exact UE EULA / Epic Content License terms for MetaSound content and the generative-AI input clauses (reportedly no use of Licensed Technology as AI training or prompt input; Fab "NoAI" content must not be fed to Krea or the 3D model as reference). **Training setting: resolved on our side** (owner confirmed 2026-11-01 that Claude's "help improve Claude" setting is OFF). The EULA text itself is still unverified from a primary source (Epic pages returned 403) | Epic's pages returned 403 to the audit; only secondary sources so far | Epic EULA in a browser; owner account settings | Nov 10 |
| 22 | Engine primitives (`/Engine/BasicShapes/Cube`, used by `ue_build_level.py`) and the default UMG font: engine content, not sourced assets? Starter Content, Mixamo, Fab, MetaHuman and plugins stay unanswered (question 8); none are wired into scripts | Ledger completeness | Forum thread | Nov 10 |
| 23 | Krea 2 license §4.2 requires "reasonable and appropriate Content Filter measures"; human review counts. Tick the `human_review` column in `stages/02_build/output/asset-pipeline-log.csv` per concept image | Krea license compliance | Krea license text | Before first real asset |
| 24 | 3D generator: Hunyuan §5(c) territory clause covers outputs (EU, UK, South Korea excluded). **Owner decided 2026-11-01 to replace it with TripoSplat (MIT); 3D generation is disabled in MegaJam until that is wired and live-tested (greybox/hand-made meshes meanwhile).** Open: wire it into `nexus-3d` (hardcodes Hunyuan model ids), live ROCm smoke test, check vertex-color import, ~~check TripoSplat dependency licenses (DINOv3, BiRefNet)~~ (resolved 2026-11-02: TripoSplat wired and live-tested, see `stages/00_prep/references/legal-audit-2026-11-02.md`; BiRefNet MIT; **owner accepted the DINOv3 License 2026-11-02** ("Yes, I accept", relayed by the Master control hub): weights stay local, never shipped; name DINOv3 in any published pipeline write-up (§1b.ii); no military/ITAR use (§1b.v); Meta may amend terms, continued use = acceptance (§8)) | Public itch download and Epic's worldwide publicity license reach those regions | `stages/00_prep/references/license-check-modly-foundrylab.md` | Nov 4 |
| 19 | What did hosts praise in the 2025 winners stream? | The only judge-adjacent signal available | [SsR4mzX9-4o](https://www.youtube.com/watch?v=SsR4mzX9-4o) | Nov 9 |

## Conclusion

The evidence points to a jam that rewards ordinary craft, while the attention goes to AI. The Rules v2 strip AI use out of scoring, double-weight Fun in ties, and zero out sourced assets. Those three clauses together make Jared's agent stack valuable for one specific reason: it can generate *original* scored art and audio fast enough to fill all seven criteria in 93 hours, something a solo human normally can't do. The work therefore splits in two. Before Nov 11 the job is pure plumbing: a Windows build path proven on a clean machine, a stable 5.8.1+ editor on RDNA4, an MCP gate passed, and generation scripts timed per asset. After 9 PM PT on Nov 11, every hour goes to feel, theme and finish, with human review standing between each generated asset and the "AI slop" reading that this jam's audience is primed to apply.

Glass Box is a different contest. The disclosure Epic already demands under Rule 7(h) is also the raw material for the best-dev-log prize, so the honesty that defuses the backlash and the honesty that wins the modifier are the same document. The largest remaining uncertainties are procedural, not creative. Who wins which modifier, whether Windows is mandatory, and where 7(h) draws the code line can each be closed by Nov 10 with a few forum questions and one careful read of the Box PDF. That makes them the cheapest risk reduction left on the calendar.

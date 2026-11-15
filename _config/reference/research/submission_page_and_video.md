# The submission page and the 30-60 s video: requirements, best practice, templates

Research date: 2026-10-29. Method: read the repo rules digest, the two earlier research notes, win-plan submission
checklist, capture-setup and dev-log-entry template; fetched the live itch.io jam page, the Fregward page, itch's
design docs, a presskit.gg trailer guide and a Derek Lieu search summary. The Box rules PDF did **not** load this
time (WebFetch returned only the word "Box"), so rule numbers below come from `RULES.md` (read from the PDF on
2026-10-27/29), not re-quoted.

**Status: research notes only.** No gameplay, levels or art are built or implied here; templates and prompt
libraries are fine before the window, content and art are not (Rule 7(h)).

**Takeaway.** The video is the only presentation item the rules make mandatory; the page, screenshots and dev log are
not required (the dev log only for Glass Box) and none is a scoring criterion. Judges still need a way to see the
game fast, so treat the video as the judge's front door (inference): gameplay in the first 5 seconds, theme visible
by second 15, readable on mute, ending on the title. Build the itch page around a 5-second "what is this, how do I
play it" scan, keep the zip small, and write the dev log as a dated, honest AI ledger.

## 1. What the rules require, and whether it is scored

| Finding | Confidence | Basis | Source |
| --- | --- | --- | --- |
| Entry data: team name, each member's name and Epic-linked email, game name, one named Team Owner (Rule 1(c)). | High | official rules | RULES.md; itch jam page |
| Video: 30-60 s of recorded gameplay, 1920x1080 or higher (Rules 1(e), 7(c)). Jam page repeats 30-60 s and tips "show gameplay in the first five seconds". | High | official rules, Epic page | RULES.md; [itch jam page](https://itch.io/jam/2026-epic-ai-megajam) |
| Dev log link is optional except for Glass Box (Rule 10). Jam page: "keep notes as you build". Digest says it is submitted during the contest period. | High | official rules, Epic page | RULES.md; itch jam page |
| Sourced (non-original) assets must be licensed and listed (Rules 1(d), 15(c)); they "will not be reviewed or scored". AI-generated content is not a sourced asset (15(c)). | High | official rules | RULES.md |
| Package: Development build, zip `TeamName_GameName`, under 1 GB or use butler / Blendo uploader, hosted on our own itch account then submitted to the jam. Unpackaged projects not accepted. | High | Epic page | itch jam page |
| Must run with no extra software (7(f)); English everywhere including video and entry info (7(i)); theme must be demonstrated (7(g)). | High | official rules | RULES.md |
| Scored: only the 7 criteria, 1-5 each (Rule 9). No criterion is "presentation", "video" or "page". Disclosed AI extent is context only. | High | official rules | RULES.md; itch jam page |
| Screenshots, description length, cover image and an AI-disclosure field are **not** required by anything we found; the digest lists no screenshot rule. | Medium | official rules (absence) | RULES.md; [WindowsForum](https://windowsforum.com/news/epic-ai-megajam-2026-ai-is-optional-65k-cash-prizes-and-unreal-engine-submission-rules.449768/) via earlier note |
| Pre-jam AI tooling must be declared (7(h)); Epic may ask for it or its version history. Not a field on the form as far as known. | Medium | official rules | RULES.md |
| Human must submit, not an agent (Rule 17). | High | official rules | RULES.md |
| IP warranty / indemnity wording on submissions: **not checked** this pass (PDF did not load). Digest only records that we keep ownership and Epic gets a non-exclusive publicity licence (Rules 2, 15(b)). | Low | inference | RULES.md |

Where the repo already covers this: the win-plan Submission checklist (lines 152-168) has every disqualification
item; `templates/dev-log-entry.md` has the nightly dev-log skeleton; `capture-setup.md` has OBS settings. This note
adds the page, video outline and the final "how it was built" dev log.

## 2. What past entries put on their pages

| Finding | Confidence | Basis | Source |
| --- | --- | --- | --- |
| Fregward (2022 1st place) page: cover, warnings, "How to play" tips, premise paragraph, one 72 MB zip, five screenshots at the bottom, **no video, no GIF, no controls list, no install steps**. It won on design, not presentation. | High | past entry | [Fregward](https://honestdan.itch.io/fregward) |
| Fregward's "How to play" heading sat above an empty line, then five tips; its known-bug warning was above the fold. Honest warnings up top did not stop it winning. | High | past entry | Fregward page |
| 2025 winners list, other 2022-2025 pages and any winner's video could not be retrieved (Epic news page returned 403, results page 404). Per-entry structure of recent winners is therefore **unknown**. | Medium | past entry (gap) | [Epic 2025 post](https://www.unrealengine.com/news/epic-megajam-2025) failed |
| Earlier note: several 1st/2nd place games also won craft modifiers, so one strong visual identity travels from video to score. | Low | inference | jam_winning_strategy note |
| Post-jam devlog posts (Bit Barrage 2021, JungleFall 2020) are postmortems about scope and cut features, not marketing. Useful honesty tone for our log. | Medium | past entry | [Bit Barrage](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem) |

## 3. Trailer and gameplay-video practice

| Finding | Confidence | Basis | Source |
| --- | --- | --- | --- |
| Open on the most compelling gameplay; no logo, fade from black, narration or slow establishing shot in the first 5 s. Move the logo to the end card. | Medium | practitioner guide | [presskit.gg guide](https://presskit.gg/field-guides/game-trailers-screenshots-guide) |
| Timed shape for gameplay trailers: hook 0-5 s, core loop 5-25 s, escalation 25-45 s, title end card last 5-10 s. Guide targets 60-90 s for store trailers; we are capped at 60 s, so compress. | Medium | practitioner guide | presskit.gg |
| Many viewers watch muted: test on mute, text cards at 5 words or fewer, each on screen at most 3 s. | Medium | practitioner guide | presskit.gg (quotes Valve) |
| Derek Lieu: show the game's main unique feature as early as possible then expand it; list the game's verbs first and build the cut around them; "show the dream, not the job". Second-hand summary, his own guide not reached. | Medium | practitioner guide | [Lieu summary via search](https://www.pcgamer.com/uk/the-art-of-making-effective-game-trailers); derek-lieu.com not fetched |
| First trailers should be "gameplay gameplay gameplay"; story supports gameplay. A developer-commentary trailer reads as gameplay when muted. | Medium | practitioner guide | [GameDiscoverCo, Sep 2022](https://newsletter.gamediscover.co/p/game-trailers-breaking-down-a-key) (via earlier note) |
| Gameplay vs cinematic ratio: no hard number found. The consistent advice is mostly real gameplay, with at most one short cinematic beat. Our rule: 85-90 percent real build footage (inference). Rule 7(c) says "recorded gameplay", so avoid pre-rendered cutscenes. | Medium | inference | Rule 7(c); guides above |
| Showing the theme: caption it once with a ≤5-word card tied to an on-screen mechanic, not a lore dump. | Low | inference | presskit.gg text rules |

## 4. itch.io page practice

| Finding | Confidence | Basis | Source |
| --- | --- | --- | --- |
| Recommended cover size 630x500 (3 MB file cap per a community post; confirm in the upload dialog). Cover is hidden on the game page once screenshots exist, so upload it to screenshots too if wanted. | Medium | practitioner guide | [itch forum posts](https://itch.io/post/776268/view-in-topic) via search |
| Itch's own design docs give no pixel sizes. The banner is "probably the most important graphic part"; it can be an animated GIF. Suggested description contents: controls, recommended specs, story summary, feature list, development status, links, credits. Use Header 2 for section titles. | High | practitioner guide | [itch design docs](https://itch.io/docs/creators/design) |
| YouTube/Vimeo trailers must be public (an unlisted link may fail the embed; verify). Win-plan says "unlisted"; Epic's form link is separate from the page embed. | Low | inference | itch design docs; win-plan |
| Screenshots: 6-8 varied, 1920x1080 16:9, core gameplay first, one-sentence captions, no title-screen shot, animated GIFs of 2-4 s inside the description, not the carousel. Steam-oriented; transferable. | Medium | practitioner guide | presskit.gg; jam_winning_strategy note |
| Page copy that serves both judges and testers: "How to play" and controls in the first screen, build size and install steps visible, known bugs stated honestly. | Medium | inference | Fregward; itch docs |

## 5. Dev log (Glass Box) and honest AI disclosure

| Finding | Confidence | Basis | Source |
| --- | --- | --- | --- |
| Glass Box is the $2,500 dev-log modifier, described in press as showing AI tool use; Epic's scoring wording for it was not found. Rule 10 is the governing text. | Medium | official rules, Epic page | RULES.md; Inven (earlier note) |
| AI extent is context only for the 7 criteria (Rule 9), so honesty costs nothing in the main score and is the whole point of Glass Box. | High | official rules | RULES.md |
| Nothing found on what Epic's panel rewards in a dev log. Best available: dated, specific, shows failures and the human decisions. | Low | inference | jam_winning_strategy note |

Structure that fits both Rule 10 and honesty (extends `templates/dev-log-entry.md`):
1. Nightly post (existing template) plus one **prompt-to-result pair**: what we asked, what came back, what we changed by hand.
2. A **failure or cut** line per day. 3. The final "how it was built" post carries the ledger table in the template below.
4. Mark each item as hand-made, AI-generated, AI-assisted or sourced. Never claim hand-made for AI output.

## 6. Itch page template (fill in the blanks)

Pre-window safe: this is empty scaffolding. Do not fill in game specifics before 9 PM PT Nov 11.

```markdown
[Banner / cover 630x500: one hero frame, no text beyond the title]
# {GAME_NAME}  (made solo for the 2026 Epic AI MegaJam, Unreal Engine 5.8)

**{ONE-LINE PITCH: verb + hook, 12 words max}**   Theme: "{THEME}" — {HOW_THEME_SHAPES_GAMEPLAY, one sentence}

[Embedded video, 30-60 s, same as submitted link]

## How to play
- **Move:** {KEYS / STICK}   **{ACTION_1}:** {KEY}   **{ACTION_2}:** {KEY}   **Restart:** {KEY}   **Quit:** {KEY}
- **Goal:** {ONE SENTENCE}. Round length: about {N} minutes. Controller: {YES/NO}.
- Tip: {THE ONE THING A FIRST-TIME PLAYER MISSES}

## Download and run (Windows 10/11)
1. Download `{TeamName_GameName}.zip` ({SIZE} MB, Development build). 2. Unzip anywhere (not inside the zip).
3. Run `{EXE_NAME}.exe`. No installs needed. 4. If SmartScreen warns, choose More info, then Run anyway.
Recommended: {GPU/RAM}. Tested on: {DEVICES, e.g. Legion Go S, desktop}. Target {FPS} at {RES}.

## Known issues
- {ISSUE_1 and workaround}  - {ISSUE_2}  (state honestly; Fregward did and still won)

## About
{3-4 sentences: premise, what you do, what makes it different. Lead with the mechanic.}

[Screenshots 6, 16:9, captioned: 1 core gameplay, 2 theme moment, 3 variety, 4 variety, 5 payoff, 6 level overview]
[Optional 2-4 s GIF of the core loop]

## How it was built (AI and sourcing disclosure)
Built solo in 4 days. Dev log: {LINK}. Pre-jam (tools only, Rule 7(h)): {MCP config, agent configs, prompt library, scripts; tag `pre-jam-tooling`}.

| Item | Hand-made / AI-generated / AI-assisted / Sourced | Tool and model | Human edits |
| --- | --- | --- | --- |
| Code ({SYSTEMS}) | | | |
| 3D models | | | |
| Textures / materials | | | |
| Music / SFX / VO | | | |
| Level layout | | | |
| Sourced assets (Rule 15(c)): {NAME, LICENSE, URL} | Sourced | n/a | |

## Credits and links
{NAME, Epic account handle}. Engine: Unreal Engine 5.8 (Unreal Engine logo only, per branding rules). {Contact}.
```

## 7. Video outline: 60 s target (fits the 30-60 s window; cut to 45 if the game is thin)

Never exceed 60 s; aim for 57 s so encoder rounding stays inside Rule 7(c). Record at 1920x1080, 60 fps.

| Time | Shot | Notes |
| --- | --- | --- |
| 0:00-0:05 | Hook: best moment of actual play, already mid-action | No logo, no black fade, no title card. Must read on mute |
| 0:05-0:15 | Core loop: the main verb, clean, one continuous take | Card 1 (≤5 words): the verb. Theme shown by the mechanic here |
| 0:15-0:22 | Theme beat: where the theme changes how you play | Card 2: theme name or phrase, ≤3 s on screen |
| 0:22-0:35 | Variety 1: second mechanic or enemy or environment | Cut every 2-3 s; show UI sparingly |
| 0:35-0:47 | Escalation: pressure, speed, or scale up | Peak of the music (original or licensed, listed) |
| 0:47-0:53 | Payoff: win, boss, reveal, or best-looking vista | The one place a slow shot is allowed |
| 0:53-0:60 | End card: title, "Made solo in 4 days", platform line, itch URL if short | ≤3 text cards total across the video |

Shot list to prep NOW (setup only; footage after the window opens):
- [ ] OBS profile applied on the Legion Go S (capture-setup step 2 is still open), test recording done.
- [ ] Replay-buffer hotkey set; second hotkey for start/stop; clip folder `captures/YYYYMMDD/` agreed.
- [ ] Editor choice settled (Resolve, Kdenlive or OBS only); a 60 s timeline template with markers at the times above.
- [ ] Caption style fixed (font, size, safe margin); test video on mute and on a phone.
- [ ] Loudness target set (about -14 LUFS) and a placeholder music slot; sound that is AI-generated or sourced goes in the ledger.
- [ ] Record gameplay "as you go" each day (10 clips, 5-10 s) so Sunday is editing, not hunting.
- [ ] Final export check: 1080p, under 60.0 s, plays from the YouTube link logged out.

## Gaps

- Rule PDF not re-fetched this pass: warranty/indemnity/IP wording unverified.
- No recent winner's page or video was retrieved (Epic news 403, itch results 404), so "strongest past entries" rests on Fregward alone.
- Derek Lieu's own guide, GDC trailer talks and Game Developer articles not read; Lieu points are second hand.
- Epic's wording for what the Glass Box panel rewards is unknown.
- Whether an itch.io GIF in the description hosts well, and whether unlisted YouTube embeds work on itch, not tested.

## Next checks before Nov 11

1. Re-open the Box PDF (browser) on Nov 10: read Rules 1, 7, 10, 15 and the warranty/indemnity clause; quote any change.
2. Pull the 2025 winners via the Epic blog in a browser and open the top five pages and videos; fill section 2.
3. Read derek-lieu.com "How to Make a Trailer" directly; adjust the outline.
4. Create the itch project and upload a 100 MB test zip and butler channel early; confirm the cover size in the upload dialog and test a YouTube embed.
5. Finish the OBS wizard on the Legion Go S and record a test clip of the mock-jam build (Nov 7-8).

## Caveats

- Video length and resolution come from the rules; every other number (screenshot count, GIF length, cover size, text-card limits) is practitioner advice, much of it Steam-oriented.
- Nothing here shows the judges watch the video first; that is an inference from the required field and short review time.
- Third-party summaries (presskit.gg, search-derived) may misattribute credits; weight them below the official rules.
- Treat the template as scaffolding; do not pre-write game-specific copy before the window (Rule 7(h)).

# Outside strategy prompts (ChatGPT, Grok, Gemini)

Written 2026-10-27. Three ready-to-paste prompts that ask other models for an independent jam
strategy, each with a different job so the answers disagree usefully:

| Model | Role | What it brings |
| --- | --- | --- |
| ChatGPT | The judge | Evidence from past MegaJam and big-jam winners |
| Grok | The contrarian | X search, a safe plan vs. a high-risk plan, standing out among AI-made entries |
| Gemini | The technical producer | Feasibility in 93 hours, hour estimates, technical traps, a Nov 10 go/no-go list |
| Claude | The game designer | Fun Factor first: theme-to-mechanic method, core loops, level structure, juice, a concept worksheet |

All four share the same brief and the same 12 numbered sections (Gemini and Claude add a 13th),
so the answers line up section by section.

How to use: copy one whole prompt below into its model. Save each answer in this folder as
`chatgpt.md`, `grok.md`, `gemini.md` and `claude.md`, then compare them against `stages/00_prep/references/win-plan.md`.
Claude helped write `stages/00_prep/references/win-plan.md`, so its prompt runs in a fresh agent that doesn't read
this repo.

This is a prompt library, which Rule 7(h) allows before the contest period. It holds no
gameplay, level or art content. List it in the pre-jam declaration.

## ChatGPT

```text
YOUR ROLE: THE JUDGE. Use web search. Think like a judge who plays hundreds of jam entries for a few minutes each. Research past Epic MegaJam winners (2019–2025) and other big jams (GMTK, Ludum Dare): what the top entries had in common, what judges praised, and what lost points. Base your advice on that evidence and name specific winning games and what they did. Where the evidence says my plan is wrong, say so plainly.

I'm entering the 2026 Epic AI MegaJam on itch.io and want your independent strategy. I'm asking two other AI models with different briefs and will compare all three, so give me your own honest view, not a safe consensus.

THE JAM
- Runs Wed Nov 11, 2026, 9:00 PM PT to Sun Nov 15, 5:59 PM PT (about 93 hours). The theme is revealed at the kickoff livestream on Nov 11 at 11 AM PT. I don't know it yet.
- I'm on the Unreal Engine track (not UEFN). The entry must be a packaged build that runs on Windows 10/11 with no extra software, zipped under 1 GB, plus a 30–60 second gameplay video at 1080p or higher. Everything in English, Teen-rated, no third-party IP or trademarks (Unreal logo only). It must use the theme and go beyond Epic's tutorials and starter templates.
- Before the jam starts, only tools, agent configs, MCP settings, prompt libraries and scripts may exist. No gameplay, levels or art. Epic may check my git history.
- AI is allowed for code, assets and in-game systems. AI-generated assets count as my own original work. Store assets (Fab etc.) are allowed but are not scored at all.
- Judging: 7 criteria, 5 points each, equal weight: Ambition & Innovation, Use of Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. Disclosed AI use is "context only" and doesn't move scores. Ties are re-scored with Fun Factor counted double.
- Prizes: Best Overall (Unreal) $7,500 / $5,000 / $2,500. Each entry can win at most one main prize and one modifier prize. Modifiers include Glass Box ($2,500, best dev log), Solo Driver ($2,500), Render Royalty ($2,500) and Pocket Powerhouse ($2,500); check the official rules for what each requires. Epic may later invite top entries to Development Continuation Grants of up to $50,000.

ME AND MY SETUP
- Solo, plus AI agents.
- My experience: deep knowledge of Unreal's file formats and older engine content (I'm building a Rust tool that converts asset packages across UE1–UE5, and I've ported characters into UT2004), but little hands-on UE5 editor time. I haven't shipped a UE5 game, and so far I've only set up the Unreal MCP in a scratch project. Other game dev: I shipped a small browser platformer (plain HTML/JS) and I'm building an agent-driven Unity ARPG prototype with spec and test gates. I'm an experienced software developer, strong with AI agents, and I run my own local image, 3D and music generation pipeline.
- Main machine: a Linux (CachyOS) desktop with an AMD RX 9070 XT (16 GB) running the UE 5.8 Linux editor. A Lenovo Legion Go S with Windows 11 packages the Windows builds (Unreal can't package Windows from Linux) and doubles as a low-end test device.
- Claude Code is the lead agent and drives the editor through Epic's Unreal MCP plugin (experimental, runs one tool call at a time). Other agents write C++ and Blueprint in files.
- A local AI asset pipeline on the same GPU: text-to-image (Qwen-Image), image-to-3D (Modly) with a remesh-and-bake step, and music (ACE-Step). The editor and the generators can't share the GPU, so generation runs in batches while the editor is closed.

MY CURRENT PLAN (challenge it)
- Target: top 3 Best Overall (Unreal) plus the Glass Box modifier, with Solo Driver as the fallback.
- Pick the concept on paper by 3 PM PT Nov 11: 10 readings of the theme, filter to 3, score each on the 7 criteria plus feasibility, write a one-page design doc.
- Avoid multiplayer, open worlds, dialogue trees and humanoid heroes with complex animation (AI rigs are weak). Prefer a creature, vehicle, object or abstract hero, stylized visuals, and a top-down or third-person camera.
- Get every criterion to a 4, then push two to a 5. Ambition comes from breadth (a bigger hand-built level, more enemy types), not a fragile tech gimmick.
- Daily gates: playable greybox on night 0; Windows build #1 on day 1; a full start-to-end run on day 2, played by someone else; art, audio, UI and juice on day 3 with feature freeze at 10 PM; fixes only on day 4; submitted by 4:30 PM PT (90 minutes of buffer).
- Work in feature slices of 2 hours or less, each with a done-test and my own playtest. A cut list written on day 1. 6 hours of sleep a night.
- Pre-jam prep: packaging script, asset-pipeline scripts, prompt library, QA harness (screenshots and fps), OBS setup, dev log tooling, and a 24-hour mock jam on a made-up theme.

OUTPUT FORMAT (use these exact headings so I can compare answers)
1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it
2. Your winning strategy in one paragraph
3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why
4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there
5. Where AI agents help most and where they'll hurt me
6. Schedule: your version of the 4 days, with gates
7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like
8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play
9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules
10. Top 10 risks with mitigations
11. One thing you'd do that most entrants won't
12. What you're least sure about, and what I should verify

Be specific and concrete. Tell me where you disagree with my plan; agreement only helps if you explain why it's right. Cite sources for factual claims about the jam or past winners, and say when you're guessing.

Write the whole answer as one Markdown document I can save as a file. Start it with the line "# MegaJam strategy — <your model name and version>, <today's date>", use "##" for each numbered section, put sources as inline links, and give it to me as a downloadable .md file if you can.
```

## Grok

```text
YOUR ROLE: THE CONTRARIAN. Argue against my plan wherever you can make a real case. Use X search: look for posts from Epic and Unreal Engine accounts, past MegaJam winners and judges, and current chatter about the 2026 jam (rule clarifications, sponsor AI credits, what people are planning, what's already overdone). In section 2, give me two strategies side by side, a safe one and a high-risk/high-reward one, and tell me which you'd pick and why. Also tell me how an AI-heavy solo entry looks to judges in 2026, and how to stand out when many entries will be AI-made.

I'm entering the 2026 Epic AI MegaJam on itch.io and want your independent strategy. I'm asking two other AI models with different briefs and will compare all three, so give me your own honest view, not a safe consensus.

THE JAM
- Runs Wed Nov 11, 2026, 9:00 PM PT to Sun Nov 15, 5:59 PM PT (about 93 hours). The theme is revealed at the kickoff livestream on Nov 11 at 11 AM PT. I don't know it yet.
- I'm on the Unreal Engine track (not UEFN). The entry must be a packaged build that runs on Windows 10/11 with no extra software, zipped under 1 GB, plus a 30–60 second gameplay video at 1080p or higher. Everything in English, Teen-rated, no third-party IP or trademarks (Unreal logo only). It must use the theme and go beyond Epic's tutorials and starter templates.
- Before the jam starts, only tools, agent configs, MCP settings, prompt libraries and scripts may exist. No gameplay, levels or art. Epic may check my git history.
- AI is allowed for code, assets and in-game systems. AI-generated assets count as my own original work. Store assets (Fab etc.) are allowed but are not scored at all.
- Judging: 7 criteria, 5 points each, equal weight: Ambition & Innovation, Use of Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. Disclosed AI use is "context only" and doesn't move scores. Ties are re-scored with Fun Factor counted double.
- Prizes: Best Overall (Unreal) $7,500 / $5,000 / $2,500. Each entry can win at most one main prize and one modifier prize. Modifiers include Glass Box ($2,500, best dev log), Solo Driver ($2,500), Render Royalty ($2,500) and Pocket Powerhouse ($2,500); check the official rules for what each requires. Epic may later invite top entries to Development Continuation Grants of up to $50,000.

ME AND MY SETUP
- Solo, plus AI agents.
- My experience: deep knowledge of Unreal's file formats and older engine content (I'm building a Rust tool that converts asset packages across UE1–UE5, and I've ported characters into UT2004), but little hands-on UE5 editor time. I haven't shipped a UE5 game, and so far I've only set up the Unreal MCP in a scratch project. Other game dev: I shipped a small browser platformer (plain HTML/JS) and I'm building an agent-driven Unity ARPG prototype with spec and test gates. I'm an experienced software developer, strong with AI agents, and I run my own local image, 3D and music generation pipeline.
- Main machine: a Linux (CachyOS) desktop with an AMD RX 9070 XT (16 GB) running the UE 5.8 Linux editor. A Lenovo Legion Go S with Windows 11 packages the Windows builds (Unreal can't package Windows from Linux) and doubles as a low-end test device.
- Claude Code is the lead agent and drives the editor through Epic's Unreal MCP plugin (experimental, runs one tool call at a time). Other agents write C++ and Blueprint in files.
- A local AI asset pipeline on the same GPU: text-to-image (Qwen-Image), image-to-3D (Modly) with a remesh-and-bake step, and music (ACE-Step). The editor and the generators can't share the GPU, so generation runs in batches while the editor is closed.

MY CURRENT PLAN (challenge it)
- Target: top 3 Best Overall (Unreal) plus the Glass Box modifier, with Solo Driver as the fallback.
- Pick the concept on paper by 3 PM PT Nov 11: 10 readings of the theme, filter to 3, score each on the 7 criteria plus feasibility, write a one-page design doc.
- Avoid multiplayer, open worlds, dialogue trees and humanoid heroes with complex animation (AI rigs are weak). Prefer a creature, vehicle, object or abstract hero, stylized visuals, and a top-down or third-person camera.
- Get every criterion to a 4, then push two to a 5. Ambition comes from breadth (a bigger hand-built level, more enemy types), not a fragile tech gimmick.
- Daily gates: playable greybox on night 0; Windows build #1 on day 1; a full start-to-end run on day 2, played by someone else; art, audio, UI and juice on day 3 with feature freeze at 10 PM; fixes only on day 4; submitted by 4:30 PM PT (90 minutes of buffer).
- Work in feature slices of 2 hours or less, each with a done-test and my own playtest. A cut list written on day 1. 6 hours of sleep a night.
- Pre-jam prep: packaging script, asset-pipeline scripts, prompt library, QA harness (screenshots and fps), OBS setup, dev log tooling, and a 24-hour mock jam on a made-up theme.

OUTPUT FORMAT (use these exact headings so I can compare answers)
1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it
2. Your winning strategy in one paragraph
3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why
4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there
5. Where AI agents help most and where they'll hurt me
6. Schedule: your version of the 4 days, with gates
7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like
8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play
9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules
10. Top 10 risks with mitigations
11. One thing you'd do that most entrants won't
12. What you're least sure about, and what I should verify

Be specific and concrete. Tell me where you disagree with my plan; agreement only helps if you explain why it's right. Cite sources for factual claims about the jam or past winners, and say when you're guessing.

Write the whole answer as one Markdown document I can save as a file. Start it with the line "# MegaJam strategy — <your model name and version>, <today's date>", use "##" for each numbered section, put sources as inline links, and give it to me as a downloadable .md file if you can.
```

## Gemini

```text
YOUR ROLE: THE TECHNICAL PRODUCER. Your job is to tell me whether this can actually be built in 93 hours. Use search and YouTube: past winners' dev logs and breakdowns, UE 5.8 packaging and performance on low-end Windows handhelds, Epic's Unreal MCP docs, and how image-to-3D assets hold up in Unreal. Give honest hour estimates for the asset pipeline (AI image → 3D → in-game with good materials). Call out technical traps: Linux editor vs. Windows packaging, Lumen/Nanite on a handheld, shader-compile hitches, build size, plugin and MCP failures. Tell me exactly what my mock jam should test. After section 12, add section 13: a technical go/no-go checklist for Nov 10.

I'm entering the 2026 Epic AI MegaJam on itch.io and want your independent strategy. I'm asking two other AI models with different briefs and will compare all three, so give me your own honest view, not a safe consensus.

THE JAM
- Runs Wed Nov 11, 2026, 9:00 PM PT to Sun Nov 15, 5:59 PM PT (about 93 hours). The theme is revealed at the kickoff livestream on Nov 11 at 11 AM PT. I don't know it yet.
- I'm on the Unreal Engine track (not UEFN). The entry must be a packaged build that runs on Windows 10/11 with no extra software, zipped under 1 GB, plus a 30–60 second gameplay video at 1080p or higher. Everything in English, Teen-rated, no third-party IP or trademarks (Unreal logo only). It must use the theme and go beyond Epic's tutorials and starter templates.
- Before the jam starts, only tools, agent configs, MCP settings, prompt libraries and scripts may exist. No gameplay, levels or art. Epic may check my git history.
- AI is allowed for code, assets and in-game systems. AI-generated assets count as my own original work. Store assets (Fab etc.) are allowed but are not scored at all.
- Judging: 7 criteria, 5 points each, equal weight: Ambition & Innovation, Use of Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. Disclosed AI use is "context only" and doesn't move scores. Ties are re-scored with Fun Factor counted double.
- Prizes: Best Overall (Unreal) $7,500 / $5,000 / $2,500. Each entry can win at most one main prize and one modifier prize. Modifiers include Glass Box ($2,500, best dev log), Solo Driver ($2,500), Render Royalty ($2,500) and Pocket Powerhouse ($2,500); check the official rules for what each requires. Epic may later invite top entries to Development Continuation Grants of up to $50,000.

ME AND MY SETUP
- Solo, plus AI agents.
- My experience: deep knowledge of Unreal's file formats and older engine content (I'm building a Rust tool that converts asset packages across UE1–UE5, and I've ported characters into UT2004), but little hands-on UE5 editor time. I haven't shipped a UE5 game, and so far I've only set up the Unreal MCP in a scratch project. Other game dev: I shipped a small browser platformer (plain HTML/JS) and I'm building an agent-driven Unity ARPG prototype with spec and test gates. I'm an experienced software developer, strong with AI agents, and I run my own local image, 3D and music generation pipeline.
- Main machine: a Linux (CachyOS) desktop with an AMD RX 9070 XT (16 GB) running the UE 5.8 Linux editor. A Lenovo Legion Go S with Windows 11 packages the Windows builds (Unreal can't package Windows from Linux) and doubles as a low-end test device.
- Claude Code is the lead agent and drives the editor through Epic's Unreal MCP plugin (experimental, runs one tool call at a time). Other agents write C++ and Blueprint in files.
- A local AI asset pipeline on the same GPU: text-to-image (Qwen-Image), image-to-3D (Modly) with a remesh-and-bake step, and music (ACE-Step). The editor and the generators can't share the GPU, so generation runs in batches while the editor is closed.

MY CURRENT PLAN (challenge it)
- Target: top 3 Best Overall (Unreal) plus the Glass Box modifier, with Solo Driver as the fallback.
- Pick the concept on paper by 3 PM PT Nov 11: 10 readings of the theme, filter to 3, score each on the 7 criteria plus feasibility, write a one-page design doc.
- Avoid multiplayer, open worlds, dialogue trees and humanoid heroes with complex animation (AI rigs are weak). Prefer a creature, vehicle, object or abstract hero, stylized visuals, and a top-down or third-person camera.
- Get every criterion to a 4, then push two to a 5. Ambition comes from breadth (a bigger hand-built level, more enemy types), not a fragile tech gimmick.
- Daily gates: playable greybox on night 0; Windows build #1 on day 1; a full start-to-end run on day 2, played by someone else; art, audio, UI and juice on day 3 with feature freeze at 10 PM; fixes only on day 4; submitted by 4:30 PM PT (90 minutes of buffer).
- Work in feature slices of 2 hours or less, each with a done-test and my own playtest. A cut list written on day 1. 6 hours of sleep a night.
- Pre-jam prep: packaging script, asset-pipeline scripts, prompt library, QA harness (screenshots and fps), OBS setup, dev log tooling, and a 24-hour mock jam on a made-up theme.

OUTPUT FORMAT (use these exact headings so I can compare answers)
1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it
2. Your winning strategy in one paragraph
3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why
4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there
5. Where AI agents help most and where they'll hurt me
6. Schedule: your version of the 4 days, with gates
7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like
8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play
9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules
10. Top 10 risks with mitigations
11. One thing you'd do that most entrants won't
12. What you're least sure about, and what I should verify

Be specific and concrete. Tell me where you disagree with my plan; agreement only helps if you explain why it's right. Cite sources for factual claims about the jam or past winners, and say when you're guessing.

Write the whole answer as one Markdown document I can save as a file. Start it with the line "# MegaJam strategy — <your model name and version>, <today's date>", use "##" for each numbered section, put sources as inline links, and give it to me as a downloadable .md file if you can.
```

## Claude

```text
YOUR ROLE: THE GAME DESIGNER. Focus on what makes a jam game fun in the few minutes a judge gives it. Fun Factor breaks ties, so treat it as the criterion that matters most. Use web search to study the design of past MegaJam and big-jam winners: their core verbs, game feel, how they taught the player in the first minute, and how they ended. Give me a design toolkit I can use the moment the theme drops: a method for turning a theme into a mechanic, core-loop patterns that fit 93 hours and AI-made assets, a level structure, and a juice checklist. You helped write my current plan in an earlier session; don't defend it, judge it fresh. After section 12, add section 13: a one-page concept worksheet I can fill in on Nov 11 before the jam opens.

I'm entering the 2026 Epic AI MegaJam on itch.io and want your independent strategy. I'm asking two other AI models with different briefs and will compare all three, so give me your own honest view, not a safe consensus.

THE JAM
- Runs Wed Nov 11, 2026, 9:00 PM PT to Sun Nov 15, 5:59 PM PT (about 93 hours). The theme is revealed at the kickoff livestream on Nov 11 at 11 AM PT. I don't know it yet.
- I'm on the Unreal Engine track (not UEFN). The entry must be a packaged build that runs on Windows 10/11 with no extra software, zipped under 1 GB, plus a 30–60 second gameplay video at 1080p or higher. Everything in English, Teen-rated, no third-party IP or trademarks (Unreal logo only). It must use the theme and go beyond Epic's tutorials and starter templates.
- Before the jam starts, only tools, agent configs, MCP settings, prompt libraries and scripts may exist. No gameplay, levels or art. Epic may check my git history.
- AI is allowed for code, assets and in-game systems. AI-generated assets count as my own original work. Store assets (Fab etc.) are allowed but are not scored at all.
- Judging: 7 criteria, 5 points each, equal weight: Ambition & Innovation, Use of Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. Disclosed AI use is "context only" and doesn't move scores. Ties are re-scored with Fun Factor counted double.
- Prizes: Best Overall (Unreal) $7,500 / $5,000 / $2,500. Each entry can win at most one main prize and one modifier prize. Modifiers include Glass Box ($2,500, best dev log), Solo Driver ($2,500), Render Royalty ($2,500) and Pocket Powerhouse ($2,500); check the official rules for what each requires. Epic may later invite top entries to Development Continuation Grants of up to $50,000.

ME AND MY SETUP
- Solo, plus AI agents.
- My experience: deep knowledge of Unreal's file formats and older engine content (I'm building a Rust tool that converts asset packages across UE1–UE5, and I've ported characters into UT2004), but little hands-on UE5 editor time. I haven't shipped a UE5 game, and so far I've only set up the Unreal MCP in a scratch project. Other game dev: I shipped a small browser platformer (plain HTML/JS) and I'm building an agent-driven Unity ARPG prototype with spec and test gates. I'm an experienced software developer, strong with AI agents, and I run my own local image, 3D and music generation pipeline.
- Main machine: a Linux (CachyOS) desktop with an AMD RX 9070 XT (16 GB) running the UE 5.8 Linux editor. A Lenovo Legion Go S with Windows 11 packages the Windows builds (Unreal can't package Windows from Linux) and doubles as a low-end test device.
- Claude Code is the lead agent and drives the editor through Epic's Unreal MCP plugin (experimental, runs one tool call at a time). Other agents write C++ and Blueprint in files.
- A local AI asset pipeline on the same GPU: text-to-image (Qwen-Image), image-to-3D (Modly) with a remesh-and-bake step, and music (ACE-Step). The editor and the generators can't share the GPU, so generation runs in batches while the editor is closed.

MY CURRENT PLAN (challenge it)
- Target: top 3 Best Overall (Unreal) plus the Glass Box modifier, with Solo Driver as the fallback.
- Pick the concept on paper by 3 PM PT Nov 11: 10 readings of the theme, filter to 3, score each on the 7 criteria plus feasibility, write a one-page design doc.
- Avoid multiplayer, open worlds, dialogue trees and humanoid heroes with complex animation (AI rigs are weak). Prefer a creature, vehicle, object or abstract hero, stylized visuals, and a top-down or third-person camera.
- Get every criterion to a 4, then push two to a 5. Ambition comes from breadth (a bigger hand-built level, more enemy types), not a fragile tech gimmick.
- Daily gates: playable greybox on night 0; Windows build #1 on day 1; a full start-to-end run on day 2, played by someone else; art, audio, UI and juice on day 3 with feature freeze at 10 PM; fixes only on day 4; submitted by 4:30 PM PT (90 minutes of buffer).
- Work in feature slices of 2 hours or less, each with a done-test and my own playtest. A cut list written on day 1. 6 hours of sleep a night.
- Pre-jam prep: packaging script, asset-pipeline scripts, prompt library, QA harness (screenshots and fps), OBS setup, dev log tooling, and a 24-hour mock jam on a made-up theme.

OUTPUT FORMAT (use these exact headings so I can compare answers)
1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it
2. Your winning strategy in one paragraph
3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why
4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there
5. Where AI agents help most and where they'll hurt me
6. Schedule: your version of the 4 days, with gates
7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like
8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play
9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules
10. Top 10 risks with mitigations
11. One thing you'd do that most entrants won't
12. What you're least sure about, and what I should verify

Be specific and concrete. Tell me where you disagree with my plan; agreement only helps if you explain why it's right. Cite sources for factual claims about the jam or past winners, and say when you're guessing.

Write the whole answer as one Markdown document I can save as a file. Start it with the line "# MegaJam strategy — <your model name and version>, <today's date>", use "##" for each numbered section, put sources as inline links, and give it to me as a downloadable .md file if you can.
```

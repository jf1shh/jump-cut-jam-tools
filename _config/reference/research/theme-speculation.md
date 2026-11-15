# Theme speculation and reveal-day drill

Research date: 2026-10-29. **Speculation, not a decision.** The real theme is revealed at the
kickoff livestream, 2026-11-11 11:00 AM PT. Nothing here is gameplay, levels or art (Rule 7(h));
it is a planning/prompt artifact so the day-one "spread" in `stages/00_prep/references/win-plan.md` starts warm.

The goal is not to guess the exact words. It is to have already practised bending our verbs onto
the *kind* of theme Epic picks, so the 30-minute spread on Nov 11 produces a fresh reading instead of
the literal one hundreds of other teams will ship.

## 1. What past MegaJam themes look like

| Year | Theme | Shape |
|---|---|---|
| 2017 | "However vast the darkness, we must supply our own light" | Quote; light vs dark |
| 2019 | "Down to Earth" | Idiom with literal + figurative meaning |
| 2020 | "It's been a long time, but we're not done yet" | Meta: Epic's own moment (pandemic year, returning jam) |
| 2021 | "Running Out of Space" | Idiom; double meaning (room / outer space / storage) |
| 2022 | "As Above, So Below" | Idiom; duality |
| 2023 | "Antiquated Future" (unconfirmed, one participant's itch profile) | Contradiction pair |
| 2024 | apparently no jam (one devlog says so; unconfirmed) | — |
| 2025 | "Here We Go Again" (+ 3 optional classic themes) | Meta: 10-year anniversary; idiom |

Sources: `_config/reference/knowledge-base.md` "Past winners turned the theme into the mechanic";
`_config/reference/research/jam_rules_judging_past_winners.md` Q9; 2023 from
[tryhardcasuals.itch.io](https://tryhardcasuals.itch.io); 2024 from an
[itch devlog](https://itch.io/devlog/1063994/00-epic-megajam-announcement-and-musings.amp).

Patterns, in order of how strongly they hold:

1. **A common English idiom or phrase, 2–5 words**, that reads both literally and figuratively.
   Every confirmed theme since 2019 fits this.
2. **Meta about the jam's own moment.** 2020 and 2025 both nodded at what was happening to the jam
   itself. 2026's moment is obvious: it was renamed the *AI* MegaJam, cut to four days, and sold as
   "Vibe your way to $50k".
3. **Duality or tension** (light/dark, above/below, antiquated/future). Gives two states to switch
   between, which is why mirror/realm-switch games won in 2022.
4. **Never names a genre or a mechanic.** Epic leaves the verb to us.

## 2. 2026 signals worth reading

- **Key art: pink and blue flower-shaped balloons** behind the "EPIC MEGAJAM 2026" title
  (caption of the promo image on [android.com.pl](https://android.com.pl/tech/1098417-epic-rzuca-wyzwanie-tworcom-gier/)).
  Key art sometimes foreshadows the theme. Balloons suggest inflate / pop / pressure / float /
  fragile; flowers suggest bloom / grow. Weak signal, but free to prepare for, and it lines up with
  the water-balloon concept already researched (`_config/reference/research/water_balloon_physics_ue5.md` on the
  `research/water-balloon-concept` branch).
- **Launch post used a red pill / blue pill motif** (wait months for a prototype vs build it in a
  weekend with AI), per the same article. Signals *choice* or *two paths*. Epic won't use the film's
  IP, but a generic "choose" theme is plausible.
- **Humans + agents framing:** "Up to five humans. As many AI agents as you want." Collaboration,
  delegation, control and trust are the obvious meta-themes.
- **Walkie-Talkie modifier** (LLM-powered NPC dialogue, UEFN) and **Glass Box** (dev log) show Epic
  thinking about talking to and watching machines.
- **Four days, not seven.** A time-pressure theme would be on the nose but has precedent in tone
  (2020's "not done yet").

Sources: [itch jam page](https://itch.io/jam/2026-epic-ai-megajam),
[Epic news](https://www.unrealengine.com/news/2026-epic-ai-megajam),
[Inven Global](https://www.invenglobal.com/articles/27578/epic-games-announces-2026-epic-ai-megajam-with-up-to-50000-in-grants).
No official theme hint or teaser was found as of 2026-10-29.

## 3. Candidate themes, ranked by gut likelihood

Likelihoods are gut calls to order the drill, not probabilities anyone should bet on. The chance
that the real theme is *exactly* one of these is low; the chance it is the same *shape* as one of
them is high.

| # | Candidate | Why it fits | Tier |
|---|---|---|---|
| 1 | **Better Together** / Two Heads Are Better Than One | Human + agent meta; duality; idiom | A |
| 2 | **Out of Control** / Lose Control | AI autonomy anxiety; vibe-coding chaos; idiom | A |
| 3 | **Under Pressure** | Balloons; jam crunch; idiom | A |
| 4 | **Choose Wisely** / Fork in the Road | Red/blue pill launch motif; two paths | A |
| 5 | **Copy That** / Echo | Walkie-talkie radio phrase; AI copies; repetition | B |
| 6 | **Lost in Translation** | Talking to LLMs; NPC dialogue | B |
| 7 | **Something From Nothing** | Generative AI; building from scratch | B |
| 8 | **Bloom** / Grow / Inflate | Key art flowers and balloons | B |
| 9 | **Ghost in the Machine** | AI meta; spooky Nov; idiom | B |
| 10 | **Against the Clock** / Every Second Counts | Four-day jam | C |
| 11 | **Do As You're Told** / Follow the Instructions | Prompting; obedience; invertible | C |
| 12 | **Pop** | Balloons; pop culture; one word (Epic rarely does one word) | C |

## 4. Bend drill: each candidate onto our verbs

Lead verb is **Throw** (`stages/00_prep/references/pre-jam-mechanic-toolkit.md`); fallbacks Dash, Pull, Stack, Push.
For each theme: the literal reading most teams will make, a sideways reading, and how Throw bends
onto the sideways one. If Throw is a stretch, the fallback verb that fits better.

| Candidate | Literal (avoid) | Sideways reading | Throw bend | Better fallback |
|---|---|---|---|---|
| Better Together | Co-op buddies | You and an unreliable AI sidekick share one body/turn; each throw is half yours | Two-step throw: you aim, a partner (AI ghost) picks power; sync = big hit | Pull (tether two things together) |
| Out of Control | Car skidding | Your throws make the arena *more* chaotic; win by surfing the chaos you cause | Every hit spawns a bouncing hazard; score combos off your own mess | Push (chain reactions) |
| Under Pressure | Diver, deep sea | Pressure is the ammo: balloons get fuller, flight gets wobblier, bursts get bigger | Water balloon fullness = power vs control trade-off (existing research) | Stack (pressure topples) |
| Choose Wisely | Branching dialogue | Every throw picks one of two targets; the one you skip comes back | Two-target lanes; missed/ignored target returns stronger | Dash (left/right fork) |
| Copy That | Radio game | Everything you throw is copied by a mirror enemy a beat later | Throw → echo throws back; dodge your own last throw | Dash |
| Lost in Translation | Language puzzle | Instructions arrive garbled; throwing at the right thing decodes them | Targets are symbols; hit sequence = sentence | Stack (build the word) |
| Something From Nothing | Crafting | Thrown objects grow into platforms where they land | Throw seeds that bloom into the path you walk on | Stack |
| Bloom / Grow / Inflate | Gardening | Hits inflate targets until they pop; over-inflate and it pops on you | Charge-throw air into balloons; pop timing = score | Pull |
| Ghost in the Machine | Haunted house | You *are* the ghost; you throw the machine's parts around from inside | Possess-and-fling props at intruders | Push |
| Against the Clock | Timer racing | Time is the thing you throw: each throw costs seconds, hits refund more | Ammo = seconds; precision buys time | Dash |
| Do As You're Told | Simon Says | The game gives orders; disobeying at the right moment is how you win | Throw at what you're told *not* to hit | Push |
| Pop | Balloon shooter | Pop culture of a tiny world: you're the paparazzi throwing flashbulbs | Throw to "capture" moving celebrities (original, non-IP) | Dash |

Takeaways from running the drill:

- **Throw bent onto every candidate**, which supports keeping it as the lead verb. The weakest fits
  were "Lost in Translation" and "Something From Nothing", where Stack was cleaner.
- **The water balloon concept is the strongest single bet** if the theme lands anywhere near
  pressure / inflate / fragile / pop / bloom — four of the twelve candidates, and the key art leans
  that way. It is still not a decision.
- **Duality themes** (Better Together, Choose Wisely, Copy That) want a *second state* (a partner,
  a mirror, a second lane). Throw handles that with a twin target or an echo; no new verb needed.
- **Meta/AI themes** risk a wave of literal "the AI is the villain" entries. The sideways reading
  should make the AI angle a mechanic (a partner, a mirror, an order-giver) rather than the story.

## 5. Reveal-day plan (Nov 11)

The window opens 2026-11-12 00:00 ET (Nov 11, 9:00 PM PT). Theme reveal is 11:00 AM PT, so there
are about ten hours between reveal and start. Whether on-paper ideation in those hours is allowed is
an open question in `_config/reference/knowledge-base.md`; the plan below stays on paper either way and must not
touch the editor, levels or art before 9 PM PT.

1. **11:00 AM PT:** watch the kickoff; write the exact theme string down verbatim, plus any rule or
   category announcements.
2. **Within 15 min:** check this table. If the theme matches a candidate or its shape, start from
   that row's sideways reading rather than a blank page.
3. **30 min spread** (`stages/00_prep/references/win-plan.md` "Picking the concept"): 10 readings, literal to sideways.
   Use the prompt in `_config/reference/templates/theme-spread-prompt.md` to get a second set from an agent, then
   merge and cut.
4. Score the top three against `_config/reference/templates/scoring-rubric.md`. Throw first, then fallbacks.
5. Fill `_config/reference/templates/gdd-one-pager.md` for the winner. Theme on the title screen and in the first
   minute (Rule 7(g)).
6. **9:00 PM PT:** window opens; build starts.

## 6. Practice before the reveal

- **One timed drill:** pick a candidate at random (`shuf -n1` over section 3), set a 30-minute
  timer, run steps 3–5 above on paper only, and note how long it took and where it stalled. Delete
  nothing; record the time in this file. Goal: under 45 minutes from theme to one-pager.
  *Run 2026-11-11 (made-up theme "Hold Your Breath", agents only):* about 2 min of agent time from theme to
  one-pager draft, before owner reading time. Steps, timings and template fixes:
  `stages/00_prep/output/theme-drill-dryrun-2026-11-11.md`.
- **Re-check the key art and Epic's socials on Nov 10** for any teaser (Epic sometimes posts a hint
  the day before). Add anything found to section 2.

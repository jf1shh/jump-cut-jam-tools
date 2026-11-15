# Scope discipline and iterative design for a time-boxed jam entry

Research date: 2026-10-28, via deep-research workflow (5 search angles, 15 sources fetched,
adversarial verification on each claim). Full angle: game design theory, scope discipline from
small/solo indie teams, and jam-winning strategy, scoped to this entry (UE 5.8, Nov 11 9PM PT–Nov
15, small human team + unlimited AI agents). For the MegaJam's own rules, prize structure, AI-optional
reversal, and presentation strategy, see [jam_rules_judging_past_winners.md](jam_rules_judging_past_winners.md)
and [jam_winning_strategy_and_presentation.md](jam_winning_strategy_and_presentation.md) — this doc
does not repeat that material; it adds the design-process layer on top of it.

## Bottom line

Across jam judging norms, scope-discipline heuristics, and prototyping theory, the research converges
on one practical strategy: **pick one or two mechanics and polish them hard rather than spreading
effort across many systems.** Most jams (not confirmed yet for MegaJam specifically — see Gaps) score
several separate categories with no single combined score, so an entry can win big on
Creativity/Enjoyment/Theme-fit without being strong everywhere. Build a minimal playable loop in hours,
hit full *feature* scope by roughly the first quarter of total time, full *content* scope by the
halfway point, and spend the back half entirely on playtesting and polish.

## Findings

### Jam scoring tends to reward one strong axis, not uniform polish (confidence: high, but NOT confirmed for MegaJam)
GMTK 2025 scores five categories with no combined overall rank, and curators weight toward Creativity
and Enjoyment over raw polish. GDEX scores five categories (Functionality, Visual Design, Gameplay,
Engagement, Representation of Theme) that separate polish from theme fit. Two attempts to find
MegaJam's own rubric both failed — its judging criteria remain unverified (matches the gap already
flagged in `jam_winning_strategy_and_presentation.md`). Treat this as "how jams like this tend to
score," not MegaJam's actual rubric. **Action: don't assume uniform polish wins — decide which 1-2
categories this entry is actually trying to win, and spend disproportionately there.**
- Sources: https://itch.io/jam/gmtk-2025, https://www.thegdex.com/gamejam

### Iterative design: many small builds, not one linear build-up (confidence: high)
Design theory (independently corroborated by Zimmerman's *Play as Research* and Fullerton et al.'s
*Games, Design and Play*, not just blog sources) treats a project as a repeated cycle: plan, prototype,
playtest, evaluate, repeat — each cycle slightly bigger than the last. This directly supports
ship-the-minimal-loop-first, then layer, rather than building toward one final feature set.
- Source: https://gamedesignskills.com/game-design/iterative-process/

### Prototyping under a short deadline (confidence: medium)
Best practice: build fast (hours to a few days), test only one or two mechanics per prototype, use
placeholder art instead of final assets, define each prototype around one clear question, and start
the playtest-feedback-iterate loop as soon as the first tiny prototype exists — not after a
feature-complete build. Several supporting sources are lower-authority blogs, but the core
elements (one-or-two-mechanics prototypes, early playtesting) are independently corroborated by
gamedesignskills.com, Jesse Schell's prototyping guideline, and Cornell CS3152 materials.
- Sources: https://tonogameconsultants.com/prototyping/, https://tonogameconsultants.com/prototype-playtesting/

### Time-boxed scheduling heuristic (confidence: medium — treat exact numbers as illustrative, not rules)
Filter ideas through three gut-checks before committing scope: is it buildable in the time available,
does it pass a 30-second fun test, and is it understandable with no tutorial. Then: lock scope early,
build core mechanics next, layer content, then art/audio, and reserve the final chunk purely for
testing and submission. One experienced designer's personal heuristic puts **all features in place
(even unpolished) by roughly the first quarter of total time**, and **all content in by the halfway
point**, leaving the back half strictly for polish. The specific hour-by-hour schedule this came from
had an internal inconsistency in its own totals, so don't lift exact hours — but the checkpoint ratios
(1/4 for features, 1/2 for content) are a reasonable planning target for this jam's ~4-day window.
- Sources: https://www.strayspark.studio/blog/game-jam-survival-guide-tools-templates, https://gamedesignskills.com/game-design/iterative-process/

### Presentation-heavy jam formats risk becoming pitch contests (confidence: low)
One low-authority source, uncorroborated: jam formats that weight trailers/design statements/dev-logs
alongside the game itself can tip into rewarding marketing over gameplay unless the playable build
stays a meaningfully and separately scored criterion. Given MegaJam has a "best dev log" modifier
(per `jam_winning_strategy_and_presentation.md`), this is worth a sanity-check but shouldn't change
scope priorities — the dev log is a modifier prize, not believed to gate the main prize.
- Source: https://hackathonhost.com/articles/emerging-game-jam-formats

## Caveats

Several claims rest on single blog-quality sources rather than primary design-theory texts — treat
numeric specifics (exact hour splits, percentage checkpoints) as directional heuristics, not validated
rules. The biggest gap is unchanged from prior research: **MegaJam's own judging rubric is still
unverified**; the jam-scoring findings above come from GMTK and GDEX as general patterns, not MegaJam
itself. Re-check the official itch.io page close to submission in case the rubric or rules change again
(Epic already reversed the AI-mandatory rule once post-announcement).

## Open questions
- MegaJam's actual judging categories and weights (biggest gap — still unresolved after two research passes).
- Whether visible heavy AI usage is rewarded (craft/creativity bonus) or penalized (looks "just prompted") independent of the optional rule.
- Exact submission format expectations (video required? dev-log format?).

## Action items for our entry
1. Pick the one or two mechanics we want this entry to be known for, and explicitly deprioritize
   everything else — don't spread effort evenly across systems.
2. Target: playable core loop within the first ~24 hours (roughly first quarter of the ~4-day window),
   even with placeholder art.
3. Target: all content (levels/assets/whatever "content" means for our scope) in by the halfway point
   (~day 2 of 4).
4. Reserve the back half of the jam strictly for playtesting and polish — not new features.
5. Decide which modifier category (if any) we're actually trying to win, and weight polish effort
   toward whatever that category rewards, rather than assuming uniform polish is the goal.

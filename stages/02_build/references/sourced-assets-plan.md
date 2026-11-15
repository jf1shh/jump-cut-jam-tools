# Sourced assets plan (mixed: sourced filler + AI-generated heroes)

Ticket T-20261106-15. Owner 2026-11-06: "we just dont have the hardware for all local so we will have to use
fab and other resources that are allowed from the rules." Owner 2026-11-08: real props, not grey shapes, is a
rule now; props MVP freeze is Tue Nov 10 17:00 PT.
Pre-jam note: this file is planning only. No asset in it has been downloaded or imported (Rule 7(h)).

Evidence level: rules text is from `RULES.md`, the digest of Epic's Official Rules v3 (Box PDF, read 2026-10-27,
re-hashed 2026-10-29). This ticket could not re-read the PDF (Box blocks curl). Pack facts below come from the
vendor pages fetched 2026-11-08 (read only). "Not stated" means the page did not say; check it before relying on it.

## 1. What the rules allow

| Question | Answer | Rule | Confidence |
|---|---|---|---|
| Are sourced assets allowed? | Yes, if licensed and listed. Fab, other marketplaces and libraries all count as "sourced". | 15(c) | Digest quote |
| Must they be listed? Where? | Yes: noted in the submission (entry form / itch.io page). The ledger `stages/02_build/output/sourced-assets.csv` plus `scripts/sourced_assets.py credits` makes that block. | 1(d), 15(c) | Digest |
| Does not listing risk DQ? | Treat as yes. Unlisted or unlicensed sourced assets are DQ risk #13 in `_config/reference/knowledge-base.md`. | 1(d), 15(c) | Plan's own risk table |
| Are they scored? | No. "Will not be reviewed or scored." Visuals and Audio points come only from original work. | 15(c) | Digest quote |
| Is AI-generated content "sourced"? | No. It is not a sourced asset, so it is not listed there and it can score. Disclose it in the AI field instead (see win-plan). | 15(c) | Digest quote |
| Does placing or lighting sourced assets score? | Unknown. In 2023 the *implementation* (e.g. modulated sourced audio) could earn points. 2026 text says "not reviewed or scored". Assume no. Open question 7. | 15(c) | Unclear; safe reading: no credit |
| May we claim or download packs before Nov 12? | Claiming into the owner's Fab library and keeping files outside the repo: allowed. KB table says "Claiming Fab freebies: allowed". | 7(h) | Reasonable reading |
| May we import them into the jam project before Nov 12? | Not clear. 7(h) says all gameplay, levels and art are made in the contest period; it does not say whether a pre-owned pack counts. **Safe reading: no.** Import only after Nov 11 9:00 PM PT. | 7(h) | Unclear; safe reading picked |
| Can the pre-jam repo hold the files? | No. Epic may ask for the repo's version history. Keep packs outside git (`~/sourced-packs/`, not in the repo), and commit them only after the window opens. | 7(h) | Safe reading |
| Third-party IP / trademarks? | None. Check each pack for logos, brand names or character likenesses. | 8, 15(d) | Digest |
| Size cap | Zip under 1 GB. Cook only what is used; Megascans 8K textures are the usual cause of bloat. | 1(b) | Digest + KB |

Two things the owner could ask Epic (forum thread, open questions 7 and 8 in the knowledge base): (a) may a pack
claimed before the window be imported once it opens (we assume yes), (b) does Starter Content count as sourced.
Until answered, list Starter Content in the ledger as `Epic Content License`, and import only inside the window.

## 2. The mixed plan

Visuals is one of seven criteria (5 points each). Sourced assets score nothing, so spend sourced assets where
the camera does not linger and spend generation where it does.

| Layer | Source | Why |
|---|---|---|
| Ground, sky, lighting, foliage, rocks, fences, crates, barrels, generic furniture | **Sourced** (Kenney CC0, Poly Haven CC0, Fab free, engine content) | Bulk filler. Costs minutes, zero GPU. A real prop beats a grey cube. |
| Materials / textures for the filler | Sourced (Poly Haven, ambientCG: CC0) | Fast, consistent. |
| The few hero and focal pieces: the player's tool, the target, the signature prop, the title art | **AI-generated**: GPT/Grok concept image, then 3D via Meshy (cloud) or TripoSplat (local when the GPU is free) | Original work, so it can earn Visuals points. Only 3 to 6 pieces. |
| One master material per hero look, driven by Material Instances | Original, built in the window | A shared tint/gradient makes sourced and generated pieces look like one game. This unifies the look and is where polish points come from. |
| SFX / music | MetaSound generator and ACE-Step (original); Kenney CC0 sound packs as fallback (sourced) | See KB audio rows. |

Scoring trade-off, stated plainly: every sourced prop is a prop that earns nothing. If a piece appears in the
first 5 seconds of the video or on the thumbnail, make it a hero piece (generated) or re-tint it into the master
material so it reads as ours. Sourced filler must never be the first thing a judge sees.

Hero-piece rules from the hub notes (owner research, video notes): decimate AI props to about 6 to 12K tris and
bake; texture-free option is AO baked to vertex colour with a UE master material tint; concept prompt = front and
back view, neutral pose, plain background; acceptance = bounding box in metres, scale 1, base at origin, tri
count. Meshy free tier is CC BY 4.0 (credit needed), paid is about $20/month with no credit; credit it in the
AI disclosure either way (it is not a "sourced" entry). RetopoFlow is reported non-commercial: check before use.

## 3. Shortlist of free, commercially usable packs

Only the licence rows marked "page checked" were read on 2026-11-08. UE 5.8 note for all: these are plain
meshes. Import as FBX/GLB, set scale (Kenney is about 1 unit per metre; check the bbox), assign one material,
and nothing here depends on an engine version. Fab items install through the Epic launcher / Fab plugin and are
tagged with supported engine versions on their listing; **check "5.8" or a newer-compatible tag on each page**.

### Sources and their licences

| Source | Licence | Credit needed | Page checked | Notes |
|---|---|---|---|---|
| [Kenney](https://kenney.nl/support) | CC0 1.0 | No | Yes | Support page: all game assets on the asset pages are CC0. No AI clause found. Do not use Kenney's logo. |
| [Poly Haven](https://polyhaven.com/license) | CC0 | No | Yes | HDRIs, textures, models. No scraping of the site: download by hand, not by script. |
| [ambientCG](https://docs.ambientcg.com/) | CC0 (known; the licence page redirected and was not re-read) | No | Not re-read | PBR materials. Verify on the docs page. |
| [Fab, Standard License](https://www.fab.com/eula) | Standard: commercial use, ship in a game, no stand-alone resale or free redistribution of the asset | No (Standard) | Yes | Per-listing licence. Free listings can also be CC BY (credit needed) or CC0. Read the licence line on every listing. |
| Fab: Megascans starter content | Fab Standard, but only if **added to the library** (a bare download does not apply the licence) | No | Via Epic forum thread | About 1,500 assets per Epic; the rest of Megascans is paid since 2025. Limited-time free items rotate every two weeks. [Epic post](https://forums.unrealengine.com/t/megascans-starter-content-on-fab/2255322) |
| Epic Starter Content / template content | Epic Content License (engine EULA) | No | No | Open question 22. Log it in the ledger when used. |
| [Sketchfab, filter CC0](https://sketchfab.com/features/free-3d-models) | Per model: CC0 or CC BY, others | CC BY: yes | No | Check each model's licence badge, poly count and trademarks. Slowest to clean up; last resort. |

AI-training/NoAI note: Fab listings can carry a "NoAI" tag and the Epic EULA reportedly restricts feeding its
content to generators (open question 21). **Never use a sourced pack as a reference image for Krea/GPT/Meshy.**

### By art style

Style tags below come from pack names and tags on the pages, not from a vendor style statement. File counts are
the "files" figure on the page; download sizes were not shown on any Kenney page, so check on download (all
Kenney packs are small, usually under 50 MB, but that is not verified).

| Style | Pack | Licence | Files | Link |
|---|---|---|---|---|
| Stylized / low-poly | Kenney Prototype Kit | CC0 | 145 | https://kenney.nl/assets/prototype-kit |
| Stylized / low-poly, nature | Kenney Nature Kit (trees, rocks, foliage) | CC0 | 330 | https://kenney.nl/assets/nature-kit |
| Stylized, interiors / props | Kenney Furniture Kit | CC0 | 140 | https://kenney.nl/assets/furniture-kit |
| Sci-fi | Kenney Space Kit (planets, ships) | CC0 | 150 | https://kenney.nl/assets/space-kit |
| Sci-fi / industrial | Kenney City Kit (Industrial) | CC0 (series page says CC0; this pack page not read) | not read | https://kenney.nl/assets/city-kit-industrial |
| Fantasy / medieval | Kenney Fantasy Town Kit 2.0 | CC0 | 160 | https://kenney.nl/assets/fantasy-town-kit |
| Fantasy | Kenney Mini Dungeon | CC0 (not read) | not read | https://kenney.nl/assets/mini-dungeon |
| Urban | Kenney City Kit (Suburban) 2.0 | CC0 | 40 | https://kenney.nl/assets/city-kit-suburban |
| Urban | Kenney City Kit (Roads) | CC0 (not read) | not read | https://kenney.nl/assets/city-kit-roads |
| Any (photoreal) | Poly Haven models, textures, HDRIs | CC0 | many | https://polyhaven.com/ |
| Any (photoreal) | Fab free Megascans starter content | Fab Standard | ~1,500 | search "Megascans starter" on https://www.fab.com |

Pick one style family after the theme is revealed and stay in it. Mixing Kenney low-poly with Megascans realism
looks worse than either alone. Kenney's flat colours also fit the "one master material tint" approach best.

### Owner steps (an agent cannot do these; they need the Epic account)

1. Before Nov 11, in the Epic launcher / Fab: **Add to library** the packs you want (Megascans starter, any
   current limited-time free items). Adding to the library is claiming, not importing. Do not add them to the project.
2. Download Kenney and Poly Haven packs by hand from the browser into `~/sourced-packs/<source>/<pack>/` (outside any git repo). Keep the zip's licence file next to it.
3. For each, write down the exact licence line shown on the page (copy it into the ledger `--licence` field).
4. Nov 10: re-check each page still shows the same licence.

## 4. First-hour shopping list (generic props for a balloon game)

The concept is not final, so this list is theme-neutral. Fetch these in hour one of the window and log each one
with `sourced_assets.py add` as it is imported. Freeze the props MVP by Tue Nov 10 17:00 PT means: the *list* and
the sources are decided by then, and the import happens in the window.

| Group | Items | Likely source |
|---|---|---|
| Ground and sky | Grass/dirt/concrete tiling materials, one HDRI sky | Poly Haven, ambientCG |
| Cover and arena | Crates, barrels, fences, walls, benches, planters, bins, stalls, tables | Kenney Prototype / Furniture / Fantasy Town, Fab free |
| Greenery | Trees, bushes, flowers, rocks | Kenney Nature Kit, Megascans starter |
| Buildings (backdrop) | 3 to 6 simple buildings, a few signs without brand text | Kenney City Kit |
| Set dressing | Lamps, flags/bunting, picnic items, cones, stairs, ramps | Kenney, Fab free |
| Gameplay placeholders to *replace* | Balloon, water splash, target, player tool | Generate (hero pieces), not sourced |
| UI / audio filler | Click, pop, splash, footstep, ambient loop | MetaSound / ACE-Step first, Kenney sound packs fallback |

## 5. Checklist during the window

**Staged rows (2026-11-11):** `stages/02_build/output/sourced-assets-staged.csv` holds the 24 Kenney and Poly Haven packs already
on disk in `~/sourced-packs/` (from `~/sourced-packs/LEDGER-PRE.md`): name, URL, the exact licence line,
author, and the local path in `files_used`, with `date` empty. It is not the ledger: the ledger stays header
only until the window opens (Rule 7(h) evidence), and it lists only what the game uses. At import, copy the
row's fields into the `add` command below with `--files` set to the `/Game/Sourced/<Pack>/` path. The
credits block is ready now as a preview: `python3 scripts/sourced_assets.py --csv stages/02_build/output/sourced-assets-staged.csv credits`.
The Fab items in `LEDGER-PRE.md` were claimed, not downloaded, so they have no staged rows.


- [ ] Import a sourced asset only into `/Game/Sourced/<Pack>/`, so the ledger and the content folder match.
- [ ] Log it the same minute: `python3 scripts/sourced_assets.py add --name ... --url ... --licence ... --author ... --files ...`
- [ ] Never import a pack with an unclear licence. No licence line, no import.
- [ ] Check each pack for logos, brand names, text in a non-English language (Rule 7(i)).
- [ ] Tint or re-material anything that appears in the first 5 seconds of the video.
- [ ] Before submit: `python3 scripts/sourced_assets.py credits` and paste the block into the itch.io page and entry form.
- [ ] The cooked size stays under 1 GB; delete unused imports from `/Game/Sourced/`.

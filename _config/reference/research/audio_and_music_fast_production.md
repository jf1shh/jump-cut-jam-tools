# Audio and music: fast local production for the jam (as of 2026-10-31)

Research scope: the real gaps in the jam's local-audio pipeline that aren't already covered by
`ai_asset_to_ue_handoff.md` §5 (AI audio licensing/import) or `game_feel_recipes_ue58.md` (MetaSound hit/impact
recipes). This note does not repeat either — it cross-references them by filename and only adds what they
don't already answer: ACE-Step's actual behavior for short/loopable game audio, whether a dedicated local SFX
path exists today, a loudness/mastering workflow for the submission video, UE 5.8 loop/compression specifics,
ACE-Step's license confirmed by name, and real local timing evidence from this project's own log.

Method: read `scripts/gen_music.py` and `stages/02_build/output/audio-pipeline-log.csv` in this repo; read
`~/Projects/nexus/scripts/nexus_music.py`, `backend/services/music/{models,generator}.py`, and
`docs/sdd/guaardvark-port.md` in the Nexus repo directly (not inferred from docs); fetched the ACE-Step 1.5
GitHub repo (`README.md`, `LICENSE`, `docs/en/ace_step_musicians_guide.md`) and HF model card; fetched Epic's
5.8 docs for MetaSounds, Sound Cues, and audio import; read the installed `ffmpeg`'s own `-h filter=loudnorm`
output (the actual binary on this machine, not a web page) plus EBU's own R128 publication page. One agent,
no multi-vote verification.

**Status: research notes only.** No gameplay, levels, or art are built or implied here (Rule 7(h)); the
`gen_music.py` script and this note are pre-window-legal artifacts (scripts, docs). Any actual music/SFX
*content* generated for the game itself still has to happen inside the contest window.

---

## 1. ACE-Step 1.5: what it's actually for, and how to steer it

### Takeaway
ACE-Step 1.5 is built and documented as a **full-song generator**, not a loop or stinger generator — its own
musicians' guide says so in its first paragraph. It has no native seamless-loop feature; looping is a
post-processing step we do ourselves (crossfade or loop-point trim), not something a prompt flag turns on.
Steering mood/intensity is done through two channels: a free-text **caption** (style/instrument/mood words)
and **lyric structure tags** in square brackets (`[Intro]`, `[Chorus]`, `[Instrumental]`, etc.) that double as
an energy roadmap even when there are no real lyrics. `gen_music.py`/Nexus's wrapper forces
`lyrics = "[Instrumental]"` whenever `--lyrics` is omitted, which means our instrumental-by-default calls
currently get no structure tags at all — just the caption.

### Cited Findings

**What ACE-Step is designed to do**
- The model's own musicians' guide opens with: "You describe the music you want — the style, the
  instruments, the mood, the lyrics — and it generates a full song in seconds. **Not a loop, not a beat — a
  complete song with vocals, instruments, and structure.**" — [ACE-Step 1.5 `docs/en/ace_step_musicians_guide.md`](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ace_step_musicians_guide.md), no calendar date on the page, confidence: high (primary, verbatim), status: confirmed.
- The top-level README describes the model as a planner that "transforms simple user queries into
  comprehensive song blueprints — **scaling from short loops to 10-minute compositions**" and separately lists
  "✅ **Flexible Duration** — Supports 10 seconds to 10 minutes (600s) audio generation." "Short loops" here
  reads as short *compositions* (duration), not an audio-engineering loop point — nothing elsewhere in the
  README, the musicians' guide, or the docs index (`docs/en/index.md` directory listing) names loop points,
  seamless looping, or crossfade looping as a feature. — [ACE-Step 1.5 README](https://github.com/ace-step/ACE-Step-1.5/blob/main/README.md), no calendar date, confidence: high (absence check across the whole docs/en/ directory listing, not just one page), status: confirmed as a **Gap in the model**, not a gap in this research.
- Nexus's own request schema (`MusicRequest` in `backend/services/music/models.py`) and the ComfyUI graph it
  drives (`STAGES` dict in `backend/services/music/generator.py`, referencing `TextEncodeAceStepAudio1.5` and
  `KSampler` node types) have no loop, crossfade, or loop-point field anywhere. `duration` is a plain
  `10 <= n <= 120` integer. — `~/Projects/nexus/backend/services/music/models.py`, `generator.py` (read directly, 2026-10-31), confidence: high (primary, this project's own code), status: confirmed.

**Steering mood/intensity in a tight time budget**
- The caption is "a short paragraph describing the entire song's vibe" and the guide's own worked example of
  "better" vs. "vague" is: vague = `"a sad song"`; better = `"melancholic piano ballad with soft female
  vocals, gentle string accompaniment, slow tempo, intimate and heartbreaking atmosphere"`. Tips given
  verbatim: "Name the genre... Name the instruments... Name the mood: melancholic, uplifting, energetic,
  dreamy, aggressive, intimate... Name the production style." — [ace_step_musicians_guide.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ace_step_musicians_guide.md), confidence: high, status: confirmed.
- Lyrics "do double duty... They're not just words — they tell the AI how the song should be **structured
  over time**," via bracket tags: `[Intro]` ("sets up atmosphere, usually instrumental"), `[Verse]` ("moderate
  energy"), `[Pre-Chorus]` ("builds tension"), `[Chorus]` ("emotional peak, highest energy"), `[Bridge]` ("a
  shift"), `[Instrumental]` ("no vocals, just instruments"), `[Outro]` ("winds down, often fades"). The guide
  explicitly recommends this even with no real words: "Even if you don't care about the actual words yet,
  writing `[Intro] [Verse] [Chorus] [Verse] [Chorus] [Bridge] [Chorus] [Outro]` gives the AI a roadmap for
  energy and dynamics." Descriptors can be appended to a tag for extra guidance, e.g. `[Chorus - anthemic]` or
  `[Verse - whispered]`. — same source, confidence: high, status: confirmed.
- `gen_music.py`'s own CLI always submits `--instrumental` unless `--lyrics FILE` is given (see "else:
  cmd.append('--instrumental')" in `scripts/gen_music.py`), and Nexus's generator then hard-codes
  `lyrics = '[Instrumental]'` for any instrumental request (`effective = {... 'lyrics': '[Instrumental]' if
  request.instrumental else request.lyrics ...}` in `generator.py`). **This means every instrumental call this
  project makes today skips the `[Intro]/[Chorus]/[Outro]` energy-roadmap mechanism entirely** — intensity
  steering for instrumental tracks currently has only the caption to work with, not the structure-tag trick
  the model's own guide recommends. — read directly from both files, confidence: high, status: confirmed (this is a real finding about our own pipeline, not the model).
- The guide's general tuning advice: "Don't try to control everything on your first attempt. Start with a
  short caption and see what the AI gives you. Then add detail in areas where the output surprised you." —
  same source, confidence: high, status: confirmed.

**Hardware/time-budget hints from the model's own docs** (context for §6 below)
- A GPU hardware table in the guide ties VRAM to max song length and concurrency, e.g. "4 GB (entry level) →
  Songs up to 6 minutes, 1 song at a time, Basic mode only"; "8-12 GB (mainstream) → Songs up to 10 minutes,
  2-4 songs at a time." It gives no absolute wall-clock seconds-per-song figure, and it is written for NVIDIA
  VRAM tiers, not this project's AMD RDNA4 card. — [ace_step_musicians_guide.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ace_step_musicians_guide.md), confidence: medium (doesn't name our hardware), status: confirmed as written, not applicable as a timing number.

### Inferences
- Looping has to be done after generation, full stop — there is no flag to ask ACE-Step for a loop-safe
  render. The practical workflow for a game loop is: generate a track a few bars longer than needed, pick a
  loop point by ear/waveform (ideally on a bar boundary, at a moment with similar harmonic/rhythmic content on
  both sides), and either hard-cut at a zero-crossing or crossfade the tail into the head (a short, e.g.
  50-200 ms, equal-power crossfade smooths a seam that a hard cut leaves audible). `ffmpeg`'s `afade`/`acrossfade`
  filters or manual trim+concat can do this; this is standard DAW/game-audio practice, not something sourced
  from ACE-Step's own docs, so treat the exact crossfade length as a starting point to listen-test, not a cited
  number.
- For a one-shot stinger (Glass Box dev-log theme, a short "you won" cue), ACE-Step is a better fit than for a
  seamless loop: it's a complete-song generator, and a 10-20 s "song" with a clear `[Intro]`→`[Outro]` arc is
  closer to what it's built for than a loop with no beginning or end.
- Given the `[Instrumental]` override finding above, if intensity/structure steering of an instrumental track
  via lyric tags is wanted, `gen_music.py` would need a change to pass real structure tags through even in
  instrumental mode (currently architecturally blocked by Nexus's own override, not by ACE-Step). That's a
  real, actionable gap in our own tool, not a research gap — worth flagging to whoever owns `gen_music.py`.

### Gaps
- No primary-source confirmation of ACE-Step's output sample rate from ACE-Step's own docs (the existing
  `ai_asset_to_ue_handoff.md` already flags the "48 kHz" figure as third-party-only/low confidence; this
  research did not find anything in the ACE-Step repo itself that states it, so that gap stands).
- No measured number, from any source, for how audible a given crossfade length is on ACE-Step output
  specifically — this would need an actual listen-test on a generated track, not a web search.

---

## 2. SFX: is there a dedicated local path, or is it ACE-Step/gen_music.py?

### Takeaway
**There is no dedicated local SFX tool available through Nexus today.** The only working local audio
generator wired into Nexus is the ACE-Step music pipeline that `gen_music.py` wraps. A distinct SFX backend
(Stable Audio Open, via a planned "Audio Foundry" service) exists only as an **architecture plan with a
reserved port and no implementation** — it is explicitly called out as not-yet-built, "open-ended" effort, in
Nexus's own porting design doc. `ai_asset_to_ue_handoff.md` §5 already lists Stable Audio Open as a licensed
option and "optional SFX supplement" in its pipeline recommendation, but that's a licensing/options survey,
not a statement that it's running — this note confirms, from Nexus's actual backend code, that it is not.

### Cited Findings
- Nexus's `backend/services/` tree has exactly one music/audio generation service directory,
  `backend/services/music/` (ACE-Step via ComfyUI, `TextEncodeAceStepAudio1.5` + `KSampler` nodes). No
  `audio_foundry`, `stable_audio`, or similarly-named service directory exists anywhere in the repo (checked
  with `find`/`grep` across `backend/`, excluding stale worktree copies). — read directly from
  `~/Projects/nexus/backend/` on 2026-10-31, confidence: high (exhaustive directory search, not a doc claim), status: confirmed.
- Nexus's `service_supervisor.py` names "Audio Foundry (:8206)" as one of four out-of-process servers the
  supervisor is *designed* to manage, alongside ComfyUI (:8188), upscaling (:8202), and a swarm orchestrator
  (:8210) — but this is a reserved port in a scheduling/VRAM-claim design, not evidence a server exists there.
  — `~/Projects/nexus/backend/services/service_supervisor.py` (top-of-file docstring), confidence: high, status: confirmed (as a plan, not a running service).
- The porting design doc that defines "Audio Foundry" (`docs/sdd/guaardvark-port.md` §11.2) describes it as
  "Four backends: Chatterbox and Kokoro (voiceover), **Stable Audio Open (SFX/ambience)**, ACE-Step (full
  songs)" and estimates effort as "~3 days for Kokoro + Chatterbox; **ACE-Step open-ended**" — placed
  deliberately last in the porting plan ("Deliberately last: each is independently useful, none blocks
  anything, and all three [upscaling/audio/LoRA] compete for the same 16 GB"). Stable Audio Open and ACE-Step
  are both flagged "torch diffusion models, unverified on RDNA4" in that same doc. — `~/Projects/nexus/docs/sdd/guaardvark-port.md` §11.2, no calendar date on the section (file last touched per repo metadata, not re-checked here), confidence: high (direct read), status: confirmed as a plan, explicitly not yet built.

### Inferences
- The realistic local path for short game SFX (footsteps, UI clicks, impacts, pickup chimes) today is
  `gen_music.py`/ACE-Step itself — generating a short (10 s minimum, per `MusicRequest.duration`'s `ge=10`
  floor) instrumental clip and trimming it down, or batching several short "hits" into one render and slicing
  them out. This is a real workaround, not an ideal one: ACE-Step is a song model, not a one-shot SFX model,
  so very short percussive/foley-style sounds (a click, a chime, a footstep thud) are outside what it's
  designed to produce well, and the 10 s floor means every SFX render costs at least a 10 s generation to get
  a fraction-of-a-second usable sound.
- If dedicated local SFX generation matters for this jam's scope (footsteps/UI/impacts are common jam-budget
  needs), the options in order of effort are: (a) resourceful ACE-Step trimming as above (zero new work), (b)
  Epic's own "SFX Generator" MetaSound (already covered in `ai_asset_to_ue_handoff.md` §5 — a Fab plugin,
  in-engine, procedural, no GPU-gen step at all, good for UI blips/zaps), or (c) actually standing up the
  planned Audio Foundry/Stable Audio Open service, which per the porting doc's own estimate is not a small
  side task during a 4-day jam. For jam week specifically, (a) or (b) are the realistic choices; (c) is a
  pre-jam infra project only if there's spare capacity.

### Gaps
- Whether Stable Audio Open would actually run on this RDNA4 card at all is explicitly unverified in Nexus's
  own docs ("unverified on RDNA4") — this research did not attempt to stand it up or test it.
- Whether Epic's Fab "SFX Generator" / TechAudioTools Content plugin has a confirmed 5.8 build is already
  flagged as unresolved in `ai_asset_to_ue_handoff.md` §5 Gaps; not re-derived here.

---

## 3. Loudness/mastering for the submission video

### Takeaway
`ffmpeg`'s built-in `loudnorm` filter (installed on this machine, FFmpeg n9.0.2) is the practical normalization
tool, and it defaults to **-24 LUFS integrated, -2 dBTP true peak, 7 LU loudness range** — close to but not
identical to the EBU R128 broadcast target of **-23.0 LUFS / ±1 LU tolerance**, which is `loudnorm`'s own
spec reference (the filter is literally named after EBU R128 in its own `-h` output: "EBU R128 loudness
normalization"). For a gameplay capture video specifically there's no single universal number, but -23 LUFS
(EBU R128, the filter's native target) or YouTube's commonly reported -14 LUFS consumer-video target are the
two real anchors — this note could not confirm the -14 LUFS figure from an official Google/YouTube help page
(see Gaps), so treat it as medium confidence, not primary-sourced.

### Cited Findings
- The installed `ffmpeg` binary's own `-h filter=loudnorm` output (run directly on this machine,
  `ffmpeg version n9.0.2`) lists every parameter and its default: `I`/`i` integrated loudness target, range
  -70 to -5, **default -24**; `LRA`/`lra` loudness range target, range 1-50, **default 7**; `TP`/`tp` maximum
  true peak, range -9 to 0, **default -2**; `linear` (boolean, default **true**, "normalize linearly if
  possible"); `dual_mono` (boolean, default **false**); `print_format` (none/json/summary, for two-pass stats);
  `measured_I`/`measured_LRA`/`measured_TP`/`measured_thresh` (for feeding first-pass measurements into a
  second pass); `stats_file`. — `ffmpeg -h filter=loudnorm` run locally 2026-10-31, confidence: high (primary — the actual shipped binary), status: confirmed.
- EBU R 128 itself (the standard the filter targets) sets the Programme Loudness target at **-23.0 LUFS**,
  with a published tolerance of **±1 LU** in the base recommendation (a tighter ±0.2 LU tolerance was added in
  a 2020 revision 3, per secondary summary — not independently re-verified against the PDF text in this pass).
  — [EBU R128 publication page](https://tech.ebu.ch/publications/r128), no calendar date beyond "last updated" metadata on the page, confidence: high for the -23 LUFS/±1 LU figures (this is the standard's defining number, widely and consistently cited including by `ffmpeg`'s own code), medium for the ±0.2 LU revision-3 detail (not independently re-checked against the primary PDF), status: confirmed for -23 LUFS, unverified-but-plausible for the tighter tolerance.
- YouTube is commonly reported (multiple secondary sources, consistent with each other) to target **-14 LUFS**
  integrated loudness for uploaded content and to only turn audio *down* to reach that target, never up.
  This research could not find an official Google/YouTube Help Center page stating this number directly — the
  one YouTube support page fetched (`support.google.com/youtube/answer/9004474`, about information panels)
  does not mention loudness at all, and no on-domain `support.google.com` page with the loudness spec turned
  up in search. — no primary source found; multiple consistent secondary sources (e.g. audio-mastering/creator-tooling blogs), confidence: medium, status: **unverified from a primary source — treat as likely-correct community knowledge, not confirmed Google policy**.

### Inferences
- A practical two-pass `loudnorm` workflow for a jam deliverable, following the filter's own documented
  parameters above (this is standard `loudnorm` usage, not an ACE-Step- or jam-specific finding):
  1. First pass, measure only: `ffmpeg -i in.wav -af loudnorm=I=-23:TP=-1:LRA=7:print_format=json -f null -`
     and capture the `input_i`/`input_tp`/`input_lra`/`input_thresh` values from the printed JSON.
  2. Second pass, apply with the measured values fed back in via `measured_I`/`measured_TP`/`measured_LRA`/
     `measured_thresh`, which lets `loudnorm`'s `linear=true` mode do a single linear gain pass instead of its
     dynamic (non-linear) compressor-like mode — this avoids the audible pumping that one-pass `loudnorm` on
     highly dynamic material can produce.
  3. Pick the target `I` based on destination: -23 LUFS / -1 dBTP if treating the EBU R128 broadcast spec as
     the house standard (safe, conservative, matches the filter's own design target), or a louder -14 LUFS if
     optimizing for how it'll sound un-adjusted next to other YouTube content (less conservative, and not
     primary-sourced per above).
  4. For the final mux into the 30-60 s gameplay video, run the normalization on the mixed music+SFX stem
     *before* muxing with ffmpeg into the video container, so the loudness measurement reflects the final mix
     rather than music and SFX independently.
- This is a separate step from, and should happen after, any UE-side mixing/limiting on the Sound Mix bus; it
  targets the final rendered video's audio track specifically, which is a different deliverable from in-game
  runtime audio.

### Gaps
- No primary Google/YouTube source for the -14 LUFS figure (see above) — flagged, not asserted as fact.
- Did not independently re-verify the EBU R128 ±0.2 LU revision-3 tolerance detail against the primary PDF
  text (only a secondary summary was checked); the core -23 LUFS target is solid, that one tolerance detail is
  not.
- No cross-check performed against `game_feel_recipes_ue58.md`'s narrator-audio gap — that doc's open items
  are about in-editor camera-shake/time-dilation behavior, not loudness mastering, so there was nothing there
  to reconcile.

---

## 4. UE 5.8 audio import: loop points, Sound Cue vs. MetaSound, compression and build size

### Takeaway
For looping, UE 5.8 gives two different mechanisms depending on asset type: a plain **`SoundWave.Looping`**
boolean for playing a wave file looped directly, a legacy **Looping node (`SoundNodeLooping`)** inside a
Sound Cue graph, and a native **loop-points feature in the MetaSound Wave Player node** (seek, loop points,
sample-accurate concatenation, cue-point reading) — the most capable of the three, confirmed by name in
Epic's own MetaSounds overview page, though that page doesn't walk through *how* to set loop points, only that
the feature exists. `ai_asset_to_ue_handoff.md` §5 already covers the Sound-Cue-is-"legacy"/MetaSounds-replace-it
framing and the import-format/compression-codec list; this section only adds the loop-mechanism names Epic
uses by name, which that doc doesn't cite.

### Cited Findings
- Epic's MetaSounds overview page states: "The library features a rich **Wave Player** node, which supports
  **seeking, loop points, sample-accurate concatenation**, pitch-scale modulation, and reading from cue points
  in an audio file." — [MetaSounds: The Next-Generation Sound Sources in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine), no calendar date shown on page, confidence: high (verbatim Epic doc quote), status: confirmed feature exists; **how to configure loop points specifically is not documented on this page** (treat the "how" as a Gap, not the "that").
- `USoundWave`'s `Looping` property (C++ `bLooping`) is documented as: "If set, when played directly (not
  through a sound cue) the wave will be played looping." — Epic Python/C++ API reference (`unreal.SoundWave`
  class pages), confidence: high, status: confirmed; this is for direct wave playback, not Sound Cue or
  MetaSound graphs.
- A Sound Cue's own looping is done via a dedicated graph node, `SoundNodeLooping` (listed in Epic's Python
  API class index as a Sound Cue node type), separate from the `Looping` property on the wave asset itself. No
  Sound-Cue-specific "how to loop" walkthrough was found on Epic's general Sound Cues landing page — that page
  (`dev.epicgames.com/.../sound-cues-in-unreal-engine`) turned out to be a thin topic-index page with no
  substantive content on this fetch, not a tutorial. — confidence: medium (node's existence confirmed via API index; its usage not confirmed via a walkthrough page), status: partially confirmed.
- (Already in `ai_asset_to_ue_handoff.md` §5, not re-derived here, only restated for context): Epic's audio
  import page documents codecs **Bink Audio (Default), ADPCM, PCM, and Platform Specific**, compression
  ratios from uncompressed up to **10:1**, and a per-platform codec/quality-level setting on each Sound Wave;
  imported audio is converted to 16-bit internally, with 24-bit sources **not dithered** down (Epic's own
  recommendation is to supply 16-bit source audio to avoid this). — [Importing Audio Files](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-audio-files), confidence: high, status: confirmed (restated from the existing doc's citation, not a new finding).

### Inferences (judgment call: MetaSound vs. Sound Cue for this 4-day solo scope)
- For a 4-day solo jam, **use MetaSound Sources for anything new**, not Sound Cues — this matches
  `ai_asset_to_ue_handoff.md`'s own pipeline recommendation ("Use MetaSound Sources, not Sound Cues, for new
  content") and is reinforced here by the Wave Player node's native loop-point support: it's one asset type
  that handles both looping music/ambience and one-shot SFX, instead of maintaining two different looping
  mechanisms (a wave's `Looping` bool vs. a Sound Cue's `SoundNodeLooping` node) for no jam-scope benefit.
  Epic itself frames Sound Cues as "legacy" with MetaSounds as the replacement (already cited in the existing
  doc), which is a second, independent reason to default to MetaSound.
- For keeping the final zip under 1 GB (Rule constraint from `AGENTS.md`): prefer **Bink Audio** (the 5.8
  default, up to 10:1) over PCM/ADPCM for anything that isn't a very short, latency-critical one-shot, and set
  per-platform Compression Quality down from its max only if a real size audit shows audio is a meaningful
  share of the 1 GB budget — for a jam-scale game (handful of music tracks, dozens of short SFX) audio is
  unlikely to be the dominant contributor to package size compared to meshes/textures, so this is a "check
  once near the end, don't pre-optimize" item rather than a day-one concern.

### Gaps
- No Epic walkthrough found for *how* to actually place/author MetaSound Wave Player loop points in the
  editor UI (only that the capability exists) — would need to open the editor and look at the node's pin/
  property list directly, which this research pass (read-only, no editor session) didn't do.
- Whether FLAC specifically (the format `gen_music.py` outputs) routes through Interchange or the legacy
  import factory in 5.8 is already flagged unconfirmed in `ai_asset_to_ue_handoff.md` §5 Gaps; not re-derived
  here.

---

## 5. ACE-Step's license, confirmed by name

### Takeaway
Confirmed directly from the ACE-Step 1.5 GitHub repo: it is **MIT licensed**, with the repo's own `LICENSE`
file being the standard, unmodified MIT text (no additional restriction clauses), and the README's "License &
Disclaimer" section explicitly separates the legal license (MIT) from a set of non-binding usage
*disclaimers* (originality checking, disclosing AI involvement, respecting cultural/artistic integrity) that
read as responsible-use guidance, not license terms. This matches and confirms (does not contradict)
`ai_asset_to_ue_handoff.md` §5's existing one-line claim that "ACE-Step 1.5 ... is MIT with commercial use of
outputs explicitly allowed" — that doc already names ACE-Step specifically, so this section's job is
verification, not filling a naming gap.

### Cited Findings
- The repo's `LICENSE` file (fetched directly) is the unmodified standard MIT License text: "Permission is
  hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
  files (the 'Software'), to deal in the Software without restriction, including without limitation the
  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software..."
  (Copyright (c) 2026 ACEStep). No additional non-commercial, attribution-beyond-MIT, or field-of-use
  restriction clause is present in the file. — [ACE-Step-1.5/LICENSE](https://github.com/ace-step/ACE-Step-1.5/blob/main/LICENSE), no calendar date, confidence: high (primary, full file text fetched and read), status: confirmed.
- The README's own "📜 License & Disclaimer" section states: "This project is licensed under [MIT](./LICENSE)"
  and then, in a separate paragraph, lists usage guidance: "we encourage users to verify the originality of
  generated works, clearly disclose AI involvement, and obtain appropriate permissions when adapting protected
  styles or materials... By using ACE-Step, you agree to uphold these principles..." This is phrased as an
  ethical-use request ("we encourage"), not a license condition, and sits in a section titled "Disclaimer" as
  well as "License." — [ACE-Step-1.5 README.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/README.md), confidence: high, status: confirmed.
- The HF model card separately states, in its own words (not independently re-quoted verbatim here beyond
  what a summarization pass returned): generated music "can strictly" be used for commercial purposes. This
  is consistent with, not contradicted by, the MIT grant in the GitHub repo. — [HF ACE-Step/Ace-Step1.5](https://huggingface.co/ACE-Step/Ace-Step1.5), confidence: medium (read via a summarizing fetch, not the raw card text directly), status: confirmed-consistent with the GitHub LICENSE finding, which is the stronger primary source.

### Inferences
- Commercial use of ACE-Step-generated audio in a MegaJam prize submission is **permitted under the license
  itself** — MIT places no restriction on commercial use of the software, and by extension there is no
  license-based bar on using its *outputs* commercially either (the README's "License & Disclaimer" framing
  treats output-commercial-use as a given, only asking for responsible-use disclosure, which is a request, not
  a condition). This satisfies the license side of Rule 15(c) (original content, not a "sourced asset"); the
  separate originality-disclosure *request* in the README dovetails with the jam's own Glass Box dev-log and
  AI-disclosure expectations already discussed in `ai_asset_to_ue_handoff.md` — a credits-block entry for
  ACE-Step covers both.
- Nothing found here changes `ai_asset_to_ue_handoff.md`'s existing recommendation; this section exists to
  verify that claim against the primary LICENSE file rather than take the model card's summary at face value,
  which it now has.

### Gaps
- None of substance — this was the most directly verifiable of the six research items, since the primary
  source (the LICENSE file itself) is short, unambiguous, and was fetched and read in full.

---

## 6. Real local generation time, from this project's own log

### Takeaway
`stages/02_build/output/audio-pipeline-log.csv` in this repo is **not empty** — it has real rows from actual `gen_music.py` runs
on this hardware, and they're the only real timing evidence this research used (no benchmark numbers were
invented or taken from someone else's hardware). The two successful runs logged so far: a 30 s track took
**112.46 s**, and a 45 s track took **118.41 s**. Both failed attempts in the log failed fast (sub-3-second
exit codes 1/3 — invocation or missing-model errors, not generation attempts), so they're not timing data
points, just failure records.

### Cited Findings
- `stages/02_build/output/audio-pipeline-log.csv`, read directly, contains 6 data rows (plus header) as of this research pass:
  - `2026-10-28T20:15:41Z, work/audio/test_theme.flac, duration=30, seconds=0.14, exit_code=3` — fast failure
    (exit 3 = "model missing or backend unreachable" per `nexus_music.py`'s documented exit codes), not a
    generation attempt.
  - `2026-10-28T23:19:32Z, work/audio/test_theme.flac, duration=30, seconds=112.46, exit_code=0` — **successful
    30 s track, 112.46 s wall-clock.**
  - `2026-10-29T13:34:34Z` and `T13:34:55Z, work/audio/mockjam4_score_hit.flac, duration=10, seconds≈2.2,
    exit_code=1` — fast failures (exit 1 = "failed or cancelled"), ~2.2 s each, not generation attempts.
  - `2026-10-29T17:39:02Z, work/audio/lastlight_theme.flac, duration=45, seconds=0.16, exit_code=3` — fast
    failure, same pattern as the first row.
  - `2026-10-29T17:43:47Z, work/audio/lastlight_theme.flac, duration=45, seconds=118.41, exit_code=0` —
    **successful 45 s track, 118.41 s wall-clock.**
  — `stages/02_build/output/audio-pipeline-log.csv`, read directly 2026-10-31, confidence: high (this is this project's own
  measured data, the single best-sourced finding in this entire note), status: confirmed.

### Inferences
- The two successful runs (30 s → 112.46 s, 45 s → 118.41 s) are close to each other despite a 50% difference
  in requested track length — generation time on this hardware looks dominated by a largely fixed model-load/
  setup cost plus a comparatively small per-second-of-output cost, not a linear scale-up. With only two data
  points this is a pattern, not a fitted curve — don't extrapolate a 90 s or 120 s track's time from just these
  two rows.
- Practical scheduling takeaway for jam week: budget roughly **2 minutes per successful instrumental track**
  as a planning number (rounding up from the two real data points), plus slack for failed/retried attempts —
  and since this has to run with the Unreal Editor closed (one GPU workload at a time, per the project's
  hardware constraint), batch all planned music/stinger generations into one editor-closed session rather than
  interleaving them with editor work.

### Gaps
- Only two successful runs exist in the log — not enough data to say whether time scales with duration, bpm,
  or prompt complexity, or whether the ~110-120 s figures hold for durations further from 30-45 s (e.g. a full
  90 s loop candidate, or a 10-20 s stinger). The three failed rows give no generation-time information at
  all (they all failed before or during setup).
- No data yet exists for a lyrics/vocal (non-instrumental) run, which per the model's own guide may behave
  differently (different node path through the ComfyUI graph, possibly different timing).

---

## Summary of what's actionable

1. **Our own `gen_music.py`/Nexus wrapper currently defeats ACE-Step's structure-tag steering mechanism** for
   every instrumental call (forces `lyrics = "[Instrumental]"`, dropping `[Intro]/[Chorus]/[Outro]` energy
   tags). If finer control over a track's energy arc matters, that's a real fix to consider, not a modeling
   limitation.
2. **There is no dedicated local SFX tool today** — Stable Audio Open ("Audio Foundry") is a reserved port and
   an unbuilt, open-ended-effort plan in Nexus, not a running service. For jam week, short SFX realistically
   comes from either stretching ACE-Step/`gen_music.py` past its comfort zone, or Epic's in-engine Fab "SFX
   Generator" MetaSound plugin (no GPU step, license already cleared in the existing doc).
3. **Looping is always a post-process**, never a model feature — confirmed directly from ACE-Step's own
   musicians' guide ("Not a loop... a complete song"). Plan for a manual crossfade/trim step on any music
   meant to loop in-game.
4. **Use MetaSound Sources, not Sound Cues**, for any new audio asset — Epic's own Wave Player node natively
   supports loop points, seeking, and cue points, one mechanism instead of juggling `SoundWave.Looping` and
   `SoundNodeLooping` separately. (Matches and reinforces what `ai_asset_to_ue_handoff.md` already recommends.)
5. **ACE-Step's MIT license is now directly verified** (LICENSE file text itself, not just the model card) —
   commercial use in the jam submission is clear; a credits-block entry is still the right move for the
   README's responsible-use disclosure request.
6. **Real timing data exists and says ~110-120 s per successful track** regardless of 30 s vs. 45 s requested
   length (`stages/02_build/output/audio-pipeline-log.csv`) — plan audio-generation batches accordingly, and don't trust a
   linear-scaling assumption beyond that range since only two successful runs are logged.
7. For the submission video's audio, **run two-pass `ffmpeg loudnorm`** before muxing (defaults: I=-24, TP=-2,
   LRA=7; EBU R128's own target is I=-23/TP=-1) — the exact target (−23 EBU vs. the commonly reported but
   not-primary-sourced −14 YouTube figure) is a judgment call, not a hard rule confirmed here.

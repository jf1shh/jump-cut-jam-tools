# MetaSound music plan (JumpCut)

Owner/hub rule: no cloud music, no local AI music. Music is made in-engine with a MetaSound source, so it is original, licence-free and listed as in-engine content (Rule 15).

**Update 2026-11-12 (superseded in part):** the hub 142 / Fable "Road to 30" decision (`superagent-sandbox/.handoff/hub141/road-to-30-fable.md`, section 2: "generate a new score, keep code loops as fallback") allows cloud-generated music for the score, through the terms-gated fal adapter `scripts/gen_music_fal.py` (see `_config/reference/ai-providers.md`, "fal music"). AI-generated music is the entry's own work, not a sourced asset (Rule 15(c)); ledger every call. The MetaSound / code loops below stay as the fallback. The "no local AI music" half is unchanged (owner 2026-11-11: no local models during the jam). The old text is kept as history.

## Hook already in the game
- `UJCTuning::Music` (`USoundBase`) is played once by `UJCCutComponent::UpdateMusic` (dv.28) on real time, never seeked.
- While the hold ease is active, the component raises a low-pass filter from 20 kHz down to `HoldLowPassHz`. A MetaSound source is a `USoundBase`, so it drops straight in. No C++ change is needed.

## Plan
1. `MS_Jump_Cut_Loop` (MetaSound Source, looping, mono-to-stereo out): a tempo clock (about 112 BPM) drives three layers.
   - Bass: saw oscillator through a ladder filter, 8-step pattern chosen by a Random Get over two patterns.
   - Pad: two detuned oscillators, slow LFO on cutoff.
   - Pulse: noise burst through a band-pass on 8ths, as a hi-hat stand-in.
2. Inputs for the game: `Intensity` (float 0..1, lifts pulse level and bass filter). v1 may leave it unwired; the engine low-pass already handles the hold.
3. Set `Tuning.Music` to the asset and `Volume` to about 0.5. Check the log line `JC music: started MS_Jump_Cut_Loop`.
4. Check off-screen with `-nosound` removed only if the hub allows audio, else verify the log line and a render of the asset to a wave in the editor by hand.

## Risks
- MetaSound graph building over Unreal MCP is slow; build it by hand in the editor in one sitting, or by Python if the 5.9 MetaSound builder API allows (check `MetaSoundBuilderSubsystem` in the engine source first).
- Audio cannot be heard off-screen; Yo or the owner must listen on the Legion.
- Keep the music file out of the pre-window ban: author it only inside the contest window (it is).

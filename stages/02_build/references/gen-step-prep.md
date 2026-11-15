# GEN step prep (cloud-only window 03:45-06:15, 2026-11-12)

Prepared 2026-11-12 ~00:40 PT by the Lead. Nothing here has been sent or run. Plan source: `stages/00_prep/references/jam-execution-plan.md` (Queue row). Local AI is OFF for the jam, so every step below uses a cloud provider.

## Start condition (hard gate)

```bash
python3 scripts/greybox_gate.py check --project ~/Projects/megajam-game/JumpCut.uproject
```

Must pass (won, lost and restarted recorded). `status` said "not proven" at 00:25. Record it from Yo's real B4 run, not from `-JCWrapTest`:

```bash
python3 scripts/greybox_gate.py record --won --lost --restarted --run <Yo run id> --note "<log lines>" --project ~/Projects/megajam-game/JumpCut.uproject
```

## Inputs (all exist)

- Look: `stages/01_concept/output/prejam/style-guide.md` (palette, film look, sets), `storyboards.md`, `concepts.md`, `reference-images/`.
- Providers ready at 00:36 (`python3 scripts/gen_asset.py --providers-check`): concept images grok, fal, gpt (local krea is off); 3D meshy, tripo, hyper3d, fal. Music: `gen_music.py` is local ACE-Step, so it is OFF; a cloud music path is not set up (decide with the hub).
- Needed from the hub or owner before sending: the 3 art directions (one line each) and the 6 props to build (names, class, height_m). I have not invented them.

## Commands (dry-run: print only, do not run until the gate passes)

1. Concept images, 3 directions x 4 (cloud lanes in parallel; sidecar and log record the provider):
   `python3 scripts/gen_asset.py --name dirA_01 --provider grok --prompt "<direction A, style-guide palette>" --out-dir work/generated/concepts` (repeat per direction, provider grok / fal / gpt; never `--model` anything non-commercial).
2. Props: write `work/queue.yaml` as a list of `{name, prompt, class: prop, height_m}` then
   `python3 scripts/asset_chain.py --queue work/queue.yaml --workers 4 --max-tries 2` (3D provider auto = meshy first).
3. Import into a staging folder (not placed) from 06:30 with the editor, then save and VERIFIED.

## Guard rails

- Licensed models only; no Hunyuan3D, Qwen-Image 2.1, ultrasharp. Cloud providers only with key and `*_TERMS_REVIEWED` in `~/.config/megajam.env`.
- Generated content must be original; list sourced assets (Rule 15(c)). One GPU/editor workload at a time; the editor is closed during the GEN window anyway.
- Every output gets a sidecar and a row in `stages/02_build/output/asset-pipeline-log.csv`.

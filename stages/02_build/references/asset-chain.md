# Asset chain (`scripts/asset_chain.py`)

One command turns a prompt (or a reference image) into a game-ready Unreal prop. PR 1 scope (hub27 order):
**props only**. Characters, auto-rig and LOD1-2 are PR 2 if time allows. **Freeze: Tue Nov 10 17:00 PT.**
Declared pre-jam tool (Rule 7(h)): it is a script, it contains no gameplay, levels or art.

## Stages

| # | Stage | Engines (speed-first order) | Lane |
|---|---|---|---|
| 1 | image | `local` (Krea) > `grok` > `gpt`; `reference-image` if you pass `--image` | gpu / cloud / cloud |
| 2 | 3d | `triposplat` (MIT, via `nexus-3d --model triposplat`) | gpu |
| 3 | texture | `passthrough` (TripoSplat bakes albedo into the GLB; a texture engine slots in here later) | cpu |
| 4 | cleanup | `blender` headless: weld, scale, pivot to base, decimate to class budget, UV check, UCX collision hull, `M_<name>` slot, thumbnail | cpu |
| 6 | export | FBX (cm, mesh + UCX hull) + GLB (m) + `ue_import_manifest.json/.py` | cpu |
| 7 | QA | `qa.json`: tris vs budget, bbox, UV status, thumbnail, licence line | cpu |

Stage 5 (rig) is PR 2. To flip an engine order, edit the one `ORDER = {...}` dict in `scripts/chain/engines.py`,
or force one run with `--engine image=gpt`. `--list-engines` prints each engine with its licence verdict.

Tri budgets per `class`: `prop_small` 1500, `prop` 5000 (default), `prop_large` 15000, `hero_prop` 30000, or set `tri_budget`.

## Run

```bash
cd ~/Projects/megajam
python3 scripts/asset_chain.py --name crate --prompt "weathered wooden crate, game prop" --class prop --height-m 0.8
python3 scripts/asset_chain.py --queue work/queue.yaml --workers 4
```

Queue file (YAML or JSON list, or `{assets: [...]}`):

```yaml
- {name: crate, prompt: "weathered wooden crate", class: prop, height_m: 0.8}
- {name: lamp, image: work/refs/lamp.png, class: prop_small, engines: {image: reference-image}}
```

`--expect-aspect A:B[:tol]` applies to every asset in the run. A queue entry can carry its own `aspect`, which
overrides the flag for that asset only, so a mixed queue (crate 1:1, lamp_post 1:4) does not fail the wrong assets.
**Quote the value: `aspect: "1:4"`.** Unquoted, YAML reads `1:4` as the number 64. One entry with a bad aspect
(unquoted, or not `A:B` / `A:B:tol`), or an entry that is not a mapping, fails alone: its line says which entry and
why, nothing is generated for it, and the rest of the batch still runs. The preview check also rejects meshes with
non-manifold edges or a flat shape.

Output: `work/generated/chain/<name>/` (git-ignored): `game/<name>.fbx|.glb`, `thumb.png`, `qa.json`,
`provenance.json`, `ue_import_manifest.json`, `ue_import_manifest.py`, `state.json`.

## Optimizations

- **Lanes.** GPU stages run strictly one at a time (a thread semaphore plus a file lock, so two chain
  processes also never overlap), each behind `gpu-preflight`. Cloud engines run in parallel (`--cloud-lanes`,
  default 4). Blender cleanup runs in parallel subprocesses (`--cpu-lanes`, default 3).
- **Resume.** `state.json` keeps a hash per stage (stage, params, input file hashes). A rerun skips stages whose
  hash and output still match; change the prompt and it redoes everything, change `tri_budget` and only cleanup reruns.
- **Auto fallback.** With no forced engine, the chain walks the order and skips engines that are refused by the
  licence gate or not ready/failed. A forced engine (`--engine`/`engines:`) never falls back.
- **Log.** One row per stage in `stages/02_build/output/asset-pipeline-log.csv`, stage label `chain:<stage>:<engine>` (`:skipped` on resume, exit 3 = licence refusal).

## Licence gate

Every engine is checked against `config/asset-licenses.json` (written by the licence-audit ticket) and refused
unless its verdict is `ok` or `ok-with-credit`. Hunyuan, Qwen-Image and UltraSharp are refused even if listed.
If the file is missing the chain warns and allows only: triposplat, gpt, Krea, Blender, passthrough, reference-image
(so `grok` is refused until the file lands). The file shape is read flexibly: `{name: {verdict, credit}}`, or the same
under `engines` / `models` / `tools`, or a list of `{name, verdict, credit}`. Lookup tries `stage:name`, `name`, then
aliases (`krea-2-turbo`, `openai`, `xai`...). **Check the real file's keys once it lands** and add aliases in
`engines.py` if a name does not match.
Credit text is gathered into `stages/02_build/output/credits.md` (between the `chain:` markers) and into each `qa.json` licence line.

## Where it runs

The chain runs on the **Linux** side (Nexus, Krea and TripoSplat are Linux-only). If the jam machine is dual-booted
into Windows (win-plan item 2), run the queue on Linux first and copy `work/generated/chain/<name>/game/` plus
`ue_import_manifest.json` across; then in the UE editor run `ue_import_manifest.py` after editing the two paths at
its top if the folder moved. Cloud-only runs (`--engine image=gpt`/`grok` with an image supplied) still need
Nexus for stage 2 until another 3D engine is added.

## Status and owner steps

- Tests: `python3 -m unittest tests.test_asset_chain` (fakes only: queue, resume, lane limits, licence refusal, sidecar).
- Blender cleanup verified on a synthetic sphere (Blender 5.2.3): 3968 to 500 tris, pivot at base, UCX hull, FBX/GLB/thumbnail written.
- **Not yet verified (no timings yet):** the real smoke run (3 props), because `gpu-preflight` was not clear when this was built, and
  the UE import (`ue_import_manifest.py`) inside the editor. Owner steps: free the GPU (`nexus-route local-down`), run
  `python3 scripts/asset_chain.py --queue <3 props>`, paste timings from `stages/02_build/output/asset-pipeline-log.csv` here.
- Not in this PR: characters and auto-rig, LOD1-2, Meshy/Tripo/TRELLIS.2 engines (they plug in by adding an `Engine`
  to `build_registry()` once their licence entries exist), cloud rig engine.
- Changes wanted in `gen_asset.py`/providers: none (the chain imports `providers` and `gen_asset.merged_env` read-only).

| Run | Asset | image | 3d | cleanup | total |
|---|---|---|---|---|---|
| (pending first smoke run) | | | | | |

## Real GPU smoke 2026-11-07 (T-20261107-14): PASS, 3 props end to end

`gpu-preflight` was CLEAR before each prop. Real engines only: local Krea (`nexus-image --model krea-2-turbo`), `triposplat`, `passthrough`,
Blender. No cloud engine, no Hunyuan, no Unreal Editor. Each prop ran in its own scope
(`systemd-run --user --scope --unit=megajam-chain-smoke-<prop> -p MemoryHigh=26G -p MemoryMax=28G -p MemorySwapMax=8G`) with
`--engine image=local --class prop --workers 1`, run by the hub. Peak VRAM is the max of `mem_info_vram_used` (card is 16 GiB).
Outputs are in `work/generated/smoke-20261107/<prop>/` (git-ignored, not committed).

| Prop | image (local) | 3d (triposplat) | texture | cleanup | Total | Peak VRAM | Tris / budget | UV | Warnings |
|---|---|---|---|---|---|---|---|---|---|
| water_barrel | 84.8 s | 100.5 s | 0 s | 1.3 s | 187 s | 14.5 GiB (15.56e9 B) | 4999 / 5000 | present | none |
| balloon | 71.4 s | 86.3 s | 0 s | 1.4 s | 160 s | 14.5 GiB (15.56e9 B) | 5000 / 5000 | present | none |
| crate | 64.1 s | 214.4 s | 0 s | 1.3 s | 280 s | 15.7 GiB (16.86e9 B) | 5000 / 5000 | present | none |

Per prop output: `concept.png`, raw + high GLB, albedo/normal/ao maps, `provenance.json` (per-stage engine, seconds, licence verdict,
output sha256), `qa.json` (licence line `image=local(ok), 3d=triposplat(ok), texture=passthrough(ok), cleanup=blender(ok)`),
`game/<name>.glb` + `.fbx` + `thumb.png` + `cleanup_report.json`, `ue_import_manifest.json/.py`. No credit lines were needed (all verdicts `ok`).
`--list-engines`: local, triposplat, passthrough, blender, gpt are `ok`; grok is REFUSED (`unclear`).

Notes:
- The crate peaked at 15.7 of 16 GiB VRAM. Nothing else can share the card during a chain run, and a bigger prop could run out.
- Both 5000-tri props sit exactly on the `prop` budget, so decimate is doing real work. 3D (TripoSplat) is the slow stage (86-214 s).
- The balloon's longest side is about 1 m (no `--height-m` was passed), so scale was not set by the chain on these runs.
- The UE import step is still owed to the owner (no Editor was run).

**GPU runs must start in their own scope.** A first attempt from the ticket worker's cgroup (`MemoryHigh=10G / MemoryMax=12G`) failed at
stage 1 twice (472 s and 313 s): `nexus-image` returned `could not read history: timed out`, and the ComfyUI log stopped at
`Requested to load Krea2`. `nexus-image` starts ComfyUI as a child, so it inherits the caller's cap and stalls while loading Krea. In its own
26G/28G scope the same prompt loads and runs fine. See AGENTS.md ("Launch each GPU job ... in its own scope").

**Fix made:** `_provider_engine` in `scripts/chain/engines.py` threw away the per-attempt detail, so the chain only said
`no provider produced a concept image (local=failed)`. It now appends the detail (test: `ProviderErrorDetailTest`).

**Still owed:** the UE import of the three `game/*.fbx` files (owner, with the Editor).

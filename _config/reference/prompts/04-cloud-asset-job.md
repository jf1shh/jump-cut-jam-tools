# 04 Cloud asset job (concept image to 3D, through `gen_asset.py`)

**Purpose:** make one game asset from a concept image with the repo adapters, locked to the style guide, labelled, with
provenance, and with the money spent kept in view.
**When:** only after the grey-box gate passes (`greybox_gate.py check` exits 0; any other code means stop), one asset or one
small batch per job.
**Lead sends to:** an asset helper (file and network, no Unreal MCP). The lead imports the result.
**Model:** Sonnet for the job; Haiku to re-read the log and write the one-line cost summary.
**Local AI is off:** never use `--provider local`, never `--provider auto` (its order still includes `local`), and never the local `--3d-provider` fallback (TripoSplat). Name a cloud
provider for each stage. A forced provider never falls back, so a failure comes back to you instead of starting a
local model. `asset_chain.py` is not used for 3D in the jam: its only 3D engine is local TripoSplat.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{name}` | asset id: letters, digits, `_`, `-` only |
| `{what}` | one sentence: what the asset is and where it appears (a prop, a stunt part, a set piece) |
| `{class}` | `prop_small`, `prop`, `prop_large` or `hero_prop` |
| `{style_sections}` | the `style-guide.md` sections to lock to (always 1 look pillars, 2 palette, 11 do not; add 5 hero car or the scene's 6 set) |
| `{image_provider}` | `gpt`, `fal` or `grok`; only what `--providers-check` shows READY, and `grok` only if the brief names it |
| `{threed_provider}` | `meshy`, `tripo`, `hyper3d` or `fal`; only what is READY |
| `{max_image_calls}`, `{max_3d_calls}` | the spend cap, set by the hub (default 2 and 1) |

**Cost awareness** (from `_config/reference/ai-providers.md`; prices read 2026-11-07 and 2026-11-10, recheck on the
vendor page if a number matters):

| Stage | Provider | About |
|---|---|---|
| image | `fal` (FLUX schnell) | $0.003 per 1024x1024 |
| image | `gpt` | ChatGPT plan quota, no cash; about 25 s seen |
| image | `grok` | billed per image on the xAI API; never run against the real API before |
| 3D | `meshy` | about 30 credits per model (20 untextured, 35 with 8K), prepaid |
| 3D | `tripo` | about $0.30 with texture, $0.20 without; Tripo web credits do not pay the API |
| 3D | `fal` (Rodin Gen-2.5) | $0.40 per generation |
| 3D | `hyper3d` | 0.5 credit per Gen-2.5 model; whether the 213 plan credits cover the API is unknown |

Ownership and licence of Meshy, Hyper3D and Tripo output is "treat as paid, confirm before it ships" in the doc: the
owner confirms before a hero asset ships.

## Prompt

```text
{HOUSE_RULES}

You make ONE asset: {name}, {what}. You do not call Unreal MCP and you do not import into Unreal; the lead does.

1. Gate: python3 ~/Projects/megajam/scripts/greybox_gate.py check --project "$UPROJECT". If the exit code is not 0,
   stop and report BLOCKED.
2. Providers: python3 ~/Projects/megajam/scripts/gen_asset.py --providers-check (spends nothing). Use only
   {image_provider} for the image and {threed_provider} for 3D, and only if its line says ready. If not, report BLOCKED;
   do not switch to another provider and never to local.
3. Style lock: read the sections {style_sections} of
   ~/Projects/megajam/stages/01_concept/output/prejam/style-guide.md. Write the concept prompt from them: the pillars,
   the palette names and values, the silhouette rules, the "do not" list. Original design only: no real brand, car make,
   film, character or logo. One object, plain backdrop, whole object in frame, no text in the image.
4. Run (one call; swap in the chosen providers):
   python3 ~/Projects/megajam/scripts/gen_asset.py --name {name} --prompt "<your prompt>" --provider {image_provider} --3d-provider {threed_provider}
   Image attempts at most {max_image_calls}, 3D attempts at most {max_3d_calls}. A failure is reported, not retried
   past the cap.
5. Look: Read the concept PNG. Does it match the style lock and the brief? If not, rewrite the prompt once (within
   the cap). Then render the preview: python3 ~/Projects/megajam/scripts/asset_preview.py <asset folder> and Read
   preview.png: shape, scale, materials, triangle count against the {class} budget.
6. Provenance: confirm <name>.glb.provenance.json exists (it records provider, model, task id and terms dates) and that
   stages/02_build/output/asset-pipeline-log.csv has a row for each attempt. Do not edit either by hand.
7. Report the paths, the provider and model used, calls made, and what it cost in dollars or credits. Never print a key.
```

## Done when

The GLB, `preview.png`, the sidecar and the CSV rows exist; you looked at the concept and the preview and described
them; spend is stated.

## Reply format

House format, plus `Asset:` (GLB path), `Preview:` (PNG path), `Provider:` (image and 3D, with model), `Spent:`
(calls, dollars or credits), `Looks:` (two sentences from your own look at the preview, including any defect).

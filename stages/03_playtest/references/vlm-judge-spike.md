# VLM judge spike (T-20261108-27)

Status: **written, not yet run on the GPU.** The code and tests are done; the real smoke run waits for
mock 11 to end (hard stop ~02:58Z 11-09) and is done by the hub with `gpu-preflight` clear.

Goal: a local vision model looks at one playtest frame and says whether the HUD is readable, a title
line is present and the camera is steady. It is a second opinion beside the human/agent checklist in
`stages/03_playtest/references/playtest-gate.md`. It never replaces `visual_playtest.py verify`.

Everything is local. No cloud API. The model host is Lemonade (`lemond`, port 13305), the only local
model host on this box.

## Two ways to use it

1. **`scripts/vlm_judge.py` (the main path).** Plain Python, calls Lemonade's OpenAI-compatible
   endpoint directly with the frame as base64. Needs no ComfyUI.
2. **ComfyUI_VLM_nodes (optional).** `gokayfem/ComfyUI_VLM_nodes` (Apache-2.0) for eyeballing a frame by
   hand in a graph, or trying other prompts. Same Lemonade endpoint through its Custom/Local profile.
   Do this only if the CLI proves useful and you want a graph view; skip it otherwise.

## Rules while running (do not skip)

- **One GPU workload at a time.** Run `gpu-preflight` first; it is the gate. The judge model and the
  editor, Krea, TripoSplat and ComfyUI generation cannot share the box.
- Never run any of this while a mock jam run is using the GPU.
- Leave Flash Attention 2 **off**. Moondream Photon has no ROCm: do not pick it. Qwen 3.5/3.6 are slow
  without optimized kernels: do not pick them. Skip the nodes' GGUF path (it needs a ROCm/Vulkan
  `llama-cpp-python` wheel); Lemonade already serves GGUF.
- Keep ComfyUI's ROCm torch. Never `pip install` torch over it.
- Never set `PYTORCH_HIP_ALLOC_CONF=expandable_segments:True`.

## Steps

1. Gate: `gpu-preflight` must print `CLEAR`. If a Lemonade model is resident and you need the VRAM for
   something else, `lemonade unload` first.
2. Pick a vision model Lemonade can serve. See what it has: `lemonade list`. First choice is a
   Qwen3-VL GGUF around 8B (the script's default name is `Qwen3-VL-8B-Instruct-GGUF`; set the exact name
   with `--model` or `VLM_JUDGE_MODEL`). Fallback: a Gemma 3 GGUF with vision (4B or 12B). Pull it only
   if missing, and only when the owner/hub says a download is fine.
3. Load it alone, with the standard context size:
   ```bash
   lemonade load Qwen3-VL-8B-Instruct-GGUF --ctx-size 32768
   ```
   Never 8192. If the vision part needs a projector file, the GGUF entry in Lemonade must include it;
   if `lemonade list` shows the model without vision, pick another.
4. Dry run (safe anytime, touches no GPU):
   ```bash
   ./scripts/vlm_judge.py --dry-run /path/to/vp_r3/
   ```
5. Real run on one frame, then on a folder (judges the newest `.png`):
   ```bash
   ./scripts/vlm_judge.py /path/to/frame.png
   ./scripts/vlm_judge.py /path/to/vp_r3/
   echo $?   # 0 pass, 2 fail, 3 unavailable
   ```
6. In the gate: `visual_playtest.py run ... --vlm-judge`. The verdict is added to `results.json`
   (key `vlm_judge`) and to the end of `checklist.md` as an advisory section. It is off by default and a
   judge error is recorded as `"status": "unavailable"`; it never fails the gate.
7. When done, restore the usual model: `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768`
   (or leave it unloaded if the next job needs the GPU), then check `gpu-preflight` shows the truth.

### Optional: ComfyUI_VLM_nodes

Only after step 5 works. With `gpu-preflight` clear and Lemonade **unloaded or not in use** (ComfyUI is
a GPU workload too):

1. `cd <ComfyUI>/custom_nodes && git clone https://github.com/gokayfem/ComfyUI_VLM_nodes`
2. Install its requirements into ComfyUI's existing venv **without touching torch**: review
   `requirements.txt`, and drop any line that pins or replaces `torch`, `torchvision` or `llama-cpp-python`.
3. In the node's Custom/Local profile set base URL `http://127.0.0.1:13305/v1`, model = the Lemonade name,
   no API key (any placeholder). Use the JSON-schema structured output with the schema below.
4. Load an image, run the node, compare with the CLI's verdict on the same frame.

Installing nodes changes the ComfyUI folder: do it by hand or by the hub, not from a ticket worker.

## The verdict schema

```json
{
  "hud_readable": true,
  "title_line_present": true,
  "camera_steady": true,
  "issues": ["short strings, one per problem"],
  "confidence": 0.0
}
```

- `hud_readable`: every HUD element visible and its text legible. No HUD at all counts as false.
- `title_line_present`: a title, level name or objective line is on screen.
- `camera_steady`: a normal stable view; not tilted, clipped into geometry, black, or smeared.
- `issues`: strings; empty when none.
- `confidence`: 0 to 1.

The request carries this as `response_format: json_schema` (strict). Lemonade's llama.cpp backend
turns it into a grammar so the reply is always valid JSON. If a server ignores `response_format`, the
script still parses the text (a ``` fence is tolerated) and validates every field.

## Pass / fail / unavailable

| Exit | Meaning |
|---|---|
| 0 | all three flags true |
| 2 | at least one flag false (see `issues`) |
| 3 | no verdict: endpoint down, HTTP error, reply not valid JSON or a field missing, no frame found |

`confidence` is reported but does not change the exit code. Treat a pass with confidence under about 0.6
as "look at the frame yourself". The endpoint must be loopback; a remote URL is refused unless
`--allow-remote` is given (it should not be: local only).

## What the smoke run must settle (accuracy first)

Run on frames whose answer you already know, not just good ones:

- A known-good HUD frame: expect 0.
- A frame with the HUD cropped or hidden; a frame with no title line; a black or tilted frame: expect 2
  with a matching `issues` entry. If the model says pass on any of these, it is not a usable judge yet:
  try the other model, or tighten the prompt in `scripts/vlm_judge.py` (`PROMPT`).
- Run the same frame 3 times (temperature is 0, so verdicts should match).
- Note seconds per frame and peak VRAM, and whether `gpu-preflight` goes CLEAR again after unload.

Only after a real run proves a lesson, add a note under `_config/reference/canon/` and a CANON row. Until then this
doc is a plan, not evidence.

## Files

- `scripts/vlm_judge.py`: the CLI (`--endpoint`, `--model`, `--timeout`, `--dry-run`, `--allow-remote`).
- `tests/test_vlm_judge.py`: tests against a fake local endpoint; no GPU.
- `scripts/visual_playtest.py`: `run --vlm-judge` (advisory section, see `attach_vlm_judge`).

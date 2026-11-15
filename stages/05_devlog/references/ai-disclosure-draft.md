# Tools-used ledger and AI-use disclosure — DRAFT (owner reviews, edits and posts; never posted by an agent)

Two jobs in one file:
1. **A running "tools used" ledger** (section 0). The submission form has a **"Tools you used"** field, and the
   official perks email (relayed by the hub 2026-11-11) says to keep track of every tool used for it. The hub and
   agents **append a row the first time a tool is actually used in the entry** during the jam. Never delete a row;
   if a tool is later dropped from the build, say so in its notes.
2. **The AI-use disclosure** (sections 1-6): every AI tool and model the setup *can* call, written 2026-11-11
   before the window from what this repo records. It is a candidate list, not proof of use; the ledger is the proof.

Why the disclosure exists: Rule 9 says the extent of AI use is context for judges, not a score change; the
submission checklist in `stages/00_prep/references/win-plan.md` asks for a short AI-use disclosure; itch.io's generative-AI fields need
the same answers; Rule 7(h) means Epic may ask for the pre-jam declaration trail
(`stages/00_prep/references/pre-jam-declaration-2026-10-29.md`, tag `pre-jam-tooling`). AI-generated content is not a sourced asset
(Rule 15(c)); sourced assets are listed separately with `python3 scripts/sourced_assets.py credits`.

Every `OWNER-FILL` needs the owner before posting:
`grep -n OWNER-FILL stages/05_devlog/references/ai-disclosure-draft.md` must print nothing on the posted copy.

## 0. Tools-used ledger (append during the jam)

### Partner prizes that depend on this list (from the perks email, relayed by the hub 2026-11-11)

- **Hyper3D: $10,000 cash pool.** Depends on listing Hyper3D in "Tools you used". Only list it if Hyper3D Rodin
  (direct API or `fal-ai/hyper3d/rodin/v2.5`) really made an asset in the entry; the ledger row needs the asset's
  `.provenance.json` sidecar or its `stages/02_build/output/asset-pipeline-log.csv` row (`3d:hyper3d` or `3d:fal`) as evidence.
- **NVIDIA RTX Award.** Needs at least one **NvRTX, DLSS or ACE** feature in the entry. None is set up in this repo
  as of 2026-11-11 (no plugin, config or script mentions one). The desktop GPU is an AMD RX 9070 XT (`AGENTS.md`), so an NVIDIA-only feature such as DLSS could not be checked on it. If one is added, log it here with the plugin/config
  commit as evidence and check it works in the packaged Windows build on the Legion. OWNER-FILL: go / no-go.

### How to add a row

One line per tool, in order of first use. Time is Pacific. Evidence is a commit, PR, sidecar, log row, screenshot
or `stages/05_devlog/output/evidence.md` entry, never a claim alone. "Kind" is one of: engine, plugin, AI model, AI service,
agent, pipeline tool, service.

| Tool (name + version/model) | Kind | What for in the entry | First used (PT) | Evidence | Notes (prize, licence) |
|---|---|---|---|---|---|
| Unreal Engine 5.9 MegaJam Preview | engine | The game (Development config, D-009) | OWNER-FILL (window opens 2026-11-11 21:00) | OWNER-FILL: first jam commit | Required |

Candidates already set up (move to the ledger when first used): Epic Unreal MCP plugin (AllToolsets), Claude Code
with Claude models, butler (itch upload), OBS (gameplay video, `scripts/legion_obs_record_test.ps1`), and every AI
row in sections 1-4 below.

## 1. Coding, planning and review agents

| Tool / model | What it did | Where recorded | Used in the entry |
|---|---|---|---|
| Claude Code with Claude models (Opus, Sonnet, Haiku; Fable for some hardest-call reviews, e.g. the 2026-11-10 execution-plan ruling) | Lead agent (the only Unreal MCP caller), hub, worker and reviewer sessions: C++/Blueprint/Python, editor driving, docs, dev log drafts, judge pass | git history, PRs, `stages/00_prep/references/jam-execution-plan.md` section 7 | OWNER-FILL |
| Epic Developer Assistant (asked by hand) | Unreal questions queued by agents with `scripts/epic_ask.py`, typed into the Assistant and pasted back by the owner; never automated; answers verified before use | `Epic Assistant questions.md` (Obsidian), Q-ids in commits | OWNER-FILL |
| Epic Unreal MCP plugin (UE 5.9, AllToolsets) | The interface the lead agent used to drive the editor (not a model) | `AGENTS.md`, `_config/reference/canon/jam-ue59-upgrade.md` | OWNER-FILL |
| Local Lemonade models: Qwen3-Coder-30B, gpt-oss-20b | Routed coding and reading scopes (`nexus-route` local lane) | `stages/04_ship/references/jam-recovery.md` (S1), routing logs | OWNER-FILL |
| Local Lemonade: Qwen3-VL-8B-Instruct (GGUF) | Visual judge of playtest frames (`scripts/vlm_judge.py`) | `stages/03_playtest/references/vlm-judge-spike.md` | OWNER-FILL |
| Codex CLI (ChatGPT plan) | Helper for source/script/doc edits; never the MCP caller | `_config/reference/ai-providers.md` (helper agents) | OWNER-FILL |
| Cursor `agent` CLI (jam perk credit) | Fallback helper if Claude is rate-limited; needs the owner's `agent login` | `stages/04_ship/references/jam-recovery.md` (S1), `stages/00_prep/references/jam-execution-plan.md` | OWNER-FILL |
| Grok Build | Not installed when this was written; delete this row unless the owner installs and uses it | `_config/reference/ai-providers.md` | OWNER-FILL |

## 2. Art: concept images, textures, upscaling

| Tool / model | What it did | Where recorded | Used in the entry |
|---|---|---|---|
| Krea 2 Turbo (`krea-2-turbo`) via local Nexus `nexus-image` | Concept images and textures | sidecar `image_provider`, `stages/02_build/output/asset-pipeline-log.csv` | OWNER-FILL |
| GPT image (`gpt-image-2` via the codex bridge) | Concept images | same | OWNER-FILL |
| Grok `grok-imagine-image-2.0` (xAI API) | Concept images (never run against the real API before the jam) | same | OWNER-FILL |
| fal `fal-ai/flux/schnell` (FLUX.1 [schnell]) | Concept images (cloud, opt-in) | same | OWNER-FILL |
| Real-ESRGAN `realesrgan-x4plus` via `nexus-upscale` | Texture upscaling | sidecar | OWNER-FILL |

## 3. 3D meshes

| Tool / model | What it did | Where recorded | Used in the entry |
|---|---|---|---|
| Meshy (cloud, model `latest`; meshy-7.1 when checked) | Image-to-3D, first choice when configured | sidecar, `stages/02_build/output/asset-pipeline-log.csv` (`3d:meshy`) | OWNER-FILL |
| TripoSplat via local Modly (`nexus-3d --model triposplat`) | Image-to-3D fallback (albedo only) | same | OWNER-FILL |
| Tripo API (`v3.1-20260211`) | Image-to-3D (cloud, opt-in) | same | OWNER-FILL |
| Hyper3D Rodin Gen-2.5 (direct API, or via fal `hyper3d/rodin/v2.5`) | Image-to-3D (cloud, opt-in) | same | OWNER-FILL |

## 4. Audio

| Tool / model | What it did | Where recorded | Used in the entry |
|---|---|---|---|
| ACE-Step 1.5 via local Nexus (`scripts/gen_music.py`) | Music | `stages/02_build/output/audio-pipeline-log.csv` | OWNER-FILL |
| Sound effects / voice | OWNER-FILL: name the tool if any was used, or delete this row | | OWNER-FILL |

## 5. Not used (banned by our licence audit, `stages/00_prep/references/license-audit-asset-chain-2026-11-07.md`)

Hunyuan3D (all versions), Qwen-Image 2.1, 4x-UltraSharp. The contest guard and `gen_asset.py` block them.
Note: the "AI-generated content disclosure (planned)" line in `stages/00_prep/references/win-plan.md`'s submission checklist still
names "Tencent Hunyuan3D 2.0 if it is still used"; it is not, so the posted credits must not list it.

## 6. Short version for the itch page and the entry form (OWNER-FILL: trim to what was actually used)

> Built solo with AI agents. Code, editor work and docs: Claude (Anthropic) through Claude Code and Epic's
> Unreal MCP plugin, with local models on Lemonade for some routed tasks. Art: concept images machine-generated
> (Krea 2 Turbo locally; GPT image / Grok / FLUX.1 schnell where noted), upscaled with Real-ESRGAN. 3D meshes
> machine-generated (Meshy / TripoSplat / Tripo / Hyper3D Rodin where noted). Music machine-generated (ACE-Step
> 1.5). Every generated asset has a provenance sidecar in the repo. Sourced assets, if any, are listed separately.
> Before the jam we built only tools, scripts, prompts and agent configs (tag `pre-jam-tooling`).

itch.io generative-AI fields: tick **Graphics** and **Sound** if section 2-4 rows were used (per
`stages/00_prep/references/win-plan.md`); add **Code** or **Text** too if the form offers them. OWNER-FILL: confirm on the live form.

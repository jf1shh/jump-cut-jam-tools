# AI providers: concept images and helper agents

Written 2026-11-06 for ticket T-20261106-14. Pre-jam tooling only (Rule 7(h)). Owner decision
2026-11-06: "yes allow gpt photos"; the pipeline must be able to plug in ChatGPT and Grok, and must not
stall if one is unavailable.

## Concept-image providers (`scripts/gen_asset.py`)

```bash
python3 scripts/gen_asset.py --providers-check          # one line per provider, spends no quota
python3 scripts/gen_asset.py --name crate --prompt "..." --provider auto   # default
python3 scripts/gen_asset.py --name crate --prompt "..." --provider gpt    # force one, no fallback
```

**Policy (owner 2026-11-07): MegaJam is not local-only.** Anything the Official Rules allow is allowed; the
contest guard enforces only rules and licences (bans: Hunyuan3D all versions, Qwen-Image 2.1, 4x-UltraSharp,
raw curl/wget of store or asset pages; store assets only if licensed and listed as sourced assets, Rule 15(c)).
Cloud AI providers run only through a repo adapter and only when their key and `*_TERMS_REVIEWED` date are set.

`auto` tries providers in the order set by `AUTO_ORDER` in `scripts/providers/__init__.py` (one line;
default `grok, fal, local, gpt`: speed-first, since 2026-11-07; fal added 2026-11-10). A provider that is "not configured" or "down" is skipped. One that fails or times out is
logged and the next is tried. A forced provider (`--provider gpt`) never falls back.
Per-provider timeouts (`TIMEOUTS`, same file): local 900 s, gpt 600 s, grok 120 s, fal 120 s.

Every attempt is a row in `stages/02_build/output/asset-pipeline-log.csv` (stage `image:<provider>`, exit code 0 or 1).
The sidecar `<name>.glb.provenance.json` records `image_provider`, `image_provider_model`,
`image_provider_attempts` and `local_only` (false when GPT or Grok made the image).

| Provider | What it calls | Setup | Limits |
|---|---|---|---|
| `local` | `nexus-image --model krea-2-turbo` | Nexus on PATH; `gpu-preflight` clear | GPU: one workload at a time |
| `gpt` | `~/.claude/skills/gpt-image-bridge/bin/gpt-image-2` (codex CLI, ChatGPT plan) | `codex login status` must say "Logged in using ChatGPT". Owner logs in; an agent never runs `codex login` | Spends ChatGPT plan quota. Observed 25 s for a test image on 2026-11-06 (older notes say 4-6 min). Plan message caps apply and are not published as a fixed number |
| `grok` | `POST https://api.x.ai/v1/images/generations`, model `grok-imagine-image-2.0` | Key in env var `XAI_API_KEY` only (below) | Billed per image on the xAI API; rate limits are not listed on the docs page (see docs.x.ai pricing) |
| `fal` | fal queue API, model `fal-ai/flux/schnell` (FLUX.1 [schnell], Apache-2.0) | `FAL_KEY` + `FAL_TERMS_REVIEWED` (see "fal, Hyper3D Rodin, Tripo" below) | $0.003 per megapixel (about $0.003 for one 1024x1024 image), paid from fal credit |

Source for the xAI endpoint and model: https://docs.x.ai/docs/guides/image-generation (read 2026-11-06). The page
does not show the raw response or the field names for count/format, so the code accepts either
`data[0].b64_json` or `data[0].url`. **The Grok path has never been run against the real API**
(no key on this machine). Test it once with a throwaway prompt when the key exists.

### Owner: create the xAI key (agents never ask for, print, store or commit a key)

1. Create a key at https://console.x.ai (API keys), with a spending limit.
2. Put it in a private env file the loop reads, then lock it down:

```bash
install -m 600 /dev/null ~/.config/megajam.env && printf 'XAI_API_KEY=PASTE_KEY_HERE\n' > ~/.config/megajam.env
```

**Terms sign-off gate.** Even with a key, Grok stays "not configured" (also for `--provider grok`) until
you add `XAI_TERMS_REVIEWED=<date>` to the same file. Add it only after you have read xAI's live terms
(Licensing, below). The value is copied into the provenance sidecar (`image_licence_gate`).

Edit the file to paste the real key. `gen_asset.py` (and `--providers-check`) read
`~/.config/megajam.env` themselves: no `set -a; . file` needed. Rules: only `KEY=VALUE` lines
count (a leading `export ` is fine, `#` comments are skipped, nothing is run by a shell); a variable
already set to a non-empty value in the real environment wins over the file (an empty one, like
`XAI_API_KEY=`, counts as unset: the file's value is used and a warning is printed; to switch Grok off
for one run, use `--provider local` or `--provider gpt` instead); a line that is not `KEY=VALUE`
(for example `KEY = value`) is skipped with a warning that names the line number, never the value; values are never printed; and a file that is
group- or world-accessible is ignored with a warning (fix with `chmod 600 ~/.config/megajam.env`).
The values stay inside `gen_asset.py` and are not passed on to `nexus-*` or `codex`.
Check: `python3 scripts/gen_asset.py --providers-check` should show `grok: ready`.

The contest guard (`scripts/hooks/contest_guard.py`) blocks direct `curl`/`wget` to `api.x.ai` and
`api.openai.com`. Grok and GPT concept images go through `gen_asset.py --provider grok|gpt` only.

## Licensing (Rules 15(b), 15(c))

Both vendors' terms pages returned HTTP 403 to every fetch tool on 2026-11-06, so **the primary text could
not be read**. What follows comes from search-engine excerpts of those pages. Owner: read the clauses
below once in a browser before the jam.

- **OpenAI.** Terms of Use, https://openai.com/policies/terms-of-use/ (excerpted copy dated January 1, 2026,
  labelled "Previous version"; the live version may differ). Excerpt: "you (a) retain your ownership rights in
  Input and (b) own the Output", and OpenAI assigns its rights in Output to you, except other users' or
  third-party output. Restriction: you may not use Output to develop models that compete with OpenAI.
  Outputs may not be unique. Reading: shipping GPT images in a commercial game is allowed. No IP
  indemnity was found for consumer plans.
- **xAI.** Consumer terms, https://x.ai/terms-of-service (older snapshots, e.g.
  https://x.ai/legal/terms-of-service/previous-2025-06-09). Excerpt: "you retain your ownership rights to the
  Input, and you own the Output". Some versions also ask you to **attribute the service** (or get its
  permission) when using Output. Enterprise/API terms, https://x.ai/legal/enterprise/terms-of-service,
  word ownership differently across versions. **Unclear:** which terms govern an API key, whether the
  attribution duty still applies, and whether Grok Imagine output has extra limits. No indemnity found.
- **Rule 15(c).** AI-generated content is not a sourced asset (AGENTS.md, RULES.md), so GPT and Grok images
  need no entry in the sourced-asset ledger. Still record the provider (the sidecar does).
- **Rule 15(b) / Epic's publicity licence.** Nothing found in either excerpt blocks Epic's non-exclusive
  publicity licence. Unverified from primary text.
- **Decision recorded.** GPT: allowed (owner approved 2026-11-06). Grok: allowed only after the owner reads
  the live xAI terms; if the attribution duty applies, add the credit to the dev log and the itch page.
  The code enforces this: Grok is skipped until `XAI_TERMS_REVIEWED` is set (see above).
  Each provider attempt has one total time budget (busy retry and image download included); Ctrl-C or a
  timeout kills the provider's whole process group. Grok output must be a real image (PNG, or JPEG/WebP
  converted with Pillow); anything else counts as a failure and auto moves on.
- GPT or Grok images are still not UC2/UT2004 material (never, Rule 8) and not prompts naming third-party IP.

## Meshy: opt-in cloud 3D (`--3d-provider`)

Owner decision 2026-11-07 ("Yes, add Meshy"); owner read Meshy's terms (hub note 2026-11-07 18:21Z). Meshy is the
first cloud 3D adapter; Tripo, Hyper3D Rodin and Rodin-on-fal were added 2026-11-10 (next section). Local TripoSplat is the fallback. Store sites (Mixamo, Fab,
Sketchfab) are never fetched automatically: list any hand-picked, licensed store asset as a sourced asset.

```bash
python3 scripts/gen_asset.py --name crate --prompt "..." --3d-provider auto    # default: Meshy first if configured, local fallback
python3 scripts/gen_asset.py --name crate --image c.png --3d-provider meshy    # force Meshy, no fallback
python3 scripts/gen_asset.py --providers-check                                 # last line is "meshy (3d): ..."
```

`auto` is speed-first (hub, 2026-11-07): Meshy first when it is configured and reachable; if it fails, local
`nexus-3d --model triposplat` is the fallback. When Meshy is not configured, `auto` is local only. `local` never
uses Meshy. `meshy` never falls back.

Meshy output is never shipped raw: the adapter saves it as `<name>.meshy_raw.glb` (kept beside the final GLB), then
`nexus-3d handoff --glb <raw> --out <name>.glb` (CPU only) does the same game-ready and QA step as the local path. If the
handoff fails, the Meshy path counts as failed (`auto` falls back to local). Adapter safety checks: the input image must be
a real PNG/JPEG/WebP and never from UC2/UT2004 paths; the key goes only to `api.meshy.ai` and redirects are refused; the
GLB URL must be https and is fetched without the key; all reads run under a hard deadline.

**Command guard is an allow-list for cloud hosts.** If a Bash command names any cloud AI or store host (Meshy, Tripo,
OpenAI, xAI, Stability, Replicate, ElevenLabs, Suno, Mixamo, Fab, Sketchfab), `scripts/hooks/contest_guard.py` denies
it unless every piece of it (split on `; && || | |&` and newlines) is either `python3 <this repo's scripts/gen_asset.py>`
with plain arguments, or a known read-only command (`git commit/log/diff/show/status/grep/add`, `grep`, `rg`, `cat`,
`head`, `tail`, `peek`, `ls`, and `echo`/`printf` not piped on). Every piece must pass, including pieces that do not
name a host. Readers match by bare command name only (`/tmp/cat` is not a reader), and a reader may only pipe into
another reader. Anything with `$(`, backticks, `<(`, `<<`/`<<<`, a backslash or `#` outside quotes, `$'..'`/`$".."`,
text the shell parser cannot read, a leading `VAR=value` (also on the gen_asset run), a git reader with any option before
the subcommand (so no `git -c`/`-C`), `git --config-env`/`--ext-diff`/`--output`/`-O` (also inside a short-option
cluster) /`--open*` (abbreviations of those long options included, e.g. `--op`), any unquoted `(`
(subshells, zsh `=(cmd)` and glob qualifiers like `*(e:'cmd':)`; `{ ...; }` grouping is fine), or `rg --pre`/`-z`/`--hostname-bin` is denied. Git readers are exactly commit, log, diff, show,
status, grep and add. Pieces are matched on the raw first word, so `"cat;"` or `{cat}` is not `cat`.
The sanctioned run must be this checkout's own `scripts/gen_asset.py` (or the main checkout's) under `python3`.
Use `scripts/gen_asset.py`. Commands that name no cloud host are unaffected. A commit message that names a host must
not use `$(...)`/backticks/heredocs (use `-m "..."` plain).

Known limits:
- Variable indirection (`U=...; curl $U`) and split host strings (`'api.me' 'shy.ai'`) are not caught.
- Git hooks, filters and `.gitattributes` can still run programs when a git reader runs.
- The guard is a policy rail for our own agents, not a security boundary.
- The key file stays mode 600; agents never read or print it.

Each attempt is a row in
`stages/02_build/output/asset-pipeline-log.csv` with stage `3d:local` or `3d:meshy`. The sidecar gains `threed_provider`,
`threed_provider_model`, `threed_provider_task_id`, `threed_licence_gate`; `local_only` is false for Meshy.

**Owner setup.** Add two lines to `~/.config/megajam.env` (mode 600, same file as the xAI key). Agents never write or echo keys:

```bash
MESHY_API_KEY=PASTE_KEY_HERE
MESHY_TERMS_REVIEWED=2026-11-07
```

Without both, Meshy is "not configured" (also when forced). `MESHY_TERMS_REVIEWED` is already in the file as of 2026-11-07; the key is not.

**API (read 2026-11-07, https://docs.meshy.ai/en/api/image-to-3d).**
- Create: `POST https://api.meshy.ai/openapi/v1/image-to-3d`, header `Authorization: Bearer <key>`; body
  `image_url` (public URL or base64 data URI; JPG/PNG/WebP, max 20 MB, min 32 px). Reply `{"result": "<task_id>"}`.
  The adapter sends `ai_model: latest`, `should_texture: true`, `enable_pbr: true`, `target_formats: ["glb"]`.
- Poll: `GET .../image-to-3d/<id>` every 5 s. `status` is PENDING, IN_PROGRESS, SUCCEEDED, FAILED or CANCELED;
  `model_urls.glb` is the download (pre-signed, fetched without the key); `task_error` explains a failure.
- Errors: 401 bad key, 402 no credits, 403 moderation, 429 rate limit. A failure is a failed attempt, not a retry.
- Limits (https://docs.meshy.ai/en/api/rate-limits): 20 requests/s on every plan; concurrent tasks Pro 10, Premium 30,
  Studio 60 (20 on some older plans), Ultra 100. The page lists no free API tier.
- Credits (https://docs.meshy.ai/en/api/pricing): meshy-7.1/latest image-to-3D is 20 mesh-only, 30 with 2K textures,
  35 with 8K. Prepaid. Our default call costs about **30 credits** (the docs example shows `consumed_credits: 30`).
- Safety: one total time budget (900 s) covers create, polling and download; the key is redacted from every error and
  is never printed or stored; the GLB must start with the glTF magic or the attempt fails.

**Licence and ownership** (https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models, read 2026-11-07):
- Paid plan: "you retain full private ownership of all assets you create with Meshy", provided you do not publish them to
  the Meshy Community and your inputs (including uploaded images) do not infringe copyright.
- Free plan: CC BY 4.0 instead. Meshy asks you to credit it in the project description ("Model created with Meshy").
- Models made on a paid plan keep paid rights after a downgrade; later ones follow the free terms.
- Rule 15(c): AI-generated content is not a sourced asset, same reasoning as GPT and Grok. Record the provider (the sidecar does).
- **Do this:** use Meshy on a paid (prepaid-credit) account, and list Meshy in the dev log. If any asset was made on a free
  plan, add the CC BY credit to the itch page and dev log.

**Unclear (not verifiable from primary text; owner to confirm in the terms or with Meshy support):**
- `https://www.meshy.ai/terms` returned HTTP 404 to our fetch, so the full Terms of Service were **not read by an agent**;
  the ownership text above comes from the help-centre article, not the legal terms.
- Whether API-created assets always count as "paid plan" (credits are prepaid, but the docs do not say).
- Whether uploaded concept images or prompts are used to train Meshy models (the help article is silent).
- Whether the CC BY / "private" wording is compatible with Epic's non-exclusive publicity licence (Rule 15(b)); nothing found that blocks it.
- Output retention period (docs link an "Asset Retention" page we did not read); download the GLB right away (the adapter does).
- Exact credit cost for the `latest` alias on the day of the jam (docs list meshy-7.1 as latest on 2026-11-07).
- Open-source clients exist at github.com/meshy-dev (meshy-cli, MCP server, game-asset-pipeline; MIT). We use our own thin
  stdlib adapter: no Node, no new dependency to declare. Meshy's own model weights are not open.

## fal, Hyper3D Rodin, Tripo: opt-in cloud adapters (added 2026-11-10)

Owner ask 2026-11-10: enable, claim, install and test every partner perk. Pre-jam tooling only (Rule 7(h)): code,
tests and docs, no game assets. **None has been run against the real API** (no keys on this machine when written).
Run each once with a throwaway prompt after the key is in place.

| Provider | Flag | What it calls | Key / gate in `~/.config/megajam.env` | Cost per call |
|---|---|---|---|---|
| fal (image) | `--provider fal` (in `auto` after Grok); `--image-size WxH` for wide images, e.g. `2048x512` = 1 megapixel = $0.003 (fal sometimes returns 1536x512 for that request; check the size) | `queue.fal.run/fal-ai/flux/schnell` | `FAL_KEY`, `FAL_TERMS_REVIEWED` | $0.003 per megapixel (~$0.003 per 1024x1024 concept) |
| fal (3D) | `--3d-provider fal` | `queue.fal.run/fal-ai/hyper3d/rodin/v2.5`, tier Gen-2.5-Medium | `FAL_KEY`, `FAL_TERMS_REVIEWED` **and** `HYPER3D_TERMS_REVIEWED` (it is Hyper3D's model) | $0.40 per generation |
| Hyper3D Rodin | `--3d-provider hyper3d` | `api.hyper3d.com/api/v2/rodin` (+ `/status`, `/download`), tier Gen-2.5-Medium, GLB, PBR | `RODIN_API_KEY`, `HYPER3D_TERMS_REVIEWED` | 0.5 credit per Gen-2.5 model (Extreme-High +0.5); status, download and balance calls are free |
| Tripo | `--3d-provider tripo` | `openapi.tripo3d.ai/v3/files` upload, then `/v3/generation/image-to-model`, model `v3.1-20260211`, texture + PBR | `TRIPO_API_KEY`, `TRIPO_TERMS_REVIEWED` (already set 2026-11-07) | image-to-model with texture 30 credits = $0.30 (no texture 20); text-to-model 20 / 10; failed or cancelled tasks are not charged |

`--3d-provider auto` order is `THREED_CLOUD_ORDER` in `scripts/gen_asset.py`: **meshy, tripo, hyper3d, fal, then local
TripoSplat**. Each cloud provider is checked when its turn comes; without its key and terms date it is skipped at once
(no network, no log row), so an unconfigured provider never stalls `auto`. A configured one that fails gets a
`3d:<name>` row with exit 1 and `auto` moves on. A forced choice never falls back. Every cloud GLB is saved as
`<name>.<provider>_raw.glb`, then goes through `nexus-3d handoff` like Meshy output; the sidecar records
`threed_provider`, model, task id and the terms dates. Hyper3D and Tripo also have `generate_3d_from_text()`
(text-to-3D), tested but not wired into the CLI (the pipeline always has a concept image).

Shared safety rules (`scripts/providers/cloud.py`, same as Meshy): the key goes only to the vendor's API host (any other
URL is refused, including a fal `status_url` that points elsewhere); keyed requests never follow redirects; results
are downloaded without the key; the upload must be a real PNG/JPEG/WebP inside the repo and never a UC2/UT2004 path;
one 900 s budget covers the whole job; the key is redacted from every error; the GLB must start with the glTF magic.
`check()` (and `--providers-check`) is a TCP connect only and spends no credits. The contest guard now also blocks raw
`curl`/`wget` to `fal.run`, `fal.ai`, `fal.media` and `hyper3d.com`/`hyper3d.ai`.

### fal music (added 2026-11-12, MUSIC-1 worker)

`scripts/gen_music_fal.py` (adapter `FalMusicProvider` in `scripts/providers/fal.py`) makes music through the same fal
gate (`FAL_KEY` + `FAL_TERMS_REVIEWED`; the key goes to the queue host, plus one read-only GET to fal's pricing API).

| Model | Cost | Terms note | Use |
|---|---|---|---|
| `fal-ai/elevenlabs/music` | **$0.60 per output minute, rounded up to the minute** (live pricing API 2026-11-12: 0.6 per minute) | fal model page tag "Commercial use"; instrumental by negative styles in the composition plan | main score: a composition plan with named sections in one call |
| `fal-ai/stable-audio-25/text-to-audio` | $0.20 per clip (live API: 0.2 per audio) | fal page states no licence text: commercial terms **not verified**; runs only with `--accept-unverified-licence` | fallback: 34 s loop, wav, no negative prompt, no sections |
| `fal-ai/wizper` (speech-to-text) | fal lists "$0 per compute seconds" (really cents); ledgered at a conservative $0.05 per call | analysis only: our own generated music is sent, nothing from it ships | the machine **vocal gate**: `vocal-check take.wav` |

`gen_music_fal.py price | plan PRESET | gen | fetch | vocal-check` (see its docstring). Rules every paid call follows:

- **One live ledger, outside git.** `~/.local/state/megajam/cloud-spend-ledger.csv` (+ `.lock`) is shared by every
  worktree, so the $15 is one budget, and a `git checkout` / `reset` cannot rewind the spend. The path is fixed: no flag
  or environment variable moves it (round-3 review: an override was a fresh $15), and unit tests patch the module
  constant instead. The tracked `stages/02_build/output/cloud-spend-ledger.csv` is a copy refreshed after every write
  to the live ledger only (same bytes from any worktree; read back only to refuse a lost or behind live ledger, see below). The ledger stops all spend until
  fixed by hand if it is a symlink, empty, has any header but the exact one, has a row with the wrong number of cells,
  or has a cost that is missing, empty, non-finite or negative. `fetch` checks this and the `--request-id` shape
  before any network call. A live ledger that is **missing, header-only or merely behind the tracked export** (any
  export `row_id` absent from the live ledger) also refuses (exit 2, zero HTTP calls, nothing overwritten), as does an
  unreadable export. The live ledger is always a superset of every export on one machine, so a missing export row means
  a lost, stale or other-machine ledger. If the live rows are all in the export, restore with the
  `install -D -m 600 EXPORT LIVE` line the message prints (it also creates the state directory, so a second machine
  that shares the key does the same and inherits the spend); if the live ledger has rows the export lacks, the message
  asks for a hand merge instead (append the export's missing rows; with several worktrees use the export with the most
  rows, `git worktree list`). The very first ledger needs no step: it is created when the live file and the export are
  both absent or empty. A deliberate fresh start means emptying the export down to its header line first (visible in
  git). `vocal-check` checks the ledger first (like `gen`: a bad ledger means no ffprobe, pricing call or ffmpeg), its
  `--dry-run` exits 4/5/0 like `gen --dry-run`, and it validates what it would upload (size, WAV/MP3) before booking
  its $0.05; a refusal books nothing.
- **Reserve first.** The estimate is written to the live ledger under a file lock before
  the request is sent, updated with the request id the moment fal accepts it, and finished after the download. A kill,
  Ctrl-C or crash at any point still leaves the spend counted. Only an HTTP 4xx answer to the submit counts as "not billed".
- **One budget, in code.** `HARD_CAP` $15 and `STOP_AT` $12 cover every row of the ledger (`--campaign` is a label).
  `--cap` / `--stop-at` can only lower them; past $12 the lead raises the line by writing a number (at most 15) into
  `~/.local/state/megajam/music-stop-approval.txt`.
- **Prices.** The table (fal `llms.txt` pages, 2026-11-12) is the floor. The live pricing API replaces it only if positive,
  in the model's own unit and not lower. ElevenLabs bills per started minute, so plan takes just under whole minutes.
- **Billing read-back is not available:** our key has no billing scope (usage API answers 403). The ledger at list price is the control.
- `fetch --request-id ID` re-downloads a queued request whose audio was lost (poll timeout); it submits nothing.
- Outputs: `<stem>.wav|.mp3` plus `<audio>.provenance.json`; one `asset-pipeline-log.csv` row (stage `music:fal`). Keep
  outputs under `work/audio/` (git-ignored) or outside the repo. Only music is ledgered; fal image / 3D / TTS spend is not.
- AI-generated music is not a sourced asset (Rule 15(c)): disclose it, no sourced-asset row.

### Owner steps (agents never ask for, print, store or commit a key)

Create each key yourself on the vendor's site, then open `~/.config/megajam.env` in an editor (mode 600) and add the
lines shown. Add a `*_TERMS_REVIEWED=<date>` line only after reading that vendor's terms. Check with
`python3 scripts/gen_asset.py --providers-check`: the line should say `ready`.

1. **fal.** Sign in at https://fal.ai, open the dashboard's **Keys** page, create an API key. Add `FAL_KEY=PASTE_KEY_HERE`,
   and `FAL_TERMS_REVIEWED=<date>` after reading https://fal.ai/terms. For `--3d-provider fal` also set
   `HYPER3D_TERMS_REVIEWED` (step 2).
2. **Hyper3D Rodin.** API access needs a Business or Enterprise plan (you have Business). Open
   https://hyper3d.ai/workspace/api-dashboard and create a key. Add `RODIN_API_KEY=PASTE_KEY_HERE`, and
   `HYPER3D_TERMS_REVIEWED=<date>` after reading https://hyper3d.ai/legal/terms.
3. **Tripo.** The API is a separate product from the tripo3d.ai web app. On the Tripo API platform
   (https://platform.tripo3d.ai, "API Keys"; the key is shown only once) create a key, and buy API credits there if the
   balance is zero ($0.01 per credit, $1 minimum, Stripe). Add `TRIPO_API_KEY=PASTE_KEY_HERE` (`TRIPO_TERMS_REVIEWED`
   is already in the file).

### Do the jam perk credits pay for API calls?

| Perk | Covers our API calls? | Why |
|---|---|---|
| fal $30 account credit | **Yes** | fal is API-first: every model call is billed per call against the account balance. $30 is about 10,000 FLUX schnell concepts or 75 Rodin-on-fal models. |
| Hyper3D Business + 213 credits | **Unknown (likely yes)** | The API is "available on Business and Enterprise plans" and costs credits (0.5 per Gen-2.5 model), but no Hyper3D page says whether API calls draw from the same 213 subscription credits. Once the key exists, the API dashboard or the free "Check balance" endpoint shows it. Subscription credits expire at the end of the billing period. |
| Tripo 3,200 web credits + Pro trial (Nov 11-17) | **No** | Tripo's help centre says "Web App credits are not API credits" (search excerpt of https://www.tripo3d.ai/help/credit; the page returned 403 to our fetch). The API platform sells its own credits; the Pro trial is a web plan. The 3,200 credits can only be used in the web app by hand. |

### Licence and terms (Rules 15(b), 15(c))

- **Rule 15(c):** all three make AI-generated content, not sourced assets (same as Meshy, GPT, Grok). The sidecar
  records the provider; list the tools in the dev log.
- **fal** (https://fal.ai/terms, read 2026-11-10): fal makes no claim to outputs; you keep your inputs; API use inside
  your own product is allowed. Outputs may not be used to build competing products or train AI; fal may use anonymised
  usage data. The model licence also applies: FLUX.1 [schnell] is Apache-2.0 (commercial OK); Rodin-on-fal follows
  Hyper3D's terms, which is why it needs both dates.
- **Hyper3D** (https://hyper3d.ai/legal/terms, read 2026-11-10): Output is excluded from Hyper3D's IP; Rodin commercial
  rights vary "depending on your subscription plan", and the plan text is not on the terms page. Business API inputs and
  outputs are kept 7 days (https://hyper3d.ai/features/api); only Enterprise promises no training on API data.
  **Safe to ship, with conditions (hub 142 verdict 2026-11-12, not legal advice; source
  `~/Projects/superagent-sandbox/.handoff/hub142/rodin-license.md`):** Rodin outputs generated on our account while it
  is on the Business plan (MEGAJAM2026 code redeemed 2026-11-11 01:27 UTC) may go in the free jam build. Hyper3D's
  pricing lists the paid plans as "Unlimited export and any use"; the terms say Hyper3D will not limit use of Output,
  subject to the agreements, law and third-party terms, give no ownership or copyright promise, and say commercial
  export depends on the plan. Conditions: (1) keep assets made before the redemption (the 5 free credits, e.g. the
  2026-11-11 crate test) out of the build unless confirmed; (2) rights follow the plan at export, so download every
  Rodin asset before the perk ends on 2026-11-20 and keep the files (Hyper3D keeps API outputs only 7 days, so the
  local GLB is the copy that counts); (3) owner check still open: confirm in the Hyper3D
  account that Business shows commercial / any-use export and screenshot it for the ledger. Rodin-on-fal (3D, billed
  to the fal balance) follows Hyper3D's terms; fal's own terms add no restriction we found (its API supplemental terms
  were not read). The water tower (provenance created_at 2026-11-12T12:05Z) and the crew kit
  (`work/generated/SM_Crew_*/*.glb.provenance.json` in the main checkout, created_at 2026-11-13T05:49Z to 05:58Z)
  are Business-era; local GLBs kept. No credit line is
  required; for "Tools you used" list "3D models generated with Hyper3D Rodin (Deemos)."
- **Tripo:** owner read the terms 2026-11-07. The licence audit (`stages/00_prep/references/license-audit-asset-chain-2026-11-07.md`) says
  free-tier outputs are public CC BY and commercial use needs a paid plan. API credits are paid, but the docs do not say
  API output counts as paid-plan output. Treat it as paid, and confirm with Tripo before an asset ships.
- Nothing found blocks Epic's non-exclusive publicity licence (Rule 15(b)); unverified from full legal text.

Sources (read 2026-11-10): https://fal.ai/docs/model-apis/model-endpoints/queue, https://fal.ai/models/fal-ai/flux/schnell,
https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5, https://hyper3d.ai/features/api,
https://docs.hyper3d.ai/en/get-started/quick-start, https://docs.hyper3d.ai/en/api-specification/rodin-gen2-5,
.../check-status, .../download-results, https://developers.tripo3d.ai/en/docs/quick-start,
.../generation-image-to-model/standard, .../files, .../billing, https://developers.tripo3d.ai/en/pricing.
Not confirmed from docs: whether Rodin download URLs need the key (we fetch without it; if that fails the attempt fails
and `auto` moves on), and whether fal's Rodin endpoint takes a data URI (fal says many models do; if not, the attempt fails).

## Voice lines: `gen_asset.py --tts` (fal TTS, added 2026-11-12)

Hub call 2026-11-12 (owner: "Use an AI voice" for the director lines). Same gate as fal image/3D: `FAL_KEY` +
`FAL_TERMS_REVIEWED`, key only to `queue.fal.run`, audio fetched without the key (`scripts/providers/fal_tts.py`).

```bash
python3 scripts/gen_asset.py --name VO_Cut --tts "CUT!" --tts-voice Algenib --tts-style "energetic, warm, gravelly film director" --out-dir work/generated/vo
```

| Engine | Model | Notes |
|---|---|---|
| `gemini` (auto first) | `fal-ai/gemini-tts`, `gemini-2.5-pro-tts` (`--tts-quality flash` for the fast one) | `--tts-style` is plain-words direction; 30 voices (Algenib "gravelly", Fenrir "excitable", ...); WAV 24 kHz mono |
| `minimax` (fallback) | `fal-ai/minimax/speech-02-hd` | `--tts-emotion happy/angry/surprised/...`; FLAC 44.1 kHz |

Output: `<out-dir>/<name>/<name>.<wav|flac>` plus `<file>.provenance.json` (text, model, voice, style, request id,
terms date, sha256) and a `tts:<engine>` log row. Text is capped at 400 characters per call. Both models are tagged
"Commercial use" on fal; the output is AI-generated content (Rule 15(c)): disclose it in the AI field, never list it
as a sourced asset. Cost: a few seconds of speech per line; check the fal dashboard for the exact charge.

## Helper coding agents during the jam

- **ChatGPT via the codex CLI.** Installed (`codex`, logged in with ChatGPT). Headless: `codex exec "<task>"`
  in a worktree. Same rules as any helper: one lead agent is the only Unreal MCP caller, so codex edits
  source and scripts only. Quota comes from the ChatGPT plan.
- **Grok via Grok Build.** xAI ships an official terminal agent (https://docs.x.ai/build/overview): install
  with `curl -fsSL https://x.ai/cli/install.sh | bash`, run `grok` (browser sign-in on first launch),
  headless `grok -p "..."`. Docs name `GROK_CODE_XAI_API_KEY` for non-browser use; one third-party page says
  `XAI_API_KEY`, so check the docs when setting up. Early access was reported as SuperGrok/Premium+ only,
  unverified. **Not installed here; the owner installs it** (it runs a remote script, so read it first).
  Treat it like codex: source files only, no MCP.
- Neither is a substitute for the lead agent; they are overflow for scripts, tests and docs.

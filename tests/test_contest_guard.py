import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "scripts", "hooks", "contest_guard.py")
INSIDE = "~/Projects/megajam"
INSIDE_WT = "~/Projects/megajam/.claude/worktrees/x"
K = "NEXUS_THREED_IMAGE_CHECKPOINT=krea-2-turbo"


def run(command, cwd=INSIDE, tool="Bash"):
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}, "cwd": cwd})
    return subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True)


class ContestGuard(unittest.TestCase):
    def denied(self, cmd, rule=None, cwd=INSIDE):
        r = run(cmd, cwd)
        self.assertEqual(r.returncode, 2, cmd)
        if rule == "cloud-source":  # the host rules: cloud AI (cloud-source) or store (store-asset)
            self.assertTrue("[cloud-source]" in r.stderr or "[store-asset]" in r.stderr, r.stderr)
        elif rule:
            self.assertIn(f"[{rule}]", r.stderr)

    def allowed(self, cmd, cwd=INSIDE):
        r = run(cmd, cwd)
        self.assertEqual(r.returncode, 0, (cmd, r.stderr))
        self.assertEqual(r.stderr, "")

    def test_nexus_image_needs_krea(self):
        self.denied('nexus-image "a crate" --out a.png', "nexus-image-model")
        self.allowed('nexus-image "a crate" --out a.png --model krea-2-turbo')

    def test_banned_models(self):
        self.denied("nexus-image x --model qwen-image-2.1", "banned-model")
        self.denied("nexus-upscale in.png --model ultrasharp", "banned-model")
        self.denied("nexus-image x --model krea-2-turbo hunyuan3d-v2", "banned-model")

    def test_no_3d(self):
        self.denied("nexus-3d --image a.png --out a.glb", "no-3d")
        self.denied(f"{K} nexus-3d --image a.png --out a.glb", "no-3d")
        self.denied("nexus-3d --image a.png --out a.glb --model hunyuan", "no-3d")
        self.denied("nexus-3d --image a.png --out a.glb --model triposplat-x", "no-3d")
        self.denied("nexus-3d --image a.png --model triposplat --model hunyuan", "no-3d")
        self.denied("python3 nexus_3d.py --image a.png", "no-3d")
        self.denied("curl -X POST http://127.0.0.1:8765/generate/from-image", "no-3d")
        self.denied("modly generate x", "no-3d")

    def test_3d_allowed_only_as_triposplat(self):
        self.allowed("nexus-3d --image a.png --out a.glb --game-ready --model triposplat --json")
        self.allowed(f"{K} nexus-3d --image a.png --out a.glb --model=triposplat")
        self.allowed("python3 ~/Projects/nexus/scripts/nexus_3d.py --image a.png --model triposplat")
        self.denied("nexus-3d --image a.png --model triposplat --model hunyuan3d-mini", "no-3d")
        self.denied("nexus-3d --image a.png --model hunyuan3d-mini --model triposplat", "banned-model")
        self.denied("modly generate --model triposplat", "no-3d")
        self.denied("curl -X POST http://127.0.0.1:8765/generate/from-image -F model_id=triposplat/generate", "no-3d")

    def test_cloud_sources(self):
        for cmd in ("curl -O https://www.mixamo.com/x.fbx", "wget https://fab.com/x", "curl https://api.openai.com/v1/images",
                    "curl https://api.x.ai/v1/images/generations", "wget https://api.x.ai/v1/models",
                    "curl https://api.replicate.com/v1/predictions", "git clone https://sketchfab.com/foo",
                    "curl https://api.elevenlabs.io/v1/sound-generation", "curl https://api.meshy.ai/x",
                    "curl https://queue.fal.run/fal-ai/flux/schnell", "curl https://api.hyper3d.com/api/v2/rodin",
                    "wget https://openapi.tripo3d.ai/v3/files", "curl -O https://v3.fal.media/files/x.png"):
            self.denied(cmd, "cloud-source")

    def test_cloud_message_matches_provider_rule(self):
        r = run("curl https://api.x.ai/v1/images/generations")
        self.assertIn("gen_asset.py --provider", r.stderr)
        self.assertNotIn("local generation only", r.stderr)

    def test_git_mentioning_host_allowed(self):
        self.allowed('git commit -m "block direct api.x.ai fetches"')
        self.allowed("git grep -n api.x.ai scripts")
        self.denied("git clone https://sketchfab.com/foo", "cloud-source")
        for cmd in ("git -C /tmp clone https://sketchfab.com/foo",
                    "git -c http.sslVerify=false clone https://sketchfab.com/foo",
                    "git --git-dir=/tmp/x fetch https://api.x.ai/foo",
                    "git --no-pager -C /tmp pull https://sketchfab.com/foo"):
            self.denied(cmd, "cloud-source")

    def test_git_and_wrapper_bypasses_denied(self):
        for cmd in ("git fetch-pack https://sketchfab.com/r.git HEAD",
                    "git config remote.g.url https://api.x.ai/r.git && git fetch g",
                    "command git clone https://api.x.ai/r.git", "nohup curl -O https://api.x.ai/v1/x",
                    "exec git clone https://sketchfab.com/r.git",
                    "git -c alias.get=clone get https://api.x.ai/r.git",
                    "git -c 'alias.x=!curl https://api.x.ai/v1/images' x",
                    "git -c alias.x=clone x",
                    "git --attr-source HEAD clone https://api.x.ai/r.git",
                    "git -c a=b --attr-source HEAD -C d clone https://sketchfab.com/r.git"):
            self.denied(cmd, "cloud-source")
        self.allowed("git log --oneline -3")
        self.denied("git -C /tmp commit -m 'note api.x.ai'", "cloud-source")  # r6: no global git options

    def test_gen_asset_providers_allowed(self):
        self.allowed("python3 scripts/gen_asset.py --providers-check")
        self.allowed("python3 scripts/gen_asset.py --name crate --prompt x --provider grok")

    def test_store_assets_not_auto_downloaded(self):
        for cmd in ("curl -O https://www.mixamo.com/x.fbx", "wget https://fab.com/x", "git clone https://sketchfab.com/foo"):
            self.denied(cmd, "store-asset")
            self.assertIn("list it in the sourced-assets doc", run(cmd).stderr)
        self.denied("curl https://api.x.ai/v1/models", "cloud-source")
        self.assertIn("anything the Official Rules allow", run("curl https://api.x.ai/v1/models").stderr)
        self.assertNotIn("local generation only", run("curl https://api.x.ai/v1/models").stderr)

    def test_bans_stay(self):
        self.denied("nexus-3d --image a.png --out a.glb", "no-3d")
        self.denied("nexus-image x --model qwen-image-2.1", "banned-model")
        self.denied("nexus-upscale a.png --model 4x-UltraSharp", "banned-model")
        self.denied("python3 scripts/gen_asset.py --name c --prompt x --model hunyuan3d-2.1", "banned-model")

    def test_meshy_only_through_adapter(self):
        # allowed: the gen_asset adapter path (the API call happens inside python, not on the command line)
        self.allowed("python3 scripts/gen_asset.py --name crate --image a.png --3d-provider meshy")
        self.allowed("python3 scripts/gen_asset.py --name crate --prompt x --3d-provider auto")
        # denied: direct fetches of the API, assets or store pages
        for cmd in ("curl -X POST https://api.meshy.ai/openapi/v1/image-to-3d",
                    "wget https://assets.meshy.ai/x/model.glb", "curl https://www.meshy.ai/discover",
                    "git clone https://meshy.ai/x.git"):
            self.denied(cmd, "cloud-source")
        # other cloud hosts stay blocked and the message names the Meshy path
        self.denied("curl https://api.stability.ai/v2", "cloud-source")
        self.assertIn("--3d-provider", run("curl https://api.meshy.ai/x").stderr)

    def test_interpreter_fetches_denied(self):
        for cmd in ("python3 -c \"import urllib.request; urllib.request.urlopen('https://api.meshy.ai/x')\"",
                    "node -e \"fetch('https://api.meshy.ai')\"",
                    "python3 - <<EOF\nimport urllib.request\nurllib.request.urlopen('https://api.meshy.ai/x')\nEOF",
                    "ruby -e \"require 'net/http'; Net::HTTP.get(URI('https://api.openai.com/v1'))\""):
            self.denied(cmd, "cloud-source")
        self.allowed("python3 scripts/gen_asset.py --name a --image a.png --3d-provider meshy")

    def test_interpreter_guard_round2(self):
        fetch = "python3 -c \"import urllib.request as u; u.urlopen('https://api.meshy.ai/x')\""
        self.denied(fetch + " gen_asset.py", "cloud-source")  # gen_asset.py as a mere argument is no exemption
        self.denied("A=1 B=2 C=3 D=4 " + fetch, "cloud-source")
        self.denied("env -i timeout 5 nice " + fetch, "cloud-source")
        self.denied("bash -c \"python3 -c 'import urllib.request as u; u.urlopen(1)' https://api.meshy.ai\"", "cloud-source")
        self.allowed("python3 scripts/gen_asset.py --name a --image a.png --3d-provider meshy")
        # round 5: any env prefix denies; every piece must be a reader or the sanctioned run, host named or not
        self.denied("A=1 B=2 C=3 D=4 python3 scripts/gen_asset.py --3d-provider meshy api.meshy.ai", "cloud-source")
        self.denied('git commit -m "docs: note api.meshy.ai rate limits" && python3 -m unittest discover tests', "cloud-source")
        self.denied("grep -n meshy.ai _config/reference/ai-providers.md; python3 -m unittest tests.test_meshy", "cloud-source")

    def test_interpreter_guard_round3(self):
        code = "import urllib.request as u; u.urlopen('https://api.meshy.ai/x')"
        self.denied(f'echo "{code}" | python3', "cloud-source")
        self.denied(f'echo "{code}" | python3 -', "cloud-source")
        self.denied("echo \"fetch('https://api.meshy.ai')\" | node", "cloud-source")
        self.denied('echo "curl https://api.meshy.ai" | sh', "cloud-source")
        self.denied(f'python3 -c"{code}" gen_asset.py', "cloud-source")
        self.denied("perl -e'system(\"x https://api.meshy.ai\")' gen_asset.py", "cloud-source")
        self.denied("python3 -I -c \"u.urlopen('https://api.meshy.ai')\" gen_asset.py", "cloud-source")
        self.allowed('echo "hello" | python3 -c "print(1)"')
        self.allowed('git commit -m "api.meshy.ai" && python3 scripts/gen_asset.py --3d-provider meshy')

    def test_cloud_allowlist_round4(self):
        c = "import urllib.request as u; u.urlopen('https://api.meshy.ai/openapi/v2/text-to-3d')"
        u = "https://api.meshy.ai/openapi/v2/text-to-3d"
        for cmd in (f'echo "{c}" |& python3', f'echo "{c}" |\npython3', f'echo "{c}" | (python3)',
                    f'echo "{c}" | {{ python3; }}', f'echo "{c}" | xargs -0 python3 -c',
                    f'bash -c "curl {u}"', f'sh -c "wget -qO- {u}"', f'bash <<< "curl {u}"',
                    f'bash <(echo "curl {u}")', f'source <(echo "curl {u}")', f'eval "curl {u}"',
                    f'(python3 -c "{c}")', f"(curl {u})", f"{{ curl {u}; }}", f"if true; then curl {u}; fi",
                    f"for i in 1; do curl {u}; done", f"! curl {u}", f"echo $(curl -s {u})", f"X=`curl -s {u}`",
                    f'timeout 5s python3 -c "{c}"', f"timeout 30s curl {u}", f'env -u HOME python3 -c "{c}"',
                    f'stdbuf -oL python3 -c "{c}"', f'echo | xargs python3 -c "{c}"', f"echo {u} | xargs curl",
                    f'find . -maxdepth 0 -exec python3 -c "{c}" \\;', f'coproc python3 -c "{c}"'):
            self.denied(cmd, "cloud-source")
        for cmd in ('grep -c "api.meshy.ai" _config/reference/ai-providers.md | python3 -c "import sys; print(sys.stdin.read())"',
                    'ls | python3 -m json.tool; git commit -m "docs: api.meshy.ai limits"',
                    'python3 -m unittest discover -s tests 2>&1 | python3 -c "import sys; print(1)" && git commit -m "Meshy (api.meshy.ai) adapter"',
                    'echo ok | python3 -c "print(1)" && git commit -m "api.meshy.ai"'):
            self.denied(cmd, "cloud-source")  # round 5: non-reader pieces are denied even without the host text
        self.allowed('rg api.meshy.ai docs | head -5')
        self.denied("python3 /tmp/gen_asset.py --3d-provider meshy api.meshy.ai", "cloud-source")  # not this repo's script

    def test_round6(self):
        for cmd in ("echo $'\\'' ; sh -c 'echo api.meshy.ai' ; echo ''",
                    "echo $'\\'' ; python3 /tmp/up.py https://api.meshy.ai/v1 ; echo ''",
                    "echo 'unterminated api.meshy.ai",
                    "git --namespace log -c core.pager=cat log --oneline -- meshy.ai",
                    "git -C status -c core.fsmonitor=x status meshy.ai",
                    "git grep -nOecho meshy.ai", "git grep --open-files=echo meshy.ai",
                    '"cat;" meshy.ai', "{cat} meshy.ai", '"(head)" meshy.ai',
                    "git tag meshy.ai-ref", "git notes add -m api.meshy.ai",
                    "rg --hostname-bin=sh api.meshy.ai ."):
            self.denied(cmd, "cloud-source")
        for cmd in ('git commit -m "fix #12; see api.meshy.ai"', "git grep -n api.meshy.ai docs",
                    "{ cat _config/reference/ai-providers.md; } | grep api.meshy.ai"):
            self.allowed(cmd)

    def test_round7(self):
        for cmd in ("git grep --op='sh -c id' api.meshy.ai", "git grep --ope=sh api.meshy.ai",
                    "git grep --open-files-in-pager=sh api.meshy.ai", "git log --ext api.meshy.ai",
                    "git diff --outp=/tmp/x api.meshy.ai",
                    "cat =(curl https://api.meshy.ai/v1)", "ls *(e:'curl https://api.meshy.ai':)"):
            self.denied(cmd, "cloud-source")
        for cmd in ("git log --oneline -5 -- api.meshy.ai", "git diff --stat api.meshy.ai",
                    "git grep -n --count api.meshy.ai docs", "{ cat docs/x.md; } | grep api.meshy.ai"):
            self.allowed(cmd)

    def test_round8(self):
        for cmd in ("git grep --openx api.meshy.ai", "cat ((x)) api.meshy.ai", "cat x;( cat y ) api.meshy.ai",
                    "cat x|( cat y ) | grep api.meshy.ai"):
            self.denied(cmd, "cloud-source")
        self.allowed("{ cat docs/x.md; } | grep api.meshy.ai")

    def test_model_downloads(self):
        self.denied("huggingface-cli download VAST-AI/TripoSplat", "model-download")
        self.denied("hf download Comfy-Org/Krea-2", "model-download")
        self.denied("python3 -c 'from huggingface_hub import snapshot_download'", "model-download")

    def test_uc2(self):
        self.denied("cp -r ~/Projects/Unreal/extracted/UC2004/Textures work/", "uc2-import")

    def test_gen_asset_path_allowed(self):
        self.allowed('python3 scripts/gen_asset.py --name crate --prompt "a crate"')
        self.allowed("python3 scripts/gen_asset.py --name crate --image a.png")

    def test_banned_model_via_gen_asset(self):
        self.denied("python3 scripts/gen_asset.py --name c --prompt x --model qwen-image-2.1", "banned-model")

    def test_normal_commands(self):
        for cmd in ("git status", 'git commit -m "drop hunyuan, nexus-image rule"', "gh pr create --repo jf1shh/megajam",
                    "rg hunyuan docs", "ls work/", "python3 -m unittest discover tests", "echo qwen-image > notes.txt",
                    "git clone https://github.com/jf1shh/megajam"):
            self.allowed(cmd)

    def test_worktree_is_guarded(self):
        self.denied("nexus-image x", "nexus-image-model", cwd=INSIDE_WT)

    def test_outside_megajam_always_allowed(self):
        for cwd in ("~", "~/Projects/megajam-other", "~/Projects/nexus", "/tmp"):
            self.allowed("nexus-image x --model qwen-image-2.1", cwd)
            self.allowed("huggingface-cli download foo/bar", cwd)

    def test_non_bash_tool_allowed(self):
        self.assertEqual(run("nexus-image x", tool="Edit").returncode, 0)

    def test_fail_open(self):
        for stdin in ("", "not json", "[]", "null"):
            r = subprocess.run([sys.executable, HOOK], input=stdin, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, stdin)
        r = subprocess.run([sys.executable, HOOK], stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()

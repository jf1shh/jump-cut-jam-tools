"""legion_ship tests: a fake ssh/scp stands in for the Legion. No network, no GPU, no editor."""
import contextlib
import io
import json
import os
import stat
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import legion_ship as L  # noqa: E402
ORIG_RESOLVE = L.resolve_host  # Rig.setUp replaces it with a stub

FAKE_SSH = '''#!/usr/bin/env python3
import json, os, sys
cfg_path = os.environ["FAKE_CFG"]
cfg = json.load(open(cfg_path))
cmd = sys.argv[2]
open(cfg["calls"], "a").write(cmd + "\\n")
if "package-and-push.ps1" in cmd:
    print(cfg.get("package_out", "BUILD SUCCESSFUL"))
    sys.exit(cfg.get("package_rc", 0))
if cmd == "echo OK":
    if cfg.get("ssh_down"):
        print("ssh: connect to host <device-host> port 22: Connection timed out")
        sys.exit(255)
    print("OK")
    sys.exit(0)
if cmd.startswith("powershell -NoProfile -NonInteractive -EncodedCommand"):  # stage manifest
    import hashlib
    if cfg.get("manifest_rc"):
        sys.exit(cfg["manifest_rc"])
    files = sorted(cfg.get("stage_files", {"Game.exe": "exe"}).items())
    hidden = cfg.get("manifest_hidden", [])  # hash failed: error on stderr, nothing on stdout
    for name, text in files:
        if name in hidden:
            sys.stderr.write("Get-FileHash : the process cannot access the file\\n")
            continue
        print("%s|%d|%s" % (name, len(text), hashlib.sha256(text.encode()).hexdigest()))
    if cfg.get("manifest_rc_after"):
        sys.exit(cfg["manifest_rc_after"])
    if not cfg.get("manifest_no_end"):
        print("#END|%d" % (len(files) + cfg.get("manifest_count_off", 0)))
    sys.exit(0)
if cmd.startswith("tar -cf") and " -T " not in cmd:
    try:
        os.remove(cfg["uploaded"] + ".list")
    except OSError:
        pass
if cmd.startswith("robocopy") and cfg.get("robocopy_rc"):
    for needle, rc in cfg["robocopy_rc"].items():
        if needle in cmd:
            sys.exit(rc)
if cmd.startswith("type ") and "type_out" in cfg:  # a file read back from the Legion
    print(cfg["type_out"])
    sys.exit(0)
if cmd.startswith("tasklist"):
    print(cfg.get("tasks", ""))
    sys.exit(0)
if cmd.startswith("taskkill"):
    cfg["tasks"] = ""
    json.dump(cfg, open(cfg_path, "w"))
    sys.exit(0)
if cmd.startswith("dir /-c"):
    print(" 3 Dir(s)  %d bytes free" % cfg.get("free", 200 * 2**30))
    sys.exit(0)
if cmd.startswith("nslookup"):
    print(cfg.get("nslookup", "Server: x\\nAddress: 1.1.1.1\\n\\nName: api.itch.io\\nAddress: 1.2.3.4"))
    sys.exit(0)
if " del /q " in cmd or cmd.startswith("echo ok>"):  # the packaged-ok marker: keep the fake Legion's state
    path = cmd.split('"')[1]
    if cmd.startswith("echo ok>"):
        cfg["exist"].append(path)
    elif path in cfg["exist"]:
        cfg["exist"].remove(path)
    json.dump(cfg, open(cfg_path, "w"))
    sys.exit(0)
if cmd.startswith("if exist") and "findstr" in cmd:  # --publish-root target probe
    print(cfg.get("publish_state", "MISSING"))
    sys.exit(cfg.get("publish_probe_rc", 0))
if cmd.startswith("if exist"):
    path = cmd.split('"')[1]
    print("EXISTS" if path in cfg["exist"] else "MISSING")
    sys.exit(0)
if " push " in cmd:
    print("butler push ok")
    sys.exit(cfg.get("push_rc", 0))
if " status " in cmd:
    n = cfg.setdefault("status_n", 0)
    seq = cfg["status_seq"]
    print(seq[min(n, len(seq) - 1)])
    cfg["status_n"] = n + 1
    json.dump(cfg, open(cfg_path, "w"))
    sys.exit(0)
sys.exit(0)
'''

FAKE_SCP = '''#!/usr/bin/env python3
import json, os, shutil, sys
cfg = json.load(open(os.environ["FAKE_CFG"]))
if sys.argv[1].startswith("<device-host>:"):  # fetch of the staged build
    import tarfile
    open(cfg["calls"], "a").write("SCPGET " + sys.argv[1] + "\\n")
    src = os.path.join(os.path.dirname(cfg["uploaded"]), "stage_src.txt")
    lst = cfg["uploaded"] + ".list"
    only = open(lst).read().split() if os.path.exists(lst) else None
    with tarfile.open(sys.argv[2], "w") as tf:
        for name, text in cfg.get("stage_files", {"Game.exe": "exe"}).items():
            if only is None or name in only:
                open(src, "w").write(text)
                tf.add(src, arcname=name)
    sys.exit(0)
if os.path.basename(sys.argv[1]) == "stage-files.txt":
    shutil.copy(sys.argv[1], cfg["uploaded"] + ".list")
    open(cfg["calls"], "a").write("SCP " + sys.argv[2] + "\\n")
    sys.exit(0)
shutil.copy(sys.argv[1], cfg["uploaded"])
open(cfg["calls"], "a").write("SCP " + sys.argv[2] + "\\n")
'''

FAKE_BUTLER = '''#!/usr/bin/env python3
import json, os, sys
p = os.environ["FAKE_CFG"]
cfg = json.load(open(p))
line = " ".join(sys.argv[1:])
if sys.argv[1] == "push":
    line += " STAGE_OK" if os.path.isfile(os.path.join(sys.argv[2], "Game.exe")) else " STAGE_MISSING"
open(cfg["bcalls"], "a").write(line + "\\n")
if sys.argv[1] == "push":
    print("pushed")
    sys.exit(cfg.get("bpush_rc", 0))
n = cfg.get("bstatus_n", 0)
seq = cfg["status_seq"]
print(seq[min(n, len(seq) - 1)])
cfg["bstatus_n"] = n + 1
json.dump(cfg, open(p, "w"))
'''


def _table(build):
    return ("+---------+----------+------------+---------+\n"
            "| CHANNEL |  UPLOAD  |   BUILD    | VERSION |\n"
            "+---------+----------+------------+---------+\n"
            f"| win64   | #1234567 | {build:<10} | 2       |\n"
            "+---------+----------+------------+---------+\n")


TABLE_DONE = _table("√ #2329072")       # real butler shape: tick + build id = processed
TABLE_PENDING = _table("")               # upload there, build not produced yet
TABLE_UNTICKED = _table("#2329072")      # build id but no tick = still processing

STAGE = "C:\\Dev\\Game\\Packaged\\Windows"
UNREAL = STAGE + "\\Engine\\Binaries\\Win64\\UnrealGame.exe"
MARKER = "C:\\Dev\\_ship\\Game.packaged-ok"
ENGINE_BAT = "C:\\Dev\\UE_5.8\\Engine\\Build\\BatchFiles\\RunUAT.bat"
OLD_ENGINE_BAT = "C:\\UE_5.8\\Engine\\Build\\BatchFiles\\RunUAT.bat"


def make_exec(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Rig(unittest.TestCase):
    default_extra = []

    def exist(self, *more):
        return [ENGINE_BAT, L.DEFAULT_BUTLER, *more]

    def setUp(self):
        p = mock.patch.object(L, "resolve_host", lambda name: None)
        p.start()
        self.addCleanup(p.stop)
        self._td = tempfile.TemporaryDirectory()
        self.td = Path(self._td.name)
        self.addCleanup(self._td.cleanup)
        self.proj = self.td / "Game"
        (self.proj / "Content").mkdir(parents=True)
        (self.proj / "Content" / "a.uasset").write_text("x")
        (self.proj / "Saved").mkdir()
        (self.proj / "Saved" / "big.log").write_text("junk")
        (self.proj / "Game.uproject").write_text("{}")
        self.ps1 = self.td / "pp.ps1"
        self.ps1.write_text("$hasSource = 1\n")
        self.notice = self.td / "NOTICE.txt"
        self.notice.write_text("notice")
        make_exec(self.td / "ssh", FAKE_SSH)
        make_exec(self.td / "scp", FAKE_SCP)
        make_exec(self.td / "butler", FAKE_BUTLER)
        self.cfg_path = self.td / "cfg.json"
        self.calls = self.td / "calls.txt"
        self.bcalls = self.td / "bcalls.txt"
        self.uploaded = self.td / "uploaded.tar"
        self.cfg = {"calls": str(self.calls), "bcalls": str(self.bcalls), "uploaded": str(self.uploaded),
                    "exist": self.exist(STAGE + "\\Game.exe", UNREAL, MARKER),
                    "status_seq": [TABLE_PENDING, TABLE_DONE]}
        (self.td / "logs").mkdir()  # a previous good ship: the PC-side record that pairs with the marker
        (self.td / "logs" / "Game.packaged-state").write_text("ok\n")
        os.environ["FAKE_CFG"] = str(self.cfg_path)
        self.addCleanup(os.environ.pop, "FAKE_CFG", None)

    def run_ship(self, *extra, dry=False):
        self.cfg_path.write_text(json.dumps(self.cfg))
        argv = [str(self.proj), "--ssh", str(self.td / "ssh"), "--scp", str(self.td / "scp"),
                "--ps1", str(self.ps1), "--ps1-ref", "", "--notice", str(self.notice),
                "--log-dir", str(self.td / "logs"), "--state-dir", str(self.td / "logs"), "--status-interval", "0",
                "--pc-butler", str(self.td / "butler"), "--min-free-gb", "2",
                *self.default_extra, *extra]
        if dry:
            argv.append("--dry-run")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = L.main(argv)
        self.cfg = json.loads(self.cfg_path.read_text())  # carry the fake Legion's state to the next run
        return rc, out.getvalue()

    def calls_text(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def bcalls_text(self):
        return self.bcalls.read_text() if self.bcalls.exists() else ""


class ShipTests(Rig):
    """The old path: butler runs on the Legion."""
    default_extra = ["--push-from", "device-host"]

    def test_happy_path_pushes_after_check_and_waits_for_status(self):
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        calls = self.calls_text()
        self.assertIn(" push ", calls)
        self.assertLess(calls.index("if exist"), calls.index(" push "))
        self.assertEqual(calls.count(" status "), 2)  # polled until processing was over
        self.assertNotIn("-ItchTarget", calls)  # the ps1 must not push by itself
        self.assertRegex(out.splitlines()[-1], r"^SHIPPED: .*sync .*m package .*m check .*m push .*m status .*m \| total")

    def test_exe_check_failure_blocks_push(self):
        self.cfg["exist"] = self.exist(STAGE + "\\Game.exe")  # stub there, target UnrealGame.exe gone
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertNotIn(" push ", self.calls_text())
        self.assertIn("NOT pushing", out)
        self.assertIn("UnrealGame.exe", out)

    def test_content_only_with_project_named_target_ships(self):
        # UE 5.9 source engine (mock jam 16): -build makes Game\\Binaries\\Win64\\Game.exe and no UnrealGame.exe.
        self.cfg["exist"] = self.exist(STAGE + "\\Game.exe", STAGE + "\\Game\\Binaries\\Win64\\Game.exe")
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertIn(" push ", self.calls_text())

    def test_content_only_with_decoy_rename_blocks_push(self):
        self.cfg["exist"] = self.exist(STAGE + "\\Game.exe", UNREAL, UNREAL + ".decoy-disabled")
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertNotIn(" push ", self.calls_text())
        self.assertIn("decoy-disabled", out)

    def test_missing_root_stub_blocks_push(self):
        self.cfg["exist"] = self.exist(UNREAL)
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertNotIn(" push ", self.calls_text())

    def test_cpp_project_needs_game_binary_and_disabled_decoy(self):
        (self.proj / "Source").mkdir()
        self.cfg["exist"] = self.exist(STAGE + "\\Game.exe", STAGE + "\\Game\\Binaries\\Win64\\Game.exe")
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.cfg["exist"].append(UNREAL)  # decoy left enabled
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)

    def test_package_failure_captures_log_and_stops(self):
        self.cfg.update(package_rc=3, package_out="LogCook: Error: boom")
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        logs = list((self.td / "logs").glob("Game-*.log"))
        self.assertEqual(len(logs), 1)
        text = logs[0].read_text()
        self.assertIn("LogCook: Error: boom", text)
        self.assertIn("[exit 3]", text)
        self.assertIn("LogCook: Error: boom", out)  # streamed live too
        self.assertNotIn("Game.exe\" (echo", self.calls_text())  # no exe probe after a failed package
        self.assertNotIn(" push ", self.calls_text())

    def test_successful_package_also_logs(self):
        self.run_ship()
        text = next((self.td / "logs").glob("Game-*.log")).read_text()
        self.assertIn("BUILD SUCCESSFUL", text)

    def test_archive_skips_junk_and_carries_scripts(self):
        self.run_ship()
        with tarfile.open(self.uploaded) as tf:
            names = tf.getnames()
        self.assertIn("Game/Content/a.uasset", names)
        self.assertIn("_ship/scripts/package-and-push.ps1", names)
        self.assertIn("_ship/_config/reference/NOTICE.txt", names)
        self.assertFalse([n for n in names if "Saved" in n])

    def test_push_failure_reports(self):
        self.cfg["push_rc"] = 1
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("butler push failed", out)

    def test_status_timeout(self):
        self.cfg["status_seq"] = [TABLE_UNTICKED]
        rc, out = self.run_ship("--status-timeout", "0")
        self.assertEqual(rc, 1)
        self.assertIn("still processing", out)

    def test_dry_run_prints_every_remote_command_and_runs_nothing(self):
        rc, out = self.run_ship(dry=True)
        self.assertEqual(rc, 0, out)
        calls = self.calls_text()  # only the read-only preflight probes ran
        for forbidden in ("tar -xf", "robocopy", "mkdir", "package-and-push", " push ", "taskkill"):
            self.assertNotIn(forbidden, calls)
        self.assertIn("RunUAT.bat", calls)
        self.assertFalse(self.uploaded.exists())
        for needle in ("[mkdir]", "[scp]", "[unpack]", "[package]", "[check]", "[push]", "[status]",
                       "package-and-push.ps1", "butler.exe", "push"):
            self.assertIn(needle, out)
        self.assertIn("jf1shh/megajam-pretest:win64", out)

    def test_ps1_without_content_only_fix_is_refused(self):
        self.ps1.write_text("old script\n")
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("lacks the content-only fix", out)
        self.assertEqual(self.calls_text(), "")

    def test_sync_mirrors_and_keeps_cook_cache(self):
        self.run_ship()
        pre = []
        for c in self.calls_text().splitlines():
            if "package-and-push.ps1" in c:
                break
            pre.append(c)
        mirror = [c for c in pre if c.startswith("robocopy") and "/MIR" in c]
        self.assertEqual(len(mirror), 1)
        self.assertIn('"C:\\Dev\\Game\\DerivedDataCache"', mirror[0])
        self.assertIn("_incoming", mirror[0])

    def test_game_name_override_keeps_exe_check_on_uproject_name(self):
        rc, out = self.run_ship("--game-name", "WaterBalloon")
        self.assertEqual(rc, 0, out)
        self.assertIn("-GameName WaterBalloon", self.calls_text())

    def test_nested_build_saved_packaged_content_folders_are_shipped(self):
        for n in ("Build", "Saved", "Packaged"):
            d = self.proj / "Content" / "X" / n
            d.mkdir(parents=True)
            (d / f"{n}.uasset").write_text("x")
        (self.proj / "Plugins" / "P" / "Intermediate").mkdir(parents=True)
        (self.proj / "Plugins" / "P" / "Intermediate" / "junk").write_text("x")
        (self.proj / "Plugins" / "P" / "Content").mkdir()
        (self.proj / "Plugins" / "P" / "Content" / "ok.uasset").write_text("x")
        self.run_ship()
        with tarfile.open(self.uploaded) as tf:
            names = tf.getnames()
        for n in ("Build", "Saved", "Packaged"):
            self.assertIn(f"Game/Content/X/{n}/{n}.uasset", names)
        self.assertIn("Game/Plugins/P/Content/ok.uasset", names)
        self.assertFalse([n for n in names if "Plugins/P/Intermediate" in n])

    def test_butler_commands_are_wrapped_for_cmd(self):
        self.run_ship()
        for c in self.calls_text().splitlines():
            if " push " in c or " status " in c:
                self.assertTrue(c.startswith('""') and c.endswith('"'), c)
                self.assertGreater(c.count('"'), 2)

    def test_status_error_text_fails_instead_of_processed(self):
        self.cfg["status_seq"] = ["butler: error: not logged in"]
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("butler status failed", out)

    def test_status_unrecognised_output_is_not_success(self):
        self.cfg["status_seq"] = ["???"]
        rc, out = self.run_ship("--status-timeout", "0")
        self.assertEqual(rc, 1)
        self.assertIn("still processing", out)

    def test_real_status_table_states(self):
        self.assertEqual(L.status_state(TABLE_DONE), "done")
        self.assertEqual(L.status_state(TABLE_PENDING), "pending")
        self.assertEqual(L.status_state(TABLE_UNTICKED), "pending")

    def test_root_build_resources_shipped_binaries_not(self):
        (self.proj / "Build" / "Windows").mkdir(parents=True)
        (self.proj / "Build" / "Windows" / "Application.ico").write_text("i")
        (self.proj / "Binaries" / "Win64").mkdir(parents=True)
        (self.proj / "Binaries" / "Win64" / "x.dll").write_text("d")
        self.run_ship()
        with tarfile.open(self.uploaded) as tf:
            names = tf.getnames()
        self.assertIn("Game/Build/Windows/Application.ico", names)
        self.assertFalse([n for n in names if "Binaries" in n])

    def test_mirror_keeps_remote_binaries(self):
        self.run_ship()
        # Skip the compile check's own mirror (step 0b, _cc_incoming); this test is about the ship sync.
        mirror = [c for c in self.calls_text().splitlines() if "/MIR" in c and "_cc_incoming" not in c][0]
        self.assertIn('"C:\\Dev\\Game\\Binaries"', mirror)
        self.assertNotIn('"C:\\Dev\\Game\\Build"', mirror)

    def test_helpers(self):
        self.assertTrue(L.status_done("build 12 finished"))
        self.assertFalse(L.status_done("Processing"))
        self.assertFalse(L.status_done(""))
        self.assertFalse(L.status_done("some output"))
        self.assertEqual(L.status_state("Error: not logged in"), "error")
        self.assertEqual(L.cmdq('"a" b "c"'), '""a" b "c""')
        self.assertEqual(L.cmdq("tar x"), "tar x")
        self.assertEqual(L.win("C:\\Dev\\", "A", "b.exe"), "C:\\Dev\\A\\b.exe")


LEFTOVER = '"UnrealGame.exe","4242","Console","1","300,000 K"\n"explorer.exe","1","Console","1","1 K"'


class StampTests(Rig):
    """BUILD.txt names the commit that was packed (taken at sync), not whatever is checked in when packaging ends."""
    default_extra = ["--no-push"]
    SRC = "dv.commit.65 (+2 uncommitted paths in the tar) synced 2026-11-12 07:12:19"

    def stamp_at_sync(self, *extra):
        def fake(ctx, proj_dir):
            with open(self.calls, "a") as f:
                f.write("#source_stamp\n")
            return self.SRC
        with mock.patch.object(L, "source_stamp", side_effect=fake) as m:
            rc, out = self.run_ship(*extra)
        return rc, out, m

    def test_build_txt_uses_the_commit_from_sync_time(self):
        rc, out, m = self.stamp_at_sync()
        self.assertEqual(rc, 0, out)
        self.assertEqual(m.call_count, 1)
        calls = self.calls_text().splitlines()
        esc = L.cmd_echo(self.SRC)
        taken = calls.index("#source_stamp")
        saved = next(i for i, c in enumerate(calls) if c.startswith(f"echo {esc}>") and L.SOURCE_STAMP in c)
        build = next(i for i, c in enumerate(calls) if c.startswith(f"echo {esc} staged ") and "BUILD.txt" in c)
        package = next(i for i, c in enumerate(calls) if "package-and-push.ps1" in c)
        self.assertLess(taken, saved)
        self.assertLess(saved, package)  # on the Legion before the long package step
        self.assertLess(package, build)
        self.assertIn(f"BUILD STAMP: {self.SRC} staged ", out)

    def test_resume_reads_the_stamp_the_sync_left(self):
        self.cfg["type_out"] = "dv.commit.64 synced 2026-11-12 06:52:00"
        rc, out, m = self.stamp_at_sync("--from-step", "2")
        self.assertEqual(rc, 0, out)
        self.assertEqual(m.call_count, 0)  # no sync in a resumed run
        self.assertIn("BUILD STAMP: dv.commit.64 synced 2026-11-12 06:52:00 staged ", out)

    def test_resume_without_a_sync_stamp_says_unknown(self):
        rc, out, m = self.stamp_at_sync("--from-step", "2")
        self.assertEqual(rc, 0, out)
        self.assertIn("BUILD STAMP: unknown source (no sync stamp) staged ", out)

    def test_cmd_echo_escapes_parentheses(self):
        self.assertEqual(L.cmd_echo("a (b) c"), "a ^(b^) c")


class PublishTests(Rig):
    """--publish-root: one build root (its Intermediate survives) while each build gets its own folder."""
    PUB = "C:\\Dev\\megajam-game-b9"

    def test_default_team_is_second_unit(self):
        rc, out = self.run_ship("--no-push")
        self.assertEqual(rc, 0, out)
        self.assertIn("-TeamName SecondUnit -GameName Game", self.calls_text())

    def test_publish_mirrors_the_checked_stage(self):
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 0, out)
        calls = self.calls_text().splitlines()
        pub = [i for i, c in enumerate(calls) if c.startswith("robocopy") and self.PUB in c]
        self.assertEqual(len(pub), 1, calls)
        self.assertIn(f'robocopy "{STAGE}" "{self.PUB}\\Game\\Packaged\\Windows" /MIR', calls[pub[0]])
        exe = max(i for i, c in enumerate(calls) if c.startswith("if exist") and "Game.exe" in c)
        self.assertLess(exe, pub[0])  # only a stage that passed the exe check is published
        self.assertIn(f"PUBLISHED: {self.PUB}\\Game\\Packaged\\Windows", out)

    def test_publish_failure_fails_the_ship(self):
        self.cfg["robocopy_rc"] = {self.PUB: 8}
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 1)
        self.assertIn("publish copy", out)

    def test_publish_onto_the_stage_itself_is_refused(self):
        rc, out = self.run_ship("--no-push", "--publish-root", "C:\\Dev\\")
        self.assertEqual(rc, 1)
        self.assertIn("resolves to the stage itself", out)
        self.assertNotIn(f'robocopy "{STAGE}"', self.calls_text())

    def publish_calls(self):
        return [c for c in self.calls_text().splitlines() if c.startswith("robocopy") and self.PUB in c]

    def test_publish_into_a_nonempty_target_is_refused(self):
        self.cfg["publish_state"] = "NONEMPTY"
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 1)
        self.assertIn("already holds an earlier build", out)
        self.assertIn("--publish-overwrite", out)
        self.assertEqual(self.publish_calls(), [])
        probe = [c for c in self.calls_text().splitlines() if "findstr" in c]
        self.assertEqual(len(probe), 1, probe)
        self.assertIn(f'"{self.PUB}\\Game\\Packaged\\Windows"', probe[0])  # the probed path stays quoted

    def test_publish_overwrite_replaces_a_nonempty_target(self):
        self.cfg["publish_state"] = "NONEMPTY"
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB, "--publish-overwrite")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self.publish_calls()), 1)
        self.assertIn("PUBLISHED", out)

    def test_publish_into_an_empty_or_missing_target_needs_no_flag(self):
        for state in ("EMPTY", "MISSING"):
            self.cfg["publish_state"] = state
            rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
            self.assertEqual(rc, 0, (state, out))
        self.assertEqual(len(self.publish_calls()), 2)

    def test_publish_check_failure_refuses_rather_than_guesses(self):
        # ssh down or cmd error: a nonzero exit and no state token on stdout
        self.cfg["publish_probe_rc"] = 255
        self.cfg["publish_state"] = "ssh: connect to host <device-host> port 22: Connection timed out"
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 1)
        self.assertIn("could not check the publish target", out)
        self.assertEqual(self.publish_calls(), [])

    def test_publish_empty_target_with_exit_1_is_still_empty(self):
        # cmd: the EMPTY branch echoes after a failing findstr (errorlevel 1), so cmd /c can exit 1
        self.cfg["publish_probe_rc"] = 1
        self.cfg["publish_state"] = "EMPTY"
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self.publish_calls()), 1)

    def test_publish_nonempty_target_with_exit_1_is_still_refused(self):
        self.cfg["publish_probe_rc"] = 1
        self.cfg["publish_state"] = "NONEMPTY"
        rc, out = self.run_ship("--no-push", "--publish-root", self.PUB)
        self.assertEqual(rc, 1)
        self.assertIn("already holds an earlier build", out)
        self.assertEqual(self.publish_calls(), [])

    def test_publish_target_state_reads_the_token_whatever_the_exit_code(self):
        def state(rc, out):
            ctx = mock.Mock(dry=False)
            ctx.remote = lambda cmd, label, stdout_only=False: (rc, out)
            return L.publish_target_state(ctx, "C:\\pub")
        self.assertEqual(state(1, "EMPTY\r\n"), "EMPTY")
        self.assertEqual(state(0, "EMPTY\r\n"), "EMPTY")
        self.assertEqual(state(1, "NONEMPTY\r\n"), "NONEMPTY")
        self.assertEqual(state(0, "MISSING\r\n"), "MISSING")
        for rc, out in ((255, ""), (1, "'findstr' is not recognized"), (0, "garbage")):
            with self.assertRaises(L.ShipError):
                state(rc, out)

    def test_no_publish_root_copies_nothing(self):
        rc, out = self.run_ship("--no-push")
        self.assertEqual(rc, 0, out)
        self.assertNotIn(f'robocopy "{STAGE}"', self.calls_text())
        self.assertNotIn("PUBLISHED", out)


class PcPushTests(Rig):
    """Default path: the Legion packages, the PC's butler pushes."""

    def test_pc_push_fetches_stage_then_pushes_from_pc(self):
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        calls, b = self.calls_text(), self.bcalls_text()
        self.assertIn("SCPGET <device-host>:", calls)
        self.assertLess(calls.index("Game.exe\" (echo"), calls.index("SCPGET"))  # check before fetch
        self.assertNotIn(" push ", calls)  # the Legion never ran butler
        self.assertNotIn(" status ", calls)
        self.assertIn("push ", b)
        self.assertIn("STAGE_OK", b)  # the fetched copy was on disk when butler ran
        self.assertIn(L.DEFAULT_TARGET, b)
        self.assertEqual(b.count("status "), 2)

    def fetched(self):
        return self.td / "logs" / "stage-Game"

    def test_second_ship_of_unchanged_build_copies_nothing(self):
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls_text().count("SCPGET"), 1)
        self.assertTrue((self.td / "logs" / "stage-Game.manifest.json").is_file())
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls_text().count("SCPGET"), 1, "second run must not fetch")
        self.assertEqual(self.calls_text().count("tar -cf"), 1)
        self.assertIn("copied 0", out)
        self.assertTrue((self.fetched() / "Game.exe").is_file())
        self.assertEqual(self.bcalls_text().count("STAGE_OK"), 2)  # butler still saw the full build

    def test_changed_files_only_are_copied_and_removed_ones_deleted(self):
        self.cfg["stage_files"] = {"Game.exe": "exe", "a.pak": "one", "old.txt": "x"}
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.cfg["stage_files"] = {"Game.exe": "exe", "a.pak": "two!", "new.pak": "n"}
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertIn("copying 2 of 3", out)
        self.assertIn("-T ", self.calls_text())
        d = self.fetched()
        self.assertEqual((d / "a.pak").read_text(), "two!")
        self.assertTrue((d / "new.pak").is_file())
        self.assertFalse((d / "old.txt").exists())
        self.assertEqual((d / "Game.exe").read_text(), "exe")

    def test_full_flag_copies_everything_again(self):
        self.run_ship()
        rc, out = self.run_ship("--from-step", "4", "--full")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls_text().count("SCPGET"), 2)
        self.assertNotIn(" -T ", self.calls_text())

    def test_missing_or_unreadable_manifest_means_whole_copy(self):
        self.run_ship()
        m = self.td / "logs" / "stage-Game.manifest.json"
        for bad in (None, "{not json", '{"files": 3}'):
            n = self.calls_text().count("SCPGET")
            if bad is None:
                m.unlink(missing_ok=True)
            else:
                m.write_text(bad)
            rc, out = self.run_ship("--from-step", "4")
            self.assertEqual(rc, 0, out)
            self.assertEqual(self.calls_text().count("SCPGET"), n + 1, bad)

    def test_no_manifest_from_legion_means_whole_copy(self):
        self.run_ship()
        self.cfg["manifest_rc"] = 1
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls_text().count("SCPGET"), 2)

    def test_locally_deleted_file_is_recopied(self):
        self.run_ship()
        (self.fetched() / "Game.exe").unlink()
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.fetched() / "Game.exe").is_file())

    def test_folder_replaced_by_file_still_fetches(self):
        self.cfg["stage_files"] = {"Game.exe": "exe", "X/a.txt": "a"}
        self.assertEqual(self.run_ship()[0], 0)
        self.cfg["stage_files"] = {"Game.exe": "exe", "X": "now a file"}
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertEqual((self.fetched() / "X").read_text(), "now a file")

    def test_file_replaced_by_folder_still_fetches(self):
        self.cfg["stage_files"] = {"Game.exe": "exe", "X": "file"}
        self.assertEqual(self.run_ship()[0], 0)
        self.cfg["stage_files"] = {"Game.exe": "exe", "X/a.txt": "a"}
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertEqual((self.fetched() / "X" / "a.txt").read_text(), "a")

    def test_dropped_folder_is_pruned_like_a_whole_copy(self):
        self.cfg["stage_files"] = {"Game.exe": "exe", "Movies/intro.mp4": "m"}
        self.assertEqual(self.run_ship()[0], 0)
        self.cfg["stage_files"] = {"Game.exe": "exe"}
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertEqual(sorted(p.name for p in self.fetched().iterdir()), ["Game.exe"])

    def test_non_ascii_names_in_oem_code_page_fall_back_to_whole_copy(self):
        old = ('        print("%s|%d|%s" % (name, len(text), hashlib.sha256(text.encode()).hexdigest()))')
        new = ('        sys.stdout.flush()\n'
               '        sys.stdout.buffer.write(("%s|%d|%s\\r\\n" % (name, len(text), '
               'hashlib.sha256(text.encode()).hexdigest())).encode("cp437"))\n'
               '        sys.stdout.flush()')
        self.assertIn(old, FAKE_SSH)
        make_exec(self.td / "ssh", FAKE_SSH.replace(old, new))
        self.cfg["stage_files"] = {"Game.exe": "exe", "Movies/Café.mp4": "m"}
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertIn("no manifest from the Legion", out)

    def _ssh_with_manifest_extra(self, extra_before, bom=False):
        old = '    files = sorted(cfg.get("stage_files"'
        self.assertIn(old, FAKE_SSH)
        pre = ('    sys.stdout.buffer.write(b"\\xef\\xbb\\xbf"); sys.stdout.flush()\n' if bom else "") + extra_before
        make_exec(self.td / "ssh", FAKE_SSH.replace(old, pre + old))

    def test_broken_manifest_line_means_whole_copy_not_deleted_files(self):
        self.cfg["stage_files"] = {"Game.exe": "exe", "a.pak": "one"}
        self.assertEqual(self.run_ship()[0], 0)
        self._ssh_with_manifest_extra('    print("a.pak|3|")\n')  # a hash failure line
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertIn("no manifest from the Legion", out)
        self.assertTrue((self.fetched() / "a.pak").is_file())

    def test_ssh_stderr_warning_does_not_force_whole_copy(self):
        self._ssh_with_manifest_extra(
            '    sys.stderr.write("** WARNING: connection is not using a post-quantum key exchange algorithm.\\n");'
            ' sys.stderr.flush()\n')
        self.assertEqual(self.run_ship()[0], 0)
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("no manifest from the Legion", out)
        self.assertEqual(self.calls_text().count("SCPGET"), 1)

    def _second_ship_is_whole_copy(self, **cfg):
        self.cfg["stage_files"] = {"Game.exe": "exe", "a.pak": "one"}
        self.assertEqual(self.run_ship()[0], 0)
        self.cfg.update(cfg)
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertIn("no manifest from the Legion", out)
        self.assertEqual(self.calls_text().count("SCPGET"), 2)
        self.assertTrue((self.fetched() / "a.pak").is_file())  # the delta never deleted it

    def test_hash_error_on_stderr_with_rc0_means_whole_copy(self):
        self._second_ship_is_whole_copy(manifest_hidden=["a.pak"])

    def test_hash_error_with_nonzero_rc_means_whole_copy(self):
        self._second_ship_is_whole_copy(manifest_rc_after=1)

    def test_count_mismatch_means_whole_copy(self):
        self._second_ship_is_whole_copy(manifest_count_off=1)

    def test_missing_end_marker_means_whole_copy(self):
        self._second_ship_is_whole_copy(manifest_no_end=True)

    def test_debug_symbols_are_left_out_of_the_fetch(self):
        # mock jam 16: a 2.5 GB .pdb in the stage; it must never reach the PC copy or itch.
        import base64
        seen = []
        ctx = mock.Mock()
        ctx.remote = lambda cmd, label, stdout_only=False: (seen.append(cmd), (1, ""))[1]
        L.remote_manifest(ctx, "C:\\s")
        ps = base64.b64decode(seen[0].rsplit(" ", 1)[1]).decode("utf-16-le")
        self.assertIn("-notin '.pdb','.debug','.sym'", ps)
        self.run_ship()
        full = [c for c in self.calls_text().splitlines() if c.startswith("tar -cf") and " -T " not in c]
        self.assertTrue(full)
        for ext in L.SYMBOL_EXTS:
            self.assertIn(f"--exclude=*{ext}", full[0])

    def test_package_script_zip_limit_is_decimal_1gb(self):
        ps1 = (L.REPO / "scripts" / "package-and-push.ps1").read_text(encoding="utf-8")
        self.assertIn("[long]$MaxBytes = 1000000000,", ps1)

    def test_package_script_moves_symbols_out_before_the_zip(self):
        ps1 = (L.REPO / "scripts" / "package-and-push.ps1").read_text(encoding="utf-8")
        move = ps1.index("-Include *.pdb, *.debug, *.sym")
        self.assertLess(move, ps1.index("tar -a -cf $zipPath"))
        self.assertLess(move, ps1.index("& $butlerExe push"))
        self.assertIn('Join-Path $archiveDir "Symbols"', ps1)
        self.assertIn("Move-Item", ps1[move:ps1.index("tar -a -cf $zipPath")])

    def test_the_manifest_script_fails_hard_and_counts_files(self):
        import base64
        seen = []
        ctx = mock.Mock()
        ctx.remote = lambda cmd, label, stdout_only=False: (seen.append(cmd), (1, ""))[1]
        L.remote_manifest(ctx, "C:\\s")
        ps = base64.b64decode(seen[0].rsplit(" ", 1)[1]).decode("utf-16-le")
        self.assertIn("$ErrorActionPreference='Stop'", ps)
        self.assertIn("exit 1", ps)
        self.assertIn("#END|", ps)

    def test_utf8_bom_on_first_manifest_line_is_ignored(self):
        self._ssh_with_manifest_extra("", bom=True)
        self.assertEqual(self.run_ship()[0], 0)
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertIn("copied 0", out)

    def test_pc_push_failure_reports(self):
        self.cfg["bpush_rc"] = 1
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("butler push failed", out)

    def test_exe_check_failure_blocks_fetch_and_push(self):
        self.cfg["exist"] = self.exist(STAGE + "\\Game.exe")
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertNotIn("SCPGET", self.calls_text())
        self.assertEqual(self.bcalls_text(), "")


class PreflightTests(Rig):
    def assertNothingSynced(self):
        calls = self.calls_text()
        for forbidden in ("tar -xf", "robocopy", "package-and-push", "SCP "):
            self.assertNotIn(forbidden, calls)

    def test_bad_engine_path_fails_before_sync(self):
        self.cfg["exist"] = [L.DEFAULT_BUTLER]
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("engine path wrong on the Legion", out)
        self.assertIn("PREFLIGHT FAIL", out)
        self.assertNothingSynced()

    def test_default_engine_is_the_dev_path_without_a_flag(self):
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertIn('-EnginePath "C:\\Dev\\UE_5.8"', self.calls_text())

    def test_old_engine_path_is_the_fallback(self):
        self.cfg["exist"] = [OLD_ENGINE_BAT if e == ENGINE_BAT else e for e in self.cfg["exist"]]
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertIn('-EnginePath "C:\\UE_5.8"', self.calls_text())

    def test_dev_path_is_probed_first(self):
        self.cfg["exist"] = self.cfg["exist"] + [OLD_ENGINE_BAT]
        self.run_ship()
        self.assertIn('-EnginePath "C:\\Dev\\UE_5.8"', self.calls_text())

    def test_unanswered_preferred_engine_probe_stops_instead_of_falling_back(self):
        ctx = mock.Mock()
        ctx.a = mock.Mock(engine=None)
        ctx.probe = lambda cmd, label, timeout=15: (124, "timed out") if "Dev" in cmd else (0, "EXISTS")
        err = L.resolve_engine(ctx)
        self.assertIn("C:\\Dev\\UE_5.8", err)
        self.assertIsNone(ctx.a.engine)

    def test_no_engine_found_names_every_path_tried(self):
        self.cfg["exist"] = [L.DEFAULT_BUTLER]
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("C:\\Dev\\UE_5.8", out)
        self.assertIn("C:\\UE_5.8", out)
        self.assertNothingSynced()

    def test_no_preflight_takes_the_dev_path_without_probing(self):
        self.cfg["exist"] = [L.DEFAULT_BUTLER]
        rc, out = self.run_ship("--no-preflight")
        self.assertIn('-EnginePath "C:\\Dev\\UE_5.8"', self.calls_text())
        self.assertNotIn("RunUAT", self.calls_text())

    def test_explicit_engine_wins_and_is_not_probed_for_others(self):
        self.cfg["exist"] = self.cfg["exist"] + ["D:\\UE\\Engine\\Build\\BatchFiles\\RunUAT.bat"]
        rc, out = self.run_ship("--engine", "D:\\UE")
        self.assertEqual(rc, 0, out)
        self.assertIn('-EnginePath "D:\\UE"', self.calls_text())
        self.assertNotIn("Dev\\UE_5.8", self.calls_text())

    def test_explicit_wrong_engine_fails_and_does_not_fall_back(self):
        rc, out = self.run_ship("--engine", "D:\\Nope")
        self.assertEqual(rc, 1)
        self.assertIn("D:\\Nope", out)
        self.assertNothingSynced()

    def test_itch_dns_failure_on_pc_fails_before_sync(self):
        def boom(name):
            raise OSError("Name or service not known")
        with mock.patch.object(L, "resolve_host", boom):
            rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("api.itch.io", out)
        self.assertIn("DNS", out)
        self.assertNothingSynced()

    def test_itch_dns_failure_on_legion_when_pushing_from_legion(self):
        self.cfg["nslookup"] = "*** can't find api.itch.io: Non-existent domain"
        rc, out = self.run_ship("--push-from", "device-host")
        self.assertEqual(rc, 1)
        self.assertIn("the Legion cannot resolve api.itch.io", out)
        self.assertNothingSynced()

    def test_pc_dns_is_not_checked_on_the_legion_and_vice_versa(self):
        rc, _ = self.run_ship()
        self.assertEqual(rc, 0)
        self.assertNotIn("nslookup", self.calls_text())

    def test_ssh_down_is_one_clear_line_and_stops(self):
        self.cfg["ssh_down"] = True
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("ssh to legion failed", out)
        self.assertEqual(len(self.calls_text().splitlines()), 1)

    def test_every_problem_gets_its_own_line(self):
        self.cfg["exist"] = []
        self.cfg["free"] = 1 * 2**30
        rc, out = self.run_ship("--push-from", "device-host")
        self.assertEqual(rc, 1)
        fails = [ln for ln in out.splitlines() if "PREFLIGHT FAIL" in ln]
        self.assertGreaterEqual(len(fails), 3)  # engine, disk, butler
        self.assertTrue(any("disk low" in f for f in fails))
        self.assertTrue(any("butler missing" in f for f in fails))

    def test_missing_pc_butler(self):
        rc, out = self.run_ship("--pc-butler", str(self.td / "nope"))
        self.assertEqual(rc, 1)
        self.assertIn("butler not found or not executable on the PC", out)

    def test_non_executable_pc_butler_fails_preflight(self):
        b = self.td / "butler-noexec"
        b.write_text("#!/bin/sh\nexit 0\n")
        b.chmod(0o644)
        rc, out = self.run_ship("--pc-butler", str(b))
        self.assertEqual(rc, 1)
        self.assertIn("not executable", out)

    def test_unrunnable_butler_without_preflight_stops_cleanly(self):
        rc, out = self.run_ship("--no-preflight", "--pc-butler", str(self.td / "nope"))
        self.assertEqual(rc, 1)
        self.assertIn("STOPPED", out)
        self.assertIn("cannot run the PC butler", out)

    def test_kill_leftovers_does_not_kill_when_another_check_fails(self):
        self.cfg["tasks"] = LEFTOVER
        self.cfg["exist"] = [L.DEFAULT_BUTLER]  # bad engine path
        rc, out = self.run_ship("--kill-leftovers")
        self.assertEqual(rc, 1)
        self.assertNotIn("taskkill", self.calls_text())
        def boom(name):
            raise OSError("no dns")
        self.cfg["exist"] = self.exist()
        with mock.patch.object(L, "resolve_host", boom):
            rc, out = self.run_ship("--kill-leftovers")
        self.assertEqual(rc, 1)
        self.assertNotIn("taskkill", self.calls_text())

    def test_missing_remote_root_does_not_block_first_ship(self):
        fake = FAKE_SSH.replace('if cmd.startswith("dir /-c"):\n    print(',
                                'if cmd.startswith("dir /-c") and cfg.get("root_missing"):\n'
                                '    print("File Not Found")\n    sys.exit(1)\n'
                                'if cmd.startswith("dir /-c"):\n    print(')
        self.assertNotEqual(fake, FAKE_SSH)
        make_exec(self.td / "ssh", fake)
        self.cfg["root_missing"] = True
        rc, out = self.run_ship()
        self.assertEqual(rc, 0, out)
        self.assertIn("disk check skipped", out)

    def test_leftover_processes_fail_without_consent(self):
        self.cfg["tasks"] = LEFTOVER
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("leftover game processes", out)
        self.assertIn("unrealgame.exe", out)
        self.assertNotIn("taskkill", self.calls_text())
        self.assertNothingSynced()

    def test_kill_leftovers_kills_then_continues(self):
        self.cfg["tasks"] = LEFTOVER
        rc, out = self.run_ship("--kill-leftovers")
        self.assertEqual(rc, 0, out)
        calls = self.calls_text()
        self.assertIn('taskkill /F /T /IM "unrealgame.exe"', calls)
        self.assertNotIn("explorer", calls.split("taskkill")[1].splitlines()[0])  # only the game image
        self.assertLess(calls.index("taskkill"), calls.index("tar -xf"))

    def test_game_named_processes_count_as_leftovers(self):
        self.cfg["tasks"] = '"Game-Win64-Shipping.exe","9","Console","1","1 K"'
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("game-win64-shipping.exe", out)

    def test_dry_run_with_kill_leftovers_does_not_kill(self):
        self.cfg["tasks"] = LEFTOVER
        rc, out = self.run_ship("--kill-leftovers", dry=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("would kill", out)
        self.assertNotIn("taskkill", self.calls_text())

    def test_dry_run_checks_paths_on_the_legion(self):
        self.cfg["exist"] = [L.DEFAULT_BUTLER]
        rc, out = self.run_ship(dry=True)
        self.assertEqual(rc, 1)
        self.assertIn("engine path wrong on the Legion", out)

    def test_no_preflight_flag_skips_it(self):
        self.cfg["exist"] = [STAGE + "\\Game.exe", UNREAL]
        rc, out = self.run_ship("--no-preflight")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("RunUAT", self.calls_text())

    def test_failing_preflight_is_fast(self):
        import time
        self.cfg["exist"] = []
        t0 = time.monotonic()
        rc, _ = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertLess(time.monotonic() - t0, 30)

    def test_helpers(self):
        self.assertTrue(L.nslookup_ok("Server: x\nName: api.itch.io\nAddress: 1.2.3.4"))
        self.assertFalse(L.nslookup_ok("*** UnKnown can't find api.itch.io: No response from server"))
        # no PTR for the DNS server: header times out, the real answer still comes
        self.assertTrue(L.nslookup_ok("DNS request timed out.\n timeout was 2 seconds.\nServer: UnKnown\n"
                                      "Address: 1.1.1.1\n\nNon-authoritative answer:\nName: api.itch.io\nAddresses: 1.2.3.4"))
        self.assertFalse(L.nslookup_ok("DNS request timed out.\n timeout was 2 seconds.\nServer: UnKnown\n"
                                       "*** UnKnown can't find api.itch.io: No response from server"))
        self.assertEqual(L.free_bytes_from_dir("   3 Dir(s)  123,456,789 bytes free"), 123456789)
        self.assertIsNone(L.free_bytes_from_dir("nothing"))
        self.assertEqual(L.running_images(LEFTOVER), {"unrealgame.exe", "explorer.exe"})


class ResumeTests(Rig):
    def test_from_step_3_skips_sync_and_package(self):
        rc, out = self.run_ship("--from-step", "3")
        self.assertEqual(rc, 0, out)
        calls = self.calls_text()
        for skipped in ("tar -xf", "robocopy", "package-and-push", "SCP ", "RunUAT"):
            self.assertNotIn(skipped, calls)
        self.assertIn("Game.exe\" (echo", calls)  # the check still ran
        self.assertIn("push ", self.bcalls_text())
        self.assertRegex(out.splitlines()[-1], r"^SHIPPED: .*check .*m push .*m status")
        self.assertNotRegex(out.splitlines()[-1], r"sync|package")

    def test_from_step_3_without_a_packaged_stage_says_so(self):
        self.cfg["exist"] = self.exist()
        rc, out = self.run_ship("--from-step", "3")
        self.assertEqual(rc, 1)
        self.assertIn("needs the packaged build", out)
        self.assertIn("start at step 2", out)

    def test_from_step_4_pushes_without_rechecking(self):
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("UnrealGame.exe\" (echo", self.calls_text())
        self.assertIn("push ", self.bcalls_text())

    def test_from_step_4_skips_engine_probe(self):
        self.cfg["exist"] = [STAGE + "\\Game.exe", MARKER]  # engine path unknown: irrelevant when resuming
        rc, out = self.run_ship("--from-step", "4")
        self.assertEqual(rc, 0, out)

    def test_from_step_2_repackages_without_resync(self):
        rc, out = self.run_ship("--from-step", "2")
        self.assertEqual(rc, 0, out)
        calls = self.calls_text()
        self.assertIn("package-and-push", calls)
        self.assertNotIn("tar -xf", calls)

    def test_resume_after_failed_package_must_not_push(self):
        self.cfg.update(package_rc=1, package_out="Zip is 1300.0 MB, over the 1024 MB gate limit")
        rc, _ = self.run_ship()
        self.assertEqual(rc, 1)
        calls = self.calls_text()
        self.assertIn("del /q", calls)  # marker cleared before the package ran
        self.assertNotIn("echo ok>", calls)  # and not rewritten after the failure
        self.assertNotIn(MARKER, self.cfg["exist"])  # the fake Legion really lost the marker
        self.assertIn(STAGE + "\\Game.exe", self.cfg["exist"])  # while the rejected stage is still there
        rc, out = self.run_ship("--from-step", "3")
        self.assertEqual(rc, 1)
        self.assertIn("not marked as finished", out)
        self.assertEqual(self.bcalls_text(), "")

    def test_successful_package_writes_the_marker_after_the_script(self):
        self.run_ship()
        calls = self.calls_text()
        self.assertLess(calls.index("package-and-push.ps1"), calls.index("echo ok>"))
        self.assertIn("Game.packaged-ok", calls)

    def test_from_step_5_pc_needs_nothing_on_the_legion(self):
        self.cfg["exist"] = self.exist()
        self.cfg["ssh_down"] = True
        rc, out = self.run_ship("--from-step", "5")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls_text(), "")
        self.assertIn("status ", self.bcalls_text())

    def test_from_step_5_legion_push_still_needs_ssh(self):
        self.cfg["ssh_down"] = True
        rc, out = self.run_ship("--from-step", "5", "--push-from", "device-host")
        self.assertEqual(rc, 1)
        self.assertIn("ssh to legion failed", out)

    def test_sinkholed_dns_is_not_resolved(self):
        sink = "Server: pi.hole\nAddress: <lan-host>\n\nName: api.itch.io\nAddress: 0.0.0.0\n"
        self.assertFalse(L.nslookup_ok(sink))
        self.assertFalse(L.nslookup_ok("Name: api.itch.io\nAddresses: ::\n          0.0.0.0"))
        self.assertFalse(L.nslookup_ok("Name: api.itch.io\nAddress: 127.0.0.1"))
        self.assertTrue(L.nslookup_ok("Name: api.itch.io\nAddresses: ::\n          104.18.0.1"))
        import socket
        fake = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("0.0.0.0", 443))]
        with mock.patch.object(socket, "getaddrinfo", lambda *a, **k: fake):
            with mock.patch.object(L, "resolve_host", ORIG_RESOLVE):
                with self.assertRaises(OSError):
                    L.resolve_host("api.itch.io")

    def test_failed_marker_clear_stops_before_packaging(self):
        fake = FAKE_SSH.replace('if " del /q " in cmd or', 'if " del /q " in cmd and cfg.get("del_fails"):\n'
                                '    sys.exit(255)\nif " del /q " in cmd or')
        self.assertNotEqual(fake, FAKE_SSH)
        make_exec(self.td / "ssh", fake)
        self.cfg["del_fails"] = True
        rc, out = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn("could not clear the packaged marker", out)
        self.assertNotIn("package-and-push", self.calls_text())

    def test_failed_clear_then_resume_is_refused(self):
        wrap = ('#!/usr/bin/env python3\nimport os, sys\nif " del /q " in sys.argv[2]:\n    sys.exit(255)\n'
                'os.execv(sys.executable, [sys.executable, %r] + sys.argv[1:])\n')
        real = self.td / "ssh_real"
        (self.td / "ssh").rename(real)
        make_exec(self.td / "ssh", wrap % str(real))
        rc, _ = self.run_ship()
        self.assertEqual(rc, 1)
        self.assertIn(MARKER, self.cfg["exist"])  # the remote marker survived the failed delete
        (self.td / "ssh").unlink()
        real.rename(self.td / "ssh")
        rc, out = self.run_ship("--from-step", "3")
        self.assertEqual(rc, 1)
        self.assertIn("did not finish packaging cleanly", out)
        self.assertEqual(self.bcalls_text(), "")

    def test_dry_run_does_not_touch_the_state_record(self):
        self.run_ship(dry=True)
        self.assertEqual((self.td / "logs" / "Game.packaged-state").read_text().strip(), "ok")

    def test_lan_address_answer_is_a_sinkhole(self):
        # Pi-hole BLOCKINGMODE=IP answers with its own LAN address
        self.assertFalse(L.nslookup_ok("Name: api.itch.io\nAddress: <lan-host>"))
        self.assertFalse(L.nslookup_ok("Name: api.itch.io\nAddress: 10.1.2.3"))
        self.assertFalse(L.nslookup_ok("Name: api.itch.io\nAddress: fd00::20"))
        self.assertTrue(L.nslookup_ok("Name: api.itch.io\nAddresses: <lan-host>\n 104.18.0.1"))
        import socket
        fake = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("<lan-host>", 443))]
        with mock.patch.object(socket, "getaddrinfo", lambda *a, **k: fake):
            with mock.patch.object(L, "resolve_host", ORIG_RESOLVE):
                with self.assertRaises(OSError):
                    L.resolve_host("api.itch.io")

    def test_bad_step_is_rejected(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            L.main([str(self.proj), "--from-step", "9"])


if __name__ == "__main__":
    unittest.main()

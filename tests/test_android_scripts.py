"""Tests for the Android spike scripts. Fake commands via PATH; no real UAT, adb, network or GPU."""
import os
import stat
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, "scripts", "android_toolchain_check.sh")
PACKAGE = os.path.join(ROOT, "scripts", "android_package.sh")
INSTALL = os.path.join(ROOT, "scripts", "android_install.sh")


def write_exe(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("#!/usr/bin/env bash\n" + body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


def run(cmd, env_extra=None, path_dirs=()):
    env = {"HOME": env_extra.pop("HOME", "/nonexistent") if env_extra else "/nonexistent"}
    env["PATH"] = ":".join(list(path_dirs) + ["/usr/bin", "/bin"])
    env.update(env_extra or {})
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def make_sdk(base, platform="35", tools="35.0.1", ndk="27.2.12479018", adb=True):
    sdk = os.path.join(base, "Sdk")
    for sub in (f"platforms/android-{platform}", f"build-tools/{tools}", f"ndk/{ndk}"):
        os.makedirs(os.path.join(sdk, sub))
    if adb:
        write_exe(os.path.join(sdk, "platform-tools", "adb"), "exit 0\n")
    return sdk


def make_jvm(base, name="java-21-openjdk", with_javac=True):
    d = os.path.join(base, "jvm", name)
    if with_javac:
        write_exe(os.path.join(d, "bin", "javac"), "exit 0\n")
    else:
        os.makedirs(d)
    return os.path.dirname(d)


def make_ue(base, with_setup=True):
    ue = os.path.join(base, "UE")
    if with_setup:
        write_exe(os.path.join(ue, "Engine", "Extras", "Android", "SetupAndroid.sh"), "exit 0\n")
    return ue


class ToolchainCheck(unittest.TestCase):
    def test_all_present_exit_0(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(["bash", CHECK, "--sdk", make_sdk(t), "--ue-root", make_ue(t), "--jvm-dir", make_jvm(t)])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("RESULT: all present", r.stdout)

    def test_owner_install_shape_reports_gaps(self):
        # the desktop today: platforms 36/37.0, build-tools 35.0.0, NDK r27c, JDK 17
        with tempfile.TemporaryDirectory() as t:
            sdk = os.path.join(t, "Sdk")
            for sub in ("platforms/android-36", "platforms/android-37.0", "build-tools/35.0.0", "ndk/27.2.12479018"):
                os.makedirs(os.path.join(sdk, sub))
            r = run(["bash", CHECK, "--sdk", sdk, "--ue-root", make_ue(t), "--jvm-dir", make_jvm(t, "java-17-openjdk")])
            self.assertEqual(r.returncode, 1)
            out = r.stdout
            self.assertRegex(out, r"MISSING\s+platform\s")
            self.assertRegex(out, r"MISSING\s+build-tools\s")
            self.assertRegex(out, r"OK\s+ndk\s")
            self.assertRegex(out, r"MISSING\s+jdk\s")
            self.assertIn("platforms;android-35", out)
            self.assertIn("build-tools;35.0.1", out)
            self.assertIn("sudo pacman -S jdk21-openjdk", out)

    def test_jre_only_dir_is_not_a_jdk(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(["bash", CHECK, "--sdk", make_sdk(t), "--ue-root", make_ue(t),
                     "--jvm-dir", make_jvm(t, with_javac=False)])
            self.assertEqual(r.returncode, 1)
            self.assertRegex(r.stdout, r"MISSING\s+jdk\s")

    def test_missing_ue_root_fails(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(["bash", CHECK, "--sdk", make_sdk(t), "--jvm-dir", make_jvm(t)])
            self.assertEqual(r.returncode, 1)
            self.assertRegex(r.stdout, r"MISSING\s+ue-setup")

    def test_no_install_without_flag(self):
        with tempfile.TemporaryDirectory() as t:
            sdk = make_sdk(t, platform="34")
            marker = os.path.join(t, "ran")
            write_exe(os.path.join(sdk, "cmdline-tools", "latest", "bin", "sdkmanager"), f"touch {marker}\n")
            run(["bash", CHECK, "--sdk", sdk, "--ue-root", make_ue(t), "--jvm-dir", make_jvm(t)])
            self.assertFalse(os.path.exists(marker))

    def test_install_runs_sdkmanager_for_missing_only(self):
        with tempfile.TemporaryDirectory() as t:
            home = os.path.join(t, "home")
            sdk = make_sdk(os.path.join(home, "Android"), platform="34")
            log = os.path.join(t, "sm.log")
            write_exe(os.path.join(sdk, "cmdline-tools", "latest", "bin", "sdkmanager"), f'echo "$@" > {log}\n')
            run(["bash", CHECK, "--sdk", sdk, "--ue-root", make_ue(t), "--jvm-dir", make_jvm(t), "--install"],
                {"HOME": home})
            args = open(log).read()
            self.assertIn("platforms;android-35", args)
            self.assertNotIn("ndk", args)

    def test_install_refuses_sdk_outside_home(self):
        with tempfile.TemporaryDirectory() as t:
            home = os.path.join(t, "home")
            os.makedirs(home)
            sdk = make_sdk(t, platform="34")  # outside home
            r = run(["bash", CHECK, "--sdk", sdk, "--ue-root", make_ue(t), "--jvm-dir", make_jvm(t), "--install"],
                    {"HOME": home})
            self.assertEqual(r.returncode, 3)
            self.assertIn("not under $HOME", r.stderr)


class PackageGate(unittest.TestCase):
    def penv(self, t, state, **more):
        env = {"MEGAJAM_ANDROID_STATE": state, "MEGAJAM_JVM_DIR": os.path.join(t, "jvm")}
        env.update(more)
        return env

    def setup_env(self, t, pgrep_rc, preflight_rc, procs=()):
        """Fake pgrep -f PATTERN: ERE over `procs` lines (exit 0/1), or a fixed exit code if pgrep_rc >= 2."""
        bin_dir = os.path.join(t, "bin")
        procfile = os.path.join(t, "procs")
        with open(procfile, "w") as f:
            f.write("".join(p + "\n" for p in procs))
        if pgrep_rc >= 2:
            write_exe(os.path.join(bin_dir, "pgrep"), f"exit {pgrep_rc}\n")
        else:
            write_exe(os.path.join(bin_dir, "pgrep"), f'[ "$1" = -f ] || exit 2\ngrep -qE -- "$2" {procfile}\n')
        make_jvm(t)  # jvm/java-21-openjdk with bin/javac
        write_exe(os.path.join(bin_dir, "gpu-preflight"), f"exit {preflight_rc}\n")
        ue = os.path.join(t, "UE")
        uat_log = os.path.join(t, "uat.args")
        write_exe(os.path.join(ue, "Engine", "Build", "BatchFiles", "RunUAT.sh"),
                  f'echo "$@" > {uat_log}\n'
                  'for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#*=}";; esac; done\n'
                  'mkdir -p "$d/Android_ASTC"; head -c 2048 /dev/zero > "$d/Android_ASTC/Game.apk"\n')
        proj = os.path.join(t, "Mock.uproject")
        open(proj, "w").write("{}")
        state = os.path.join(t, "state")
        return bin_dir, ue, proj, state, uat_log

    def test_refuses_when_editor_runs(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0, procs=["/x/UnrealEditor Mock.uproject"])
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 4)
            self.assertIn("UnrealEditor", r.stderr)
            self.assertFalse(os.path.exists(uat))

    def test_refuses_on_mock_loop_by_default_in_every_name_form(self):
        for cmd in ("bash claude-loop --bg -n megajam-mock", "bash claude-loop --bg --name megajam-mock",
                    "bash claude-loop --bg -n=megajam-mock", "bash claude-loop --bg --name=megajam-mock"):
            with self.subTest(cmd=cmd), tempfile.TemporaryDirectory() as t:
                b, ue, proj, state, uat = self.setup_env(t, 1, 0, procs=[cmd])
                r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
                self.assertEqual(r.returncode, 4)
                self.assertIn("ANDROID_ALLOW_MOCK_LOOP", r.stderr)
                self.assertFalse(os.path.exists(uat))

    def test_refuses_on_revived_loop_cmdline(self):
        # claude-loop-revive runs claude_loop.sh (underscore), prompt before -n; no "claude-loop" substring
        cmd = ('bash /x/workflow-tools-live/scripts/claude_loop.sh --bg "Fresh session after an automatic handoff '
               '(the machine restarted). Read /x/megajam-mock/.handoff/loop-1/HANDOFF.md first" -n megajam-mock')
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0, procs=[cmd])
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 4)
            self.assertFalse(os.path.exists(uat))

    def test_other_loop_names_do_not_match(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0, procs=["bash claude-loop --bg -n megajam-mock-2"])
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_mock_loop_optin_passes_when_no_editor(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0, procs=["bash claude-loop --bg -n megajam-mock"])
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state, ANDROID_ALLOW_MOCK_LOOP="1"), [b])
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_optin_still_refuses_with_editor(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(
                t, 1, 0, procs=["bash claude-loop --bg -n megajam-mock", "UnrealEditor Mock.uproject"])
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state, ANDROID_ALLOW_MOCK_LOOP="1"), [b])
            self.assertEqual(r.returncode, 4)
            self.assertFalse(os.path.exists(uat))

    def test_pgrep_failure_fails_closed(self):
        for rc in (2, 3, 127):
            with self.subTest(rc=rc), tempfile.TemporaryDirectory() as t:
                b, ue, proj, state, uat = self.setup_env(t, rc, 0)
                r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
                self.assertEqual(r.returncode, 4)
                self.assertFalse(os.path.exists(uat))

    def test_refuses_without_real_jdk21(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0)
            os.remove(os.path.join(t, "jvm", "java-21-openjdk", "bin", "javac"))  # JRE only
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 2)
            self.assertIn("JDK 21", r.stderr)
            self.assertFalse(os.path.exists(uat))

    def test_exports_jdk21_as_java_home(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0)
            write_exe(os.path.join(ue, "Engine", "Build", "BatchFiles", "RunUAT.sh"),
                      f'echo "$JAVA_HOME" > {t}/jh\nexit 0\n')
            run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state, JAVA_HOME="/usr/lib/jvm/java-17-openjdk"), [b])
            with open(os.path.join(t, "jh")) as f:
                self.assertEqual(f.read().strip(), os.path.join(t, "jvm", "java-21-openjdk"))

    def test_stale_apk_is_not_reported(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, pgrep_rc=1, preflight_rc=0)
            write_exe(os.path.join(ue, "Engine", "Build", "BatchFiles", "RunUAT.sh"), "exit 0\n")  # packages nothing
            out = os.path.join(t, "out")
            old = os.path.join(out, "Android_ASTC", "Old.apk")
            os.makedirs(os.path.dirname(old))
            with open(old, "wb") as f:
                f.write(b"\0" * 100)
            # mtime stays "now" on purpose: the old APK is as fresh as the run (the hard case)
            r = run(["bash", PACKAGE, proj, "--ue-root", ue, "--out", out], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 5)
            self.assertNotIn("Old.apk", r.stdout)

    def test_refuses_when_preflight_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, pgrep_rc=1, preflight_rc=1)
            r = run(["bash", PACKAGE, proj, "--ue-root", ue], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 4)
            self.assertIn("gpu-preflight", r.stderr)
            self.assertFalse(os.path.exists(uat))

    def test_runs_uat_and_reports_apk(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, pgrep_rc=1, preflight_rc=0)
            r = run(["bash", PACKAGE, proj, "--ue-root", ue, "--config", "Shipping", "--sdk", "/fake/sdk"],
                    self.penv(t, state), [b])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            args = open(uat).read()
            for want in ("BuildCookRun", "-platform=Android", "-cookflavor=ASTC", "-clientconfig=Shipping", proj):
                self.assertIn(want, args)
            self.assertIn("SIZE: 2048 bytes", r.stdout)
            self.assertRegex(r.stdout, r"APK: .*Game\.apk")
            self.assertRegex(r.stdout, r"WALL: \d+s")
            self.assertTrue(any(f.startswith("package-") for f in os.listdir(state)))

    def test_bad_config_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            b, ue, proj, state, uat = self.setup_env(t, 1, 0)
            r = run(["bash", PACKAGE, proj, "--ue-root", ue, "--config", "Debug"], self.penv(t, state), [b])
            self.assertEqual(r.returncode, 2)


class InstallCommands(unittest.TestCase):
    def test_dry_run_builds_expected_adb_lines(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(["bash", INSTALL, "/x/Game.apk", "--addr", "<lan-host>:37123", "--package", "com.a.b", "--dry-run",
                     "--out", os.path.join(t, "shots")])
            self.assertEqual(r.returncode, 0, r.stderr)
            lines = r.stdout.strip().splitlines()
            self.assertEqual(lines[0], "adb connect <lan-host>:37123")
            self.assertEqual(lines[1], "adb -s <lan-host>:37123 install -r /x/Game.apk")
            self.assertEqual(lines[2], "adb -s <lan-host>:37123 shell monkey -p com.a.b -c android.intent.category.LAUNCHER 1")
            self.assertIn("shell screencap -p /sdcard/megajam_shot_", lines[3])
            self.assertIn(" pull /sdcard/megajam_shot_", lines[4])
            self.assertTrue(lines[-1].endswith(".png"))

    def test_requires_addr(self):
        r = run(["bash", INSTALL, "/x/Game.apk", "--dry-run"])
        self.assertEqual(r.returncode, 2)

    def test_real_path_uses_fake_adb_and_prints_png(self):
        with tempfile.TemporaryDirectory() as t:
            log = os.path.join(t, "adb.log")
            write_exe(os.path.join(t, "bin", "adb"), f'echo "$@" >> {log}\nexit 0\n')
            apk = os.path.join(t, "Game.apk")
            open(apk, "w").write("x")
            r = run(["bash", INSTALL, apk, "--addr", "1.2.3.4:5555", "--wait", "0", "--out", os.path.join(t, "s")],
                    path_dirs=[os.path.join(t, "bin")])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(r.stdout.strip().endswith(".png"))
            calls = open(log).read().splitlines()
            self.assertEqual(calls[0], "connect 1.2.3.4:5555")
            self.assertIn("-s 1.2.3.4:5555 install -r " + apk, calls)


class Templates(unittest.TestCase):
    def test_engine_template_substitutes(self):
        from string import Template
        txt = open(os.path.join(ROOT, "Config", "android", "DefaultEngine.android.ini.tmpl")).read()
        out = Template(txt).substitute(package_name="com.x.y", display_name="Mock")
        for want in ("PackageName=com.x.y", "MinSDKVersion=26", "bMultiTargetFormat_ASTC=True", "Orientation=Landscape"):
            self.assertIn(want, out)

    def test_input_template_has_touch_interface(self):
        txt = open(os.path.join(ROOT, "Config", "android", "DefaultInput.android.ini.tmpl")).read()
        self.assertIn("DefaultTouchInterface=", txt)


if __name__ == "__main__":
    unittest.main()

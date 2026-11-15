"""Launch preflight in legion_playtest.deploy_and_register: locked screen, leftover game. Fake ssh only."""
import base64
import io
import os
import sys
import unittest
from contextlib import redirect_stderr
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import legion_playtest as lp  # noqa: E402


class FakeSsh:
    """Answers the lock check with `lock_line`; taskkill gets rc from `kill_rc` (default: not found)."""

    def __init__(self, lock_line="LOCKAPP_LIVE=0 LOGONUI=0", lock_rc=0, kill_rc=None):
        self.lock_line, self.lock_rc, self.kill_rc, self.calls = lock_line, lock_rc, kill_rc or {}, []

    def __call__(self, host, cmd, timeout=60):
        self.calls.append(cmd)
        if "-EncodedCommand" in cmd:
            return self.lock_rc, "#< CLIXML\n" + self.lock_line + "\n<Objs/>\n", "" if self.lock_rc == 0 else "boom"
        if cmd.startswith("taskkill"):
            name = cmd.rsplit(" ", 1)[1]
            return self.kill_rc.get(name, lp.TASKKILL_NOT_FOUND), "", "ERROR: not found"
        raise AssertionError(f"unexpected ssh command {cmd!r}")


class LockCheck(unittest.TestCase):
    def test_suspended_lockapp_is_not_locked(self):  # the state the Legion is in after an unlock
        self.assertFalse(lp.legion_locked("device-host", FakeSsh("LOCKAPP_LIVE=0 LOGONUI=0")))

    def test_awake_lockapp_is_locked(self):
        self.assertTrue(lp.legion_locked("device-host", FakeSsh("LOCKAPP_LIVE=12 LOGONUI=0")))

    def test_logonui_is_locked(self):
        self.assertTrue(lp.legion_locked("device-host", FakeSsh("LOCKAPP_LIVE=0 LOGONUI=1")))

    def test_failed_check_raises_not_guesses(self):
        with self.assertRaisesRegex(RuntimeError, "could not check the Legion lock screen"):
            lp.legion_locked("device-host", FakeSsh(lock_rc=255))
        with self.assertRaisesRegex(RuntimeError, "could not check"):
            lp.legion_locked("device-host", FakeSsh(lock_line="garbage"))

    def test_encoded_command_round_trips_and_checks_threads(self):
        cmd = lp.encoded_powershell(lp.LOCK_PS)
        self.assertNotIn("$", cmd)  # nothing for bash/ssh/cmd to expand
        script = base64.b64decode(cmd.rsplit(" ", 1)[1]).decode("utf-16-le")
        self.assertEqual(script, lp.LOCK_PS)
        self.assertIn("Suspended", script)
        self.assertIn("LogonUI", script)


class Preflight(unittest.TestCase):
    def test_locked_fails_fast_before_any_kill(self):
        ssh = FakeSsh("LOCKAPP_LIVE=5 LOGONUI=0")
        with self.assertRaises(RuntimeError) as cm:
            lp.preflight_launch("device-host", "MockGame", ssh, sleep=lambda s: None)
        self.assertIn("Unlock the Legion screen", str(cm.exception))
        self.assertEqual(len(ssh.calls), 1)  # only the lock check ran

    def test_leftover_unrealgame_is_killed_then_waits(self):
        ssh, slept = FakeSsh(kill_rc={"UnrealGame.exe": 0}), []
        with redirect_stderr(io.StringIO()):
            stopped = lp.preflight_launch("device-host", "MockGame", ssh, sleep=slept.append)
        self.assertEqual(stopped, ["UnrealGame.exe"])
        self.assertIn("taskkill /F /T /IM UnrealGame.exe", ssh.calls)
        self.assertIn("taskkill /F /T /IM MockGame.exe", ssh.calls)
        self.assertEqual(slept, [2])

    def test_nothing_left_over_no_wait(self):
        slept = []
        self.assertEqual(lp.preflight_launch("device-host", "MockGame", FakeSsh(), sleep=slept.append), [])
        self.assertEqual(slept, [])

    def test_game_named_unrealgame_not_killed_twice(self):
        ssh = FakeSsh()
        lp.kill_leftover_games("device-host", "UnrealGame", ssh)
        self.assertEqual(sum(c.startswith("taskkill") for c in ssh.calls), 1)

    def test_kill_failure_stops_with_plain_message(self):
        ssh = FakeSsh(kill_rc={"UnrealGame.exe": 1})
        with self.assertRaisesRegex(RuntimeError, "leftover UnrealGame.exe is still running"):
            lp.preflight_launch("device-host", "MockGame", ssh, sleep=lambda s: None)


class DeployRunsPreflightFirst(unittest.TestCase):
    def test_locked_screen_stops_before_scp_or_schtasks(self):
        with mock.patch.object(lp, "_ssh_rc", FakeSsh("LOCKAPP_LIVE=3 LOGONUI=0")), \
                mock.patch.object(lp, "run", side_effect=AssertionError("deploy must not start")) as run:
            with self.assertRaisesRegex(RuntimeError, "Unlock the Legion screen"):
                lp.deploy_and_register("device-host", r"C:\Dev\G.zip", "MockGame", "MegaJamLaunchGame")
        run.assert_not_called()

    def test_unlocked_deploy_goes_ahead(self):
        out = mock.Mock(stdout='noise\n{"exePath": "C:\\\\g\\\\MockGame.exe", "logPath": "x"}\n')
        with mock.patch.object(lp, "_ssh_rc", FakeSsh()), mock.patch.object(lp, "run", return_value=out) as run:
            got = lp.deploy_and_register("device-host", r"C:\Dev\G.zip", "MockGame", "MegaJamLaunchGame")
        self.assertEqual(got["logPath"], "x")
        self.assertEqual(run.call_count, 3)  # mkdir, scp, remote launch script

    def test_main_prints_one_plain_line_and_exits_2(self):
        argv = ["legion_playtest.py", "--remote-zip", r"C:\Dev\G.zip", "--game-name", "MockGame"]
        err = io.StringIO()
        with mock.patch.object(lp, "_ssh_rc", FakeSsh("LOCKAPP_LIVE=0 LOGONUI=1")), \
                mock.patch.object(lp, "run", side_effect=AssertionError("no deploy")), \
                mock.patch.object(sys, "argv", argv), redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                lp.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("STOP: The Legion screen is locked", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()

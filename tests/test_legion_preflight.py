import importlib.util
import io
import json
import os
import re
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("legion_preflight", os.path.join(ROOT, "scripts", "legion_preflight.py"))
pf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pf)

EXE = r"C:\Dev\Game\agent_test\Game.exe"
GOOD = {
    "obsInstalled": True, "obsWebsocket": True,
    "firewallPrograms": [EXE], "mjTasks": [],
    "consoleActive": True, "locked": False,
}


def facts(**over):
    d = dict(GOOD)
    d.update(over)
    return d


class Evaluate(unittest.TestCase):
    def test_all_good(self):
        self.assertEqual(pf.evaluate(GOOD, "Game.exe", EXE), [])

    def test_obs_missing(self):
        f = pf.evaluate(facts(obsInstalled=False), "Game.exe", EXE)
        self.assertEqual(len(f), 1)
        self.assertIn("not installed", f[0])

    def test_websocket_down_and_allowed(self):
        self.assertIn("websocket", pf.evaluate(facts(obsWebsocket=False), "Game.exe", EXE)[0])
        self.assertEqual(pf.evaluate(facts(obsWebsocket=False), "Game.exe", EXE, allow_obs_stopped=True), [])

    def test_firewall_missing_prints_owner_command(self):
        f = pf.evaluate(facts(firewallPrograms=[r"C:\Other\x.exe"]), "Game.exe", EXE)
        self.assertEqual(len(f), 1)
        self.assertIn("New-NetFirewallRule", f[0])
        self.assertIn(EXE, f[0])

    def test_firewall_basename_match_case_insensitive(self):
        self.assertTrue(pf.firewall_ok([r"c:\x\unrealgame.EXE"], "UnrealGame.exe", ""))
        self.assertFalse(pf.firewall_ok([r"c:\x\other.exe"], "UnrealGame.exe", ""))
        self.assertFalse(pf.firewall_ok(None, "UnrealGame.exe", ""))

    def test_stale_tasks_listed(self):
        f = pf.evaluate(facts(mjTasks=["MJToolObsStart", "MJOld"]), "Game.exe", EXE)
        self.assertEqual(len(f), 1)
        self.assertIn("MJToolObsStart, MJOld", f[0])

    def test_single_task_as_scalar(self):
        self.assertIn("MJOld", pf.evaluate(facts(mjTasks="MJOld"), "Game.exe", EXE)[0])

    def test_no_console_session(self):
        f = pf.evaluate(facts(consoleActive=False), "Game.exe", EXE)
        self.assertEqual(len(f), 1)
        self.assertIn("No active console", f[0])

    def test_locked(self):
        f = pf.evaluate(facts(locked=True), "Game.exe", EXE)
        self.assertEqual(len(f), 1)
        self.assertIn("locked", f[0])

    def test_several_failures_one_line_each(self):
        f = pf.evaluate({}, "Game.exe", EXE)
        self.assertEqual(len(f), 4)  # obs, websocket, firewall, console (no tasks)


class Collect(unittest.TestCase):
    def test_ssh_timeout_gives_plain_line(self):
        with mock.patch.object(pf, "run", return_value=(124, "", "timed out after 20s")):
            fx, fail = pf.collect("device-host")
        self.assertIsNone(fx)
        self.assertIn("ssh to 'device-host' failed", fail)
        self.assertIn("timed out", fail)

    def test_scp_failure(self):
        def fake(cmd, timeout=0):
            if cmd[0] == "scp":
                return 1, "", "no route"
            return 0, "ok\n", ""
        with mock.patch.object(pf, "run", side_effect=fake):
            fx, fail = pf.collect("device-host")
        self.assertIsNone(fx)
        self.assertIn("could not copy", fail)

    def test_bad_json(self):
        def fake(cmd, timeout=0):
            if cmd[0] == "ssh" and "-File" in cmd[-1]:
                return 1, "garbage", "boom"
            return 0, "ok\n", ""
        with mock.patch.object(pf, "run", side_effect=fake):
            fx, fail = pf.collect("device-host")
        self.assertIsNone(fx)
        self.assertIn("no readable result", fail)

    def test_success(self):
        def fake(cmd, timeout=0):
            if cmd[0] == "ssh" and "-File" in cmd[-1]:
                return 0, "noise\n" + json.dumps(GOOD) + "\n", ""
            return 0, "ok\n", ""
        with mock.patch.object(pf, "run", side_effect=fake):
            fx, fail = pf.collect("device-host")
        self.assertIsNone(fail)
        self.assertEqual(fx, {**GOOD, 'firewallBlocked': []})


class Main(unittest.TestCase):
    def _main(self, argv, fx=None, fail=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(pf, "collect", return_value=(fx, fail)), \
                redirect_stdout(out), redirect_stderr(err):
            rc = pf.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_exit_zero(self):
        rc, out, _ = self._main(["--exe-name", "Game.exe", "--exe-path", EXE], GOOD)
        self.assertEqual((rc, out), (0, ""))

    def test_exit_nonzero_one_line_each(self):
        rc, out, _ = self._main(["--exe-name", "Game.exe", "--exe-path", EXE], facts(locked=True, obsInstalled=False))
        self.assertEqual(rc, 1)
        self.assertEqual(len(out.strip().splitlines()), 2)

    def test_ssh_fail_exit(self):
        rc, out, _ = self._main(["--exe-name", "Game.exe"], None, "ssh to 'device-host' failed (x).")
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "ssh to 'device-host' failed (x).")

    def test_remove_stale_only_deletes_tool_tasks(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            return 0, "", ""
        with mock.patch.object(pf, "run", side_effect=fake):
            removed = pf.remove_stale("device-host", ["MJToolObsStart", "MJOwnerTask"])
        self.assertEqual(removed, ["MJToolObsStart"])
        self.assertEqual(len(calls), 1)
        self.assertIn("/Delete /TN MJToolObsStart", calls[0])


class BlockAndConsole(unittest.TestCase):
    def test_block_rule_beats_allow(self):
        f = dict(GOOD, firewallPrograms=[r"C:\Dev\Game\Game.exe"], firewallBlocked=r"C:\Dev\Game\Game.exe")
        fails = pf.evaluate(f, exe_name="Game.exe")
        self.assertTrue(any("BLOCK" in x for x in fails))

    def test_no_block_passes(self):
        f = dict(GOOD, firewallPrograms=[r"C:\Dev\Game\Game.exe"], firewallBlocked=None)
        self.assertEqual(pf.evaluate(f, exe_name="Game.exe"), [])

    def test_ps1_filters_profile_and_has_home_fallback(self):
        text = open(os.path.join(ROOT, "scripts", "legion_preflight.ps1")).read()
        self.assertIn("Get-NetConnectionProfile", text)
        self.assertIn("'Block'", text)
        self.assertIn("Win32_ComputerSystem", text)
        self.assertIn("Get-Command query", text)

    def test_placeholder_path_rule_is_not_accepted(self):
        fails = pf.evaluate(dict(GOOD, firewallPrograms=[]), "Game.exe", "")
        line = [x for x in fails if "New-NetFirewallRule" in x][0]
        program = re.search(r'-Program "([^"]+)"', line).group(1)
        self.assertNotEqual(pf.evaluate(dict(GOOD, firewallPrograms=[program]), "Game.exe", ""), [])

    def test_exe_name_is_required(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            pf.main(["--host", "device-host"])

    def test_ps1_joins_rules_in_one_pass_and_uses_explorer_owner(self):
        text = open(os.path.join(ROOT, "scripts", "legion_preflight.ps1")).read()
        self.assertIn("InstanceID", text)
        self.assertIn("GetOwner", text)
        self.assertNotIn("SessionId -eq 1", text)


if __name__ == "__main__":
    unittest.main()

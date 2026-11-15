"""Round 3 finding 3: the new 'relaunched between lose and restart' rule only sees a journaled `relaunch`.
cmd_start appends it AFTER b.launch() returns. LegionBackend.launch runs the game task, sleeps warmup (10 s
default) and raises 'not running after launch' if alive() is still False. A packaged UE build that takes
longer than warmup to show its process (first run after deploy) is started but nothing is journaled. The game
then comes up as a fresh run; the tester marks it as 'restart' and the gate passes: restart by relaunch again."""
import unittest

from test_agent_playtest_cli import Base, FakeBackend


class SlowLaunch(FakeBackend):
    def launch(self):
        FakeBackend.launched = True   # schtasks /Run succeeded: the game IS starting
        raise RuntimeError("G is not running after launch (crashed or never started)")


class T(Base):
    def test_relaunch_that_raised_is_still_a_relaunch(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        self.cli("mark", "win", "--evidence", w)
        l = self.shot("look", "--label", "lose-no-way-out")
        self.cli("mark", "lose", "--evidence", l)
        import io
        from contextlib import redirect_stdout, redirect_stderr
        rc = None
        out, err = io.StringIO(), io.StringIO()
        from test_agent_playtest_cli import ap
        with redirect_stdout(out), redirect_stderr(err):
            rc = ap.main(["--session", self.dir, "start", "--remote-zip", "C:/z.zip", "--game-name", "G"],
                         make=SlowLaunch, record_mod=self.rec, now=self.now)
        self.assertEqual(rc, 2)  # start reported an error, but the game came up a few seconds later
        r = self.shot("press", "space", "--label", "new-run")
        self.cli("mark", "restart", "--evidence", r)
        grc, gout, _ = self.cli("gate")
        self.assertNotEqual(grc, 0, "restart by a (slow) process relaunch passed the gate:\n" + gout)


if __name__ == "__main__":
    unittest.main()

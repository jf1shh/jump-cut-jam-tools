"""Finding 2: 'restart' can be satisfied by relaunching the process (`start` again), not by an in-game restart.
Game whose lose screen has no way out (the exact mock-10 class of bug: lose-state camera loop, no restart):
tester loses, cannot restart in game, runs `start` again (doc-endorsed for crashes), plays a little, marks
restart with a fresh-run frame -> GATE PASS. The gate should not accept restart evidence when a relaunch
sits between the lose evidence and the restart evidence."""
import unittest

from test_agent_playtest_cli import Base


class T(Base):
    def test_relaunch_is_not_an_in_game_restart(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        self.cli("mark", "win", "--evidence", w)
        l = self.shot("look", "--label", "lose-camera-loops")
        self.cli("mark", "lose", "--evidence", l)
        # no on-screen restart exists; the tester relaunches the process instead
        self.start()
        r = self.shot("press", "space", "--label", "new-run")
        self.cli("mark", "restart", "--evidence", r)
        rc, out, _ = self.cli("gate")
        self.assertNotEqual(rc, 0, "gate passed 'restart' that was a process relaunch:\n" + out)


if __name__ == "__main__":
    unittest.main()

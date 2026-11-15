"""Finding 1: a single press whose after-frame shows the game NOT in front (game crashed or quit on that key,
e.g. `esc` during edge poking) makes the gate fail forever. The doc says 'redo that step' and 'if the game
crashes, run start again: history is kept'. Neither clears it; only --fresh does, which throws away the
already-earned win/lose/restart evidence. Also, input steps are asserted foreground by the PS1 BEFORE they
are sent, so a False here never means 'keys went elsewhere'."""
import unittest

from test_agent_playtest_cli import Base, FakeBackend


class T(Base):
    def test_crash_during_edge_poking_is_recoverable(self):
        self.start()
        for _ in range(6):
            self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        self.cli("mark", "win", "--evidence", w)
        l = self.shot("look", "--label", "lose")
        self.cli("mark", "lose", "--evidence", l)
        r = self.shot("look", "--label", "restart")
        self.cli("mark", "restart", "--evidence", r)
        self.assertEqual(self.cli("gate")[0], 0, "precondition: a full trail passes")
        # protocol step 5: press esc. The game quits / crashes, so the after-frame shows the desktop.
        FakeBackend.front = False
        self.shot("press", "esc")
        FakeBackend.front = True
        # doc: 'If the game crashes, run start again with the same zip: the history is kept'
        self.start()
        # doc: 'redo that step'
        for _ in range(3):
            self.shot("press", "w")
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 0, "gate should still pass after a documented crash+relaunch+redo:\n" + out)


if __name__ == "__main__":
    unittest.main()

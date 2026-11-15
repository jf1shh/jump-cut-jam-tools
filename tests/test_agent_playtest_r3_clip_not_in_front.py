"""Round 3 finding 2: frames must have game_in_front=True, but clips only need the game process alive. On the
first clip of a session, start_obs launches OBS (no minimize flag) AFTER the game is already running, so the
OBS window comes up in front of the game; the Display Capture source then records OBS's own window. The process
is alive and the video is not black/flat, so the clip is accepted. Same for any other window in front (crash
reporter, Windows dialog). Here: game alive but not in front for the whole clip -> still accepted as lose."""
import unittest

from test_agent_playtest_cli import Base, FakeBackend


class T(Base):
    def test_clip_with_game_behind_another_window(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        self.cli("mark", "win", "--evidence", w)
        FakeBackend.front = False      # OBS (just launched by clip) or a dialog is the front window
        rc, out, _ = self.cli("clip", "10")
        FakeBackend.front = True
        clip = out.strip()
        self.cli("mark", "lose", "--evidence", clip)
        r = self.shot("press", "space", "--label", "restart")
        self.cli("mark", "restart", "--evidence", r)
        grc, gout, _ = self.cli("gate")
        self.assertNotEqual(grc, 0, "a clip taken with the game not in front was accepted as lose evidence:\n" + gout)


if __name__ == "__main__":
    unittest.main()

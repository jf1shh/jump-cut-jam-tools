"""Finding 3: frames need game_in_front, but clips are accepted with only the black/flat video check. A clip
of the Windows desktop after the game died (crashed on the lose screen) is not black or flat, so it is
accepted as lose evidence. cmd_clip never checks that the game is alive or in front."""
import unittest

from test_agent_playtest_cli import Base, FakeBackend


class T(Base):
    def test_clip_of_dead_game_is_not_evidence(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        self.cli("mark", "win", "--evidence", w)
        # the game crashes on the lose screen: process gone, desktop visible
        FakeBackend.alive = lambda self: False
        try:
            rc, out, _ = self.cli("state")
            self.assertIn("game_running: False", out)
            rc, out, _ = self.cli("clip", "10")   # OBS records the desktop: video check passes
            clip = out.strip()
        finally:
            FakeBackend.alive = lambda self: True
        self.cli("mark", "lose", "--evidence", clip)
        self.start()
        r = self.shot("press", "space", "--label", "restart")
        self.cli("mark", "restart", "--evidence", r)
        rc, out, _ = self.cli("gate")
        self.assertNotEqual(rc, 0, "a clip recorded while the game was dead was accepted as lose evidence:\n" + out)


if __name__ == "__main__":
    unittest.main()

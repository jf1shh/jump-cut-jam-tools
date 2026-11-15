"""Round 3 finding 1: cmd_clip checks alive() only BEFORE rec.record(). legion_record.one_take (the helper the
clip reuses) checks game_alive before AND after record and rejects 'died during the recording'. If the game
crashes a second into a 10 s clip (e.g. crashes on the win screen), the clip is mostly desktop (not black or
flat), game_alive=True is journaled, cmd_clip returns 0, and the clip is accepted as win evidence."""
import unittest

from test_agent_playtest_cli import Base, FakeBackend, FakeRecord


class DyingRecord(FakeRecord):
    def record(self, host, seconds, replay):
        FakeBackend.alive = lambda self: False   # the game crashes during the recording
        return super().record(host, seconds, replay)


class T(Base):
    def test_game_dies_during_clip(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")
        rec = DyingRecord()
        try:
            rc, out, err = self.cli("clip", "10", rec=rec)
        finally:
            FakeBackend.alive = lambda self: True
        clip = out.strip()
        self.cli("mark", "win", "--evidence", clip)
        self.start()  # relaunch after the crash (doc-endorsed)
        self.shot("press", "w")
        l = self.shot("look", "--label", "lose")
        self.cli("mark", "lose", "--evidence", l)
        r = self.shot("press", "space", "--label", "restart")
        self.cli("mark", "restart", "--evidence", r)
        grc, gout, _ = self.cli("gate")
        self.assertTrue(rc != 0 or grc != 0,
                        "a clip during which the game died was accepted (clip rc=%d) and the gate passed:\n%s" % (rc, gout))


if __name__ == "__main__":
    unittest.main()

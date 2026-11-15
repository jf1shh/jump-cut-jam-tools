"""Fake-clock tests for scripts/jam_clock.py. No real time, no real nudges."""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import jam_clock as jc  # noqa: E402

DL = datetime(2026, 11, 16, 1, 59, tzinfo=timezone.utc)


def at(minutes_left):
    return DL - timedelta(minutes=minutes_left)


def setup(tmp_path):
    jc.write_deadline(tmp_path, DL)
    return tmp_path


class Rec:
    def __init__(self, rc=0, boom=False):
        self.calls, self.rc, self.boom = [], rc, boom

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw["input"]))
        if self.boom:
            raise OSError("nope")
        return subprocess.CompletedProcess(cmd, self.rc)


def test_default_deadline_is_2059_et():
    et = timezone(timedelta(hours=-5))
    assert jc.parse_deadline(jc.DEFAULT_DEADLINE) == datetime(2026, 11, 15, 20, 59, tzinfo=et)


def test_naive_deadline_rejected():
    try:
        jc.parse_deadline("2026-11-15T20:59:00")
    except ValueError:
        return
    raise AssertionError("naive time accepted")


def test_phases():
    assert jc.phase(timedelta(minutes=61)) == "WORK"
    assert jc.phase(timedelta(minutes=60)) == "PACKAGE"
    assert jc.phase(timedelta(minutes=16)) == "PACKAGE"
    assert jc.phase(timedelta(minutes=15)) == "FINAL"
    assert jc.phase(timedelta(0)) == "EXPIRED"


def test_no_markers_while_working(tmp_path):
    s = setup(tmp_path)
    assert jc.tick(s, at(120)) == "WORK"
    assert not (s / "FORCE_PACKAGE").exists() and not (s / "FINAL").exists()
    assert jc.check_code(s, at(120)) == 0


def test_t60_writes_force_package_only(tmp_path):
    s = setup(tmp_path)
    assert jc.tick(s, at(60)) == "PACKAGE"
    assert (s / "FORCE_PACKAGE").exists() and not (s / "FINAL").exists()
    assert "STOP feature work" in (s / "FORCE_PACKAGE").read_text()
    assert jc.check_code(s, at(60)) == jc.EXIT_PACKAGE


def test_t15_writes_final(tmp_path):
    s = setup(tmp_path)
    jc.tick(s, at(30))
    assert jc.tick(s, at(15)) == "FINAL"
    assert (s / "FINAL").exists()
    assert "itch page" in (s / "FINAL").read_text()
    assert jc.check_code(s, at(15)) == jc.EXIT_FINAL


def test_late_start_in_final_skips_package_order(tmp_path):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(5), "x", rec)
    assert not (s / "FORCE_PACKAGE").exists() and (s / "FINAL").exists()
    assert all("package + upload" not in m.lower() for _, m in rec.calls)
    s2, rec2 = tmp_path / "late", Rec()
    jc.write_deadline(s2, DL)
    jc.tick(s2, at(-10), "x", rec2)
    assert all("package + upload" not in m.lower() for _, m in rec2.calls)


def test_same_deadline_restart_keeps_markers_and_no_renudge(tmp_path):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(50), "x", rec)
    jc.write_deadline(s, DL)
    jc.tick(s, at(49), "x", rec)
    assert (s / "FORCE_PACKAGE").exists() and len(rec.calls) == 1


def test_start_without_deadline_keeps_existing(tmp_path):
    d = ["--state-dir", str(tmp_path)]
    jc.main(d + ["start", "--no-loop", "--deadline", "2030-01-01T00:00:00+00:00"])
    jc.main(d + ["start", "--no-loop"])
    assert jc.read_deadline(tmp_path) == datetime(2030, 1, 1, tzinfo=timezone.utc)


def test_start_without_deadline_or_state_uses_default(tmp_path):
    assert jc.main(["--state-dir", str(tmp_path), "start", "--no-loop"]) == 0
    assert jc.read_deadline(tmp_path) == jc.parse_deadline(jc.DEFAULT_DEADLINE)


def test_start_refuses_just_passed_deadline(tmp_path, capsys):
    d = ["--state-dir", str(tmp_path)]
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    jc.main(d + ["start", "--no-loop", "--deadline", past.isoformat()])
    assert jc.main(d + ["start", "--no-loop"]) == 2
    assert "pass --deadline" in capsys.readouterr().err
    assert jc.read_deadline(tmp_path) == past.replace(microsecond=past.microsecond)
    assert jc.main(d + ["check"]) == jc.EXIT_EXPIRED
    # explicit --deadline is the only way to start a new run
    assert jc.main(d + ["start", "--no-loop", "--deadline", "2099-01-01T00:00:00+00:00"]) == 0


def test_refused_start_still_writes_expired_marker_and_nudges_once(tmp_path, monkeypatch):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(10))  # daemon died after writing FINAL
    assert (s / "FINAL").exists() and not (s / "EXPIRED").exists()
    monkeypatch.setattr(jc, "_now", lambda: DL + timedelta(minutes=5))
    monkeypatch.setattr(jc.subprocess, "run", rec)
    d = ["--state-dir", str(s), "start", "--no-loop", "--nudge-cmd", "x"]
    assert jc.main(d) == 2
    assert (s / "EXPIRED").exists()
    assert jc.main(d) == 2
    assert len(rec.calls) == 1 and "PASSED" in rec.calls[0][1]


def test_start_replaces_long_dead_deadline(tmp_path, monkeypatch, capsys):
    d = ["--state-dir", str(tmp_path)]
    monkeypatch.setattr(jc, "_now", lambda: datetime(2026, 11, 9, 14, 0, tzinfo=timezone.utc))
    jc.main(d + ["start", "--no-loop", "--deadline", "2026-11-09T07:00:00-08:00"])
    monkeypatch.setattr(jc, "_now", lambda: datetime(2026, 11, 11, 20, 0, tzinfo=timezone.utc))
    assert jc.main(d + ["start", "--no-loop"]) == 0
    assert jc.read_deadline(tmp_path) == jc.parse_deadline(jc.DEFAULT_DEADLINE)
    assert "replacing" in capsys.readouterr().err
    assert jc.main(d + ["check"]) == 0
    assert not (tmp_path / "EXPIRED").exists()


def test_loop_survives_transient_bad_deadline_file(tmp_path):
    s = setup(tmp_path)
    good = (s / "deadline.json").read_text()
    times = iter([at(m) for m in (120, 90, 59, 10, -1)])
    n = {"i": 0}

    def sleep(_):
        n["i"] += 1
        if n["i"] == 1:
            (s / "deadline.json").write_text("")
        elif n["i"] == 2:
            (s / "deadline.json").write_text(good)

    jc.loop(s, None, 1, now_fn=lambda: next(times), sleep=sleep)
    assert (s / "FORCE_PACKAGE").exists()


def test_loop_waits_if_deadline_never_good_at_first(tmp_path):
    s = tmp_path
    (s / "deadline.json").write_text("{")
    times = iter([at(-1)])
    calls = {"n": 0}

    def sleep(_):
        calls["n"] += 1
        jc.write_deadline(s, DL)

    jc.loop(s, None, 1, now_fn=lambda: next(times), sleep=sleep)
    assert calls["n"] == 1


def test_expired_sends_expired_message_not_final(tmp_path):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(-10), "x", rec)
    assert len(rec.calls) == 1
    assert "PASSED" in rec.calls[0][1] and "FINAL" not in rec.calls[0][1]
    assert (s / "EXPIRED").exists() and not (s / "FINAL").exists()


def test_deadline_file_replaced_atomically(tmp_path, monkeypatch):
    s = setup(tmp_path)
    seen = []
    real = jc.os.replace

    def spy(a, b):
        seen.append(Path(a).read_text())  # tmp is fully written before the swap
        real(a, b)

    monkeypatch.setattr(jc.os, "replace", spy)
    jc.write_deadline(s, DL + timedelta(days=1))
    assert seen and '"deadline"' in seen[0]
    assert (s / "deadline.json").read_text().strip().startswith("{")


def test_markers_cleared_after_new_deadline_in_place(tmp_path, monkeypatch):
    s = setup(tmp_path)
    jc.tick(s, at(50))
    states = []
    real = Path.unlink

    def spy(self, *a, **k):
        states.append(jc.read_deadline(s))
        return real(self, *a, **k)

    monkeypatch.setattr(Path, "unlink", spy)
    new = DL + timedelta(days=1)
    jc.write_deadline(s, new)
    assert states and all(x == new for x in states)


def test_check_fails_closed(tmp_path, capsys):
    assert jc.main(["--state-dir", str(tmp_path / "none"), "check"]) == jc.EXIT_EXPIRED
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "deadline.json").write_text('{"dl": "x"}')
    assert jc.main(["--state-dir", str(bad), "check"]) == jc.EXIT_EXPIRED
    (bad / "deadline.json").write_text("not json")
    assert jc.main(["--state-dir", str(bad), "check"]) == jc.EXIT_EXPIRED


def test_marker_written_before_nudge(tmp_path):
    s = setup(tmp_path)
    seen = []

    def runner(cmd, **kw):
        seen.append((s / "FORCE_PACKAGE").exists())
        return subprocess.CompletedProcess(cmd, 0)

    jc.tick(s, at(50), "x", runner)
    assert seen == [True]


def test_expired(tmp_path):
    s = setup(tmp_path)
    assert jc.tick(s, at(-3)) == "EXPIRED"
    assert jc.check_code(s, at(-3)) == jc.EXIT_EXPIRED
    assert "-00h 03m" in jc.status_line(s, at(-3))


def test_nudge_once_per_marker(tmp_path):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(59), "send-it", rec)
    jc.tick(s, at(58), "send-it", rec)
    assert len(rec.calls) == 1 and "T-59" in rec.calls[0][1]
    jc.tick(s, at(14), "send-it", rec)
    jc.tick(s, at(13), "send-it", rec)
    assert len(rec.calls) == 2 and "FINAL" in rec.calls[1][1]
    assert '"nudged": true' in (s / "FINAL").read_text()


def test_nudge_failure_still_writes_marker(tmp_path):
    for rec in (Rec(rc=1), Rec(boom=True)):
        s = tmp_path / str(id(rec))
        jc.write_deadline(s, DL)
        jc.tick(s, at(50), "x", rec)
        assert (s / "FORCE_PACKAGE").exists()
        assert '"nudged": false' in (s / "FORCE_PACKAGE").read_text()


def test_no_nudge_cmd_means_file_only(tmp_path):
    s, rec = setup(tmp_path), Rec()
    jc.tick(s, at(50), None, rec)
    assert rec.calls == [] and (s / "FORCE_PACKAGE").exists()


def test_new_deadline_clears_old_markers(tmp_path):
    s = setup(tmp_path)
    jc.tick(s, at(10))
    jc.write_deadline(s, DL + timedelta(days=1))
    assert not (s / "FORCE_PACKAGE").exists() and not (s / "FINAL").exists()


def test_status_text(tmp_path):
    s = setup(tmp_path)
    line = jc.status_line(s, DL - timedelta(days=1, hours=2, minutes=3, seconds=4))
    assert line.startswith("WORK  time left 1d 02h 03m 04s")


def test_missing_deadline_is_clean_error(tmp_path, capsys):
    assert jc.main(["--state-dir", str(tmp_path / "none"), "status"]) == 2
    assert "no deadline" in capsys.readouterr().err


def test_loop_stops_at_deadline(tmp_path):
    s = setup(tmp_path)
    times = iter([at(61), at(59), at(10), at(-1)])
    sleeps = []
    jc.loop(s, None, 1, now_fn=lambda: next(times), sleep=sleeps.append)
    assert len(sleeps) == 3
    assert (s / "FORCE_PACKAGE").exists() and (s / "FINAL").exists()


def test_cli_roundtrip(tmp_path, capsys):
    d = ["--state-dir", str(tmp_path)]
    assert jc.main(d + ["start", "--no-loop", "--deadline", "2099-01-01T00:00:00+00:00"]) == 0
    assert jc.main(d + ["check"]) == 0
    assert jc.main(d + ["status"]) == 0
    assert "WORK" in capsys.readouterr().out

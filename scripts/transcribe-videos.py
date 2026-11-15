#!/usr/bin/env python3
"""Transcribe the must-watch videos in _config/reference/knowledge-base.md into _config/reference/research/transcripts/.

Captions-first: tries yt-dlp's auto/manual subtitles before falling back to local Whisper
(faster-whisper, CPU) for videos with no captions. See _config/reference/research/transcripts/README.md.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "_config" / "reference" / "research" / "transcripts"
VIDEO_URL_RE = re.compile(r"https://(?:www\.)?youtube\.com/(?:watch\?v=|live/)([\w-]{11})")
WHISPER_VENV_PYTHON = Path.home() / ".local/share/megajam-transcribe/venv/bin/python"


def find_video_ids(knowledge_base: Path) -> list[str]:
    text = knowledge_base.read_text()
    seen = []
    for match in VIDEO_URL_RE.finditer(text):
        vid = match.group(1)
        if vid not in seen:
            seen.append(vid)
    return seen


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def fetch_captions(video_id: str, work_dir: Path) -> Path | None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    result = run([
        "yt-dlp", "--write-auto-sub", "--write-sub", "--sub-lang", "en.*,en",
        "--skip-download", "--convert-subs", "srt",
        "-o", str(work_dir / "%(id)s.%(ext)s"), url,
    ])
    if result.returncode != 0:
        return None
    srt_files = sorted(work_dir.glob(f"{video_id}*.srt"))
    return srt_files[0] if srt_files else None


def srt_to_text(srt_path: Path) -> str:
    lines = []
    for line in srt_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return "\n".join(lines)


def fetch_audio(video_id: str, work_dir: Path) -> Path | None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    result = run([
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", str(work_dir / "%(id)s.%(ext)s"), url,
    ])
    if result.returncode != 0:
        return None
    audio_files = sorted(work_dir.glob(f"{video_id}.mp3"))
    return audio_files[0] if audio_files else None


def whisper_transcribe(audio_path: Path) -> str:
    if not WHISPER_VENV_PYTHON.exists():
        raise RuntimeError(
            f"Whisper venv not found at {WHISPER_VENV_PYTHON}. "
            "Set it up: python3.12 -m venv ~/.local/share/megajam-transcribe/venv "
            "&& .../venv/bin/pip install faster-whisper"
        )
    script = (
        "from faster_whisper import WhisperModel\n"
        "import sys, json\n"
        "model = WhisperModel('base', device='cpu', compute_type='int8')\n"
        "segments, _ = model.transcribe(sys.argv[1], vad_filter=True)\n"
        "print('\\n'.join(s.text.strip() for s in segments))\n"
    )
    result = run([str(WHISPER_VENV_PYTHON), "-c", script, str(audio_path)])
    if result.returncode != 0:
        raise RuntimeError(f"faster-whisper failed: {result.stderr[-2000:]}")
    return result.stdout.strip()


def get_title(video_id: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    result = run(["yt-dlp", "--skip-download", "--print", "%(title)s", url])
    return result.stdout.strip() if result.returncode == 0 else video_id


def transcribe_one(video_id: str, work_dir: Path, force: bool = False) -> None:
    out_path = OUT_DIR / f"{video_id}.md"
    if out_path.exists() and not force:
        print(f"[skip] {video_id} — already transcribed ({out_path})")
        return

    title = get_title(video_id)
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[{video_id}] {title}")

    srt_path = fetch_captions(video_id, work_dir)
    if srt_path is not None:
        source = "yt-dlp captions"
        text = srt_to_text(srt_path)
    else:
        print(f"  no captions — falling back to local Whisper (base, CPU)")
        audio_path = fetch_audio(video_id, work_dir)
        if audio_path is None:
            print(f"  [fail] {video_id} — yt-dlp could not fetch captions or audio")
            return
        source = "faster-whisper base (CPU)"
        text = whisper_transcribe(audio_path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"# {title}\n\n- URL: {url}\n- Source: {source}\n\n---\n\n{text}\n"
    )
    print(f"  [ok] -> {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path,
        default=REPO_ROOT / "_config" / "reference" / "knowledge-base.md",
        help="Markdown file to scan for youtube.com URLs (default: _config/reference/knowledge-base.md)",
    )
    parser.add_argument("--video-id", action="append", dest="video_ids",
                         help="Transcribe only this video ID (repeatable); skips --source scan")
    parser.add_argument("--force", action="store_true", help="Re-transcribe even if output exists")
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/megajam-transcribe-work"))
    args = parser.parse_args()

    args.work_dir.mkdir(parents=True, exist_ok=True)

    video_ids = args.video_ids or find_video_ids(args.source)
    if not video_ids:
        print(f"No youtube.com video URLs found in {args.source}", file=sys.stderr)
        return 1

    print(f"Found {len(video_ids)} video(s) to process")
    for vid in video_ids:
        transcribe_one(vid, args.work_dir, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

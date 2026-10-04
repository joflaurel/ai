---
name: video-pipeline
description: Run the free local editing pipeline - remove silences, make a Premiere EDL, Whisper captions (SRT) and transcript, and a 9:16 vertical version. Use when asked to cut silences, caption, transcribe, or make vertical versions of videos.
---

# Video pipeline

1. Make sure the videos are in `video-pipeline/input/`. If the user names files elsewhere, copy them there (copy, never move originals).
2. If the user mentions a client, read `clients/<client>.md` and apply its "Pipeline settings" by editing the SETTINGS block at the top of `video-pipeline/pipeline.py` (tell the user what you changed).
3. Run `py video-pipeline/pipeline.py` (on macOS/Linux: `python3`). The first caption run downloads the Whisper model; that's normal.
4. Report per video: the length before and after the silence cut, and the files in `video-pipeline/output/<name>/`.
5. If cuts feel too tight, raise PADDING or MIN_SILENCE; if pauses are left in, raise SILENCE_DB toward -30.

If ffmpeg or Python is missing, tell the user to run `setup/bootstrap.ps1` and open a new terminal.

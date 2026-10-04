"""
Free video editing pipeline
---------------------------
Drop videos into the "input" folder, run this script (or double-click run.bat),
and for every video you get a folder in "output" with:

  <name>_cut.mp4        silences removed
  <name>_cut.edl        Premiere timeline with the same cuts (File > Import, pick the .edl)
  <name>.srt            captions (short lines, good for Reels/TikTok)
  <name>.txt            full transcript
  <name>_9x16.mp4       vertical 1080x1920 version (captions burned in if BURN_CAPTIONS = True)

Needs: Python 3, ffmpeg on PATH, and `pip install faster-whisper` for captions.
Everything runs on your own PC. No accounts, no credits.
"""

import json, os, re, shutil, subprocess, sys
from pathlib import Path

# ===================== SETTINGS (change these) =====================
SILENCE_DB       = -35     # quieter than this counts as silence (try -30 for noisy rooms, -40 for quiet ones)
MIN_SILENCE      = 0.5     # only cut pauses longer than this many seconds
PADDING          = 0.12    # seconds of breathing room kept before/after speech
REMOVE_SILENCE   = True
MAKE_CAPTIONS    = True
WHISPER_MODEL    = "small" # tiny / base / small / medium / large-v3 (bigger = slower but more accurate)
LANGUAGE         = None    # None = auto-detect, or "en", "tl" (Tagalog), etc.
WORDS_PER_LINE   = 5       # caption chunk size for short-form style
MAKE_VERTICAL    = True
BURN_CAPTIONS    = True    # burn captions into the 9:16 version
CAPTION_STYLE    = "Fontname=Arial,Fontsize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=70"
VIDEO_EXTS       = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
# ===================================================================

HERE = Path(__file__).resolve().parent
IN_DIR, OUT_DIR = HERE / "input", HERE / "output"


def need(tool):
    if not shutil.which(tool):
        sys.exit(f"Can't find {tool}. Run setup\\bootstrap.ps1 first, then open a NEW terminal window.")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    info = json.loads(r.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    if not 1 < fps < 241:
        fps = 30.0
    return {"duration": float(info["format"]["duration"]), "w": int(v["width"]), "h": int(v["height"]),
            "fps": fps, "has_audio": has_audio}


# ---------------- silence removal ----------------
def find_speech(path, duration):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
                        "-af", f"silencedetect=noise={SILENCE_DB}dB:d={MIN_SILENCE}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    if len(ends) < len(starts):
        ends.append(duration)
    keep, cur = [], 0.0
    for s, e in zip(starts, ends):
        s, e = max(0.0, s), min(duration, e)
        if s > cur:
            keep.append([cur, s])
        cur = e
    if cur < duration:
        keep.append([cur, duration])
    # pad and merge
    padded = []
    for a, b in keep:
        a, b = max(0.0, a - PADDING), min(duration, b + PADDING)
        if padded and a <= padded[-1][1]:
            padded[-1][1] = max(padded[-1][1], b)
        else:
            padded.append([a, b])
    return [(a, b) for a, b in padded if b - a >= 0.2]


def render_cut(src, dst, segs, has_audio, workdir):
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segs)
    script = workdir / "_cut_filter.txt"
    graph = f"[0:v]select='{expr}',setpts=N/FRAME_RATE/TB[v]"
    if has_audio:
        graph += f";[0:a]aselect='{expr}',asetpts=N/SR/TB[a]"
    script.write_text(graph, encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-filter_complex_script", str(script), "-map", "[v]"]
    if has_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(dst)]
    run(cmd)
    script.unlink(missing_ok=True)


def tc(seconds, fps):
    f = int(round(seconds * fps))
    r = int(round(fps))
    return f"{f // (r * 3600):02d}:{f // (r * 60) % 60:02d}:{f // r % 60:02d}:{f % r:02d}"


def write_edl(path, src_name, segs, fps):
    lines = ["TITLE: " + Path(src_name).stem + " cut", "FCM: NON-DROP FRAME", ""]
    rec = 0.0
    for i, (a, b) in enumerate(segs, 1):
        dur = b - a
        lines.append(f"{i:03d}  AX       AA/V  C        {tc(a, fps)} {tc(b, fps)} {tc(rec, fps)} {tc(rec + dur, fps)}")
        lines.append(f"* FROM CLIP NAME: {src_name}")
        lines.append("")
        rec += dur
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------- captions ----------------
def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def transcribe(media, srt_path, txt_path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("   (skipping captions: run  py -m pip install faster-whisper)")
        return False
    print(f"   transcribing with Whisper '{WHISPER_MODEL}' (first run downloads the model)...")
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(media), language=LANGUAGE, word_timestamps=True, vad_filter=True)
    words, full = [], []
    for seg in segments:
        full.append(seg.text.strip())
        for w in seg.words or []:
            words.append((w.start, w.end, w.word.strip()))
    txt_path.write_text("\n".join(full), encoding="utf-8")
    out, n = [], 1
    for i in range(0, len(words), WORDS_PER_LINE):
        chunk = words[i:i + WORDS_PER_LINE]
        text = " ".join(w for _, _, w in chunk).strip()
        if text:
            out.append(f"{n}\n{srt_time(chunk[0][0])} --> {srt_time(chunk[-1][1])}\n{text}\n")
            n += 1
    srt_path.write_text("\n".join(out), encoding="utf-8")
    return True


# ---------------- vertical ----------------
def make_vertical(src, dst, info, srt_name, workdir):
    if info["w"] / info["h"] > 9 / 16:   # wider than 9:16 -> fill height, crop the sides (center)
        vf = "scale=-2:1920,crop=1080:1920"
    else:                               # already tall -> fit width, pad if needed
        vf = "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    vf += ",setsar=1"
    if srt_name:
        vf += f",subtitles={srt_name}:force_style='{CAPTION_STYLE}'"
    # run inside the output folder so the subtitles path has no drive letters to escape on Windows
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src.name, "-vf", vf,
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "copy", "-movflags", "+faststart", dst.name], cwd=workdir)


def process(src):
    name = src.stem
    out = OUT_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    info = probe(src)
    print(f"\n>> {src.name}  ({info['duration']:.1f}s, {info['w']}x{info['h']}, {info['fps']:.2f}fps)")

    work = src
    if REMOVE_SILENCE and info["has_audio"]:
        segs = find_speech(src, info["duration"])
        kept = sum(b - a for a, b in segs)
        cut = out / f"{name}_cut.mp4"
        render_cut(src, cut, segs, info["has_audio"], out)
        write_edl(out / f"{name}_cut.edl", src.name, segs, info["fps"])
        print(f"   silences removed: {info['duration']:.1f}s -> {kept:.1f}s ({len(segs)} pieces)")
        work = cut
    elif not info["has_audio"]:
        print("   no audio track, skipping silence removal and captions")

    srt = out / f"{name}.srt"
    have_srt = False
    if MAKE_CAPTIONS and info["has_audio"]:
        have_srt = transcribe(work, srt, out / f"{name}.txt")

    if MAKE_VERTICAL:
        # vertical is made from the file inside the output folder
        temp_copy = work.parent != out
        local = out / work.name
        if temp_copy:
            shutil.copy2(work, local)
        make_vertical(local, out / f"{name}_9x16.mp4", probe(local),
                      srt.name if (BURN_CAPTIONS and have_srt) else None, out)
        if temp_copy:
            local.unlink(missing_ok=True)
        print("   vertical 9:16 version done")
    print(f"   -> {out}")


def main():
    need("ffmpeg"); need("ffprobe")
    IN_DIR.mkdir(exist_ok=True); OUT_DIR.mkdir(exist_ok=True)
    videos = sorted(p for p in IN_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS)
    if not videos:
        print(f"No videos found. Put your clips in:\n  {IN_DIR}")
        return
    for v in videos:
        if (OUT_DIR / v.stem / f"{v.stem}_9x16.mp4").exists() or (OUT_DIR / v.stem / f"{v.stem}_cut.mp4").exists():
            print(f"\n>> {v.name}: already done, skipping (delete its output folder to redo)")
            continue
        try:
            process(v)
        except Exception as e:
            print(f"   !! failed: {e}")
    print("\nAll done.")


if __name__ == "__main__":
    main()

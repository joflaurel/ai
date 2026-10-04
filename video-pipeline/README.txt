FREE VIDEO PIPELINE
===================

FIRST TIME ONLY
Run setup\bootstrap.ps1 (see the main README). It installs Python, ffmpeg and Whisper - all free.

EVERY TIME
1. Put your raw videos in the "input" folder (run.bat creates it the first time).
2. Double-click run.bat (or in Claude Code: "run the video pipeline").
3. Grab your files from the "output" folder - one folder per video:

   name_cut.mp4    silences removed
   name_cut.edl    Premiere timeline with the cuts (Premiere: File > Import > pick the .edl,
                   then link it to your original clip if it asks)
   name.srt        captions, 5 words per line (drag into Premiere or CapCut)
   name.txt        full transcript
   name_9x16.mp4   vertical 1080x1920 version with captions burned in

SETTINGS
Open pipeline.py in Notepad. The SETTINGS block at the top lets you change:
- how quiet counts as silence (SILENCE_DB) and how long a pause must be to cut (MIN_SILENCE)
- Whisper model size (tiny = fastest, medium = most accurate)
- language (None = auto, "en" = English, "tl" = Tagalog)
- words per caption line, caption font/size, burned captions on/off

TIPS
- The first caption run downloads the Whisper model (a few hundred MB), so it takes longer.
- Already-processed videos are skipped. Delete a video's output folder to redo it.

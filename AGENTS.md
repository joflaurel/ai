In every chat, start with "Hey, boss."
Explore this repository for video editing skills: https://github.com/awesome-genmedia/skills

## About me
I'm Jofrey, a video editor (short-form and long-form) based in Cebu, Philippines. I work mainly in Premiere Pro and CapCut on Windows.

## This workspace
This repo is my portable toolkit. It works the same on any machine.
- `video-pipeline/` - free local pipeline: silence removal, Premiere EDL, Whisper captions (SRT), 9:16 versions. Run `py video-pipeline/pipeline.py` (videos go in `video-pipeline/input/`).
- `clients/` - per-client editing rules. Read the matching file before working on a client's video.
- `setup/bootstrap.ps1` - sets up a new Windows PC.

## Rules
- Prefer free, local tools (ffmpeg, Whisper, Python) over paid APIs unless I ask.
- Never commit video, audio, or client footage. `.gitignore` blocks media; keep it that way.
- This repo is public: no client names, contacts, rates or private details in committed files.
- When you change a script, test it on a short sample before telling me it works.

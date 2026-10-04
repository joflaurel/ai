# Jofrey's AI Video Editing Workspace

My portable toolkit for video editing with Claude Code. Same setup on every machine.

## Set up a new Windows PC (one time)

Open **PowerShell** and run these two commands:

```powershell
irm https://claude.ai/install.ps1 | iex
irm https://raw.githubusercontent.com/joflaurel/ai/main/setup/bootstrap.ps1 | iex
```

The second command installs Git, Python, ffmpeg and Whisper, fixes the PATH for Claude Code,
and downloads this repo to `C:\Users\<you>\ai`. Then close PowerShell, open a new window, and run:

```powershell
cd ~\ai
claude
```

No install allowed (school, office, internet cafe)? Use https://claude.ai/code in the browser and pick this repo.

## What's inside

| Folder | What it does |
|---|---|
| `video-pipeline/` | Drop videos in `input/` -> silence-cut video, Premiere EDL, SRT captions, transcript, 9:16 version |
| `clients/` | Editing rules per client (template inside; keep private details out of this public repo) |
| `.claude/skills/` | Skills Claude Code loads automatically in this folder |
| `setup/` | `bootstrap.ps1` for new machines |

## Quick commands

```powershell
py video-pipeline\pipeline.py      # process everything in video-pipeline\input
```

Or just tell Claude Code what you want, e.g. *"caption and cut the silences in the clips in input"*.

## Where things live

- **This repo** - scripts, instructions, skills (small text files)
- **Google Drive** - footage, exports, Premiere/CapCut projects (too big and private for GitHub)
- **Claude account** - chats, memory and artifacts, available after you log in anywhere

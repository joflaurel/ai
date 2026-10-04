# Jofrey's workspace bootstrap for a new Windows PC.
# Run in PowerShell:
#   irm https://raw.githubusercontent.com/joflaurel/ai/main/setup/bootstrap.ps1 | iex
# Safe to run again: anything already installed is skipped, and the repo is updated instead of re-downloaded.

$ErrorActionPreference = "Continue"
$RepoUrl = "https://github.com/joflaurel/ai.git"
$Workspace = Join-Path $HOME "ai"

function Say($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Install-App($cmd, $wingetId, $label) {
    if (Have $cmd) { Write-Host "    $label already installed" -ForegroundColor DarkGray; return }
    Say "Installing $label..."
    winget install -e --id $wingetId --accept-source-agreements --accept-package-agreements --silent
    Refresh-Path
}

if (-not (Have "winget")) {
    Write-Host "winget is missing. Install 'App Installer' from the Microsoft Store, then run this again." -ForegroundColor Red
    return
}

# 1. Core tools
Install-App "git"    "Git.Git"              "Git"
Install-App "py"     "Python.Python.3.12"   "Python"
Install-App "ffmpeg" "Gyan.FFmpeg"          "ffmpeg"

# 2. Claude Code (and the PATH fix it needs)
$claudeBin = Join-Path $HOME ".local\bin"
$userPath = [string][Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$claudeBin*") {
    Say "Adding Claude Code's folder to your PATH..."
    [Environment]::SetEnvironmentVariable("Path", ($userPath.TrimEnd(";") + ";" + $claudeBin), "User")
    Refresh-Path
}
if (-not (Have "claude")) {
    Say "Installing Claude Code..."
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    Refresh-Path
} else {
    Write-Host "    Claude Code already installed" -ForegroundColor DarkGray
}

# 3. The workspace repo
if (Test-Path (Join-Path $Workspace ".git")) {
    Say "Updating your workspace in $Workspace..."
    git -C $Workspace pull --ff-only
} elseif (Have "git") {
    Say "Downloading your workspace to $Workspace..."
    git clone $RepoUrl $Workspace
} else {
    Write-Host "Git isn't available yet. Close PowerShell, open a new window and run this again." -ForegroundColor Yellow
}

# 4. Python packages for the pipeline and motion graphics
$py = if (Have "py") { "py" } elseif (Have "python") { "python" } else { $null }
if ($py) {
    Say "Installing Python packages (Whisper captions, image tools)..."
    & $py -m pip install --upgrade --quiet pip
    & $py -m pip install --upgrade --quiet faster-whisper pillow numpy
} else {
    Write-Host "Python isn't available yet. Close PowerShell, open a new window and run this again." -ForegroundColor Yellow
}

# 5. Summary
Say "Check:"
foreach ($c in "git", "py", "ffmpeg", "claude") {
    if (Have $c) { Write-Host "    [ok] $c" -ForegroundColor Green } else { Write-Host "    [  ] $c (open a new PowerShell window and run this again)" -ForegroundColor Yellow }
}
Write-Host "`nAll set. Close this window, open a NEW PowerShell window, then run:" -ForegroundColor Green
Write-Host "    cd ~\ai"
Write-Host "    claude"

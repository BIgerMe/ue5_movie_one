# Push ue5_movie_one to GitHub (run after gh auth login)
$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $proj

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Install GitHub CLI: winget install GitHub.cli"
    exit 1
}

$status = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Run: gh auth login -h github.com -p https -w"
    exit 1
}

if (-not (git remote get-url origin 2>$null)) {
    gh repo create ue5_movie_one --private --source=. --remote=origin --push
} else {
    git push -u origin main
}

Write-Host "Done. Repo: https://github.com/$(gh api user -q .login)/ue5_movie_one"

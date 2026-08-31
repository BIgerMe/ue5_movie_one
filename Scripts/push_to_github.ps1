# Push to existing GitHub repo ue5_movie_one
# Usage:
#   .\Scripts\push_to_github.ps1
#   .\Scripts\push_to_github.ps1 -UserName your_github_username
param(
    [string]$UserName = "",
    [string]$Repo = "ue5_movie_one"
)

$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git not found."
}

Write-Host "Project: $proj"
Write-Host "Commits:"
git log --oneline -3

if (-not $UserName -and (Get-Command gh -ErrorAction SilentlyContinue)) {
    try {
        gh auth status 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $UserName = gh api user -q .login
            Write-Host "GitHub user (gh): $UserName"
        }
    } catch {}
}

if (-not $UserName) {
    $UserName = Read-Host "Enter your GitHub username"
}

$remote = "https://github.com/$UserName/$Repo.git"
Write-Host "Remote: $remote"

$cur = git remote get-url origin 2>$null
if ($cur) {
    git remote set-url origin $remote
} else {
    git remote add origin $remote
}

Write-Host "Pushing main (Git LFS may take several minutes)..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done: https://github.com/$UserName/$Repo"
} else {
    Write-Host @"

Push failed. Try:
  1. gh auth login -h github.com -p https -w
  2. Or use VPN if github.com is blocked
  3. Re-run: .\Scripts\push_to_github.ps1 -UserName $UserName
"@
    exit 1
}

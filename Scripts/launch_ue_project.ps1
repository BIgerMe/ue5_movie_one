# Launch Unreal Editor with the 模型使用 project.
$UeEditor = "G:\app\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Project = "G:\app\UE_5.8\assets\模型使用\模型使用.uproject"

if (-not (Test-Path -LiteralPath $UeEditor)) {
    Write-Error "UnrealEditor not found: $UeEditor"
    exit 1
}
if (-not (Test-Path -LiteralPath $Project)) {
    Write-Error "Project not found: $Project"
    exit 1
}

$existing = Get-Process -Name "UnrealEditor" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Unreal Editor already running (PID $($existing.Id))."
    exit 0
}

Write-Host "Launching: $Project"
Start-Process -FilePath $UeEditor -ArgumentList "`"$Project`""

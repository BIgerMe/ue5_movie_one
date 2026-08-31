# Run UE Python script then relaunch editor. Save this file as UTF-8 with BOM.
param(
    [Parameter(Mandatory = $true)]
    [string]$PythonScript
)

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = "G:\app\UE_5.8"
$UeCmd = Join-Path $Root "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Project = Join-Path $Root "assets\模型使用\模型使用.uproject"
$LaunchScript = Join-Path $Root "assets\模型使用\Scripts\launch_ue_project.ps1"

if (-not (Test-Path -LiteralPath $Project)) {
    Write-Error "Project not found: $Project"
    exit 1
}

$wasRunning = $null -ne (Get-Process -Name "UnrealEditor" -ErrorAction SilentlyContinue)
if ($wasRunning) {
    Write-Host "Closing Unreal Editor..."
    Get-Process -Name "UnrealEditor" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 3
}

Write-Host "Running Python: $PythonScript"
$proc = Start-Process -FilePath $UeCmd -ArgumentList @(
    "`"$Project`"",
    "-ExecutePythonScript=`"$PythonScript`"",
    "-stdout",
    "-unattended",
    "-NoLogTimes"
) -Wait -PassThru -NoNewWindow

if ($proc.ExitCode -ne 0) {
    Write-Error "UnrealEditor-Cmd exit code: $($proc.ExitCode)"
    exit $proc.ExitCode
}

Write-Host "Relaunching Unreal Editor..."
& $LaunchScript

#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Runs ON the Legion Go S (via legion_playtest.py or by hand over SSH with -File, never
  -Command - see the $-escaping gotcha below). Takes a zip already produced by
  package-and-push.ps1, deploys it to a clean test folder, and points a reusable Scheduled
  Task at the correct exe so a launch over SSH lands in the real interactive session
  instead of SSH's own non-interactive session 0.

  Encodes two root causes from mock jam 7's multi-session packaged-build debugging
  (stages/00_prep/references/mock-jam-6-tooling-plan.md's gotchas log, stages/00_prep/output/mock-jam-findings-7.md):
    1. The wrong-exe trap: a packaged zip's root also contains
       Engine\Binaries\Win64\UnrealGame.exe, a leftover unrenamed engine template binary
       that looks launchable but is NOT the game - it silently dies or hangs on startup.
       The real exe is <GameName>.exe at the package root. This script finds and launches
       ONLY that one, and throws loudly (naming the wrong-exe trap) if it's missing.
    2. schtasks.exe /Change on an Interactive-logon task prompts for a "run as password"
       interactively and hangs over non-interactive SSH, even though the task needs none.
       Always recreate via Register-ScheduledTask -Force (PowerShell cmdlet) instead.

.PARAMETER ZipPath
  Path to the zip built by package-and-push.ps1 (TeamName_GameName.zip).

.PARAMETER GameName
  Must match the exe name produced by packaging: <GameName>.exe at the zip root.

.PARAMETER DestDir
  Where to extract for this test run. Defaults to a sibling "agent_test" folder next to the
  zip. Cleared and re-extracted every call, so it always reflects ZipPath exactly - no stale
  binaries from a previous build.

.PARAMETER TaskName
  Windows Scheduled Task name, created/updated (not reused as-is - always re-registered with
  -Force so a changed exe path never requires the broken /Change path above).

.OUTPUTS
  A single-line JSON object on stdout: {"exePath", "workingDir", "logPath", "taskName"}.
  legion_playtest.py parses this; a human running it by hand can just read it.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File legion_remote_launch.ps1 `
      -ZipPath C:\Dev\MockJam7Game\Packaged\SilentBlade_MockJam7.zip -GameName MockJam7Game

  Over SSH with -File (not -Command), quote path arguments with double quotes only - the
  remote shell's own argv splitting doesn't treat single quotes as quoting, so they pass
  through literally into the parameter value instead of being stripped.
#>
param(
    [Parameter(Mandatory)] [string]$ZipPath,
    [Parameter(Mandatory)] [string]$GameName,
    [string]$DestDir,
    [string]$TaskName = "MegaJamLaunchGame"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ZipPath)) {
    throw "Zip not found: $ZipPath"
}

if (-not $DestDir) {
    $DestDir = Join-Path (Split-Path -Parent $ZipPath) "agent_test"
}

if (Test-Path $DestDir) { Remove-Item $DestDir -Recurse -Force }
New-Item -ItemType Directory -Path $DestDir -Force | Out-Null

Push-Location $DestDir
tar -xf $ZipPath
Pop-Location
if ($LASTEXITCODE -ne 0) { throw "tar extraction failed (exit $LASTEXITCODE)" }

$exePath = Join-Path $DestDir "$GameName.exe"
if (-not (Test-Path $exePath)) {
    $wrongExe = Join-Path $DestDir "Engine\Binaries\Win64\UnrealGame.exe"
    $hint = if (Test-Path $wrongExe) {
        " Found $wrongExe instead - that's the unrenamed engine template binary, NOT the " +
        "game (mock jam 7's root cause, see stages/00_prep/output/mock-jam-findings-7.md). Do not launch it."
    } else {
        " Nothing at Engine\Binaries\Win64\UnrealGame.exe either - check -GameName matches " +
        "the TeamName_GameName.zip packaging name."
    }
    throw "Expected exe not found: $exePath.$hint"
}

$action = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $DestDir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
# Handheld on battery: default settings leave the task 'Queued' and stop the game when unplugged (mock 17).
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

$result = [ordered]@{
    exePath    = $exePath
    workingDir = $DestDir
    logPath    = Join-Path $DestDir "$GameName\Saved\Logs\$GameName.log"
    taskName   = $TaskName
}
$result | ConvertTo-Json -Compress

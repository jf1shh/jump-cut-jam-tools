#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Nov 4 packaging gate: cook+stage+archive a Win64 Development build with RunUAT,
  zip it as TeamName_GameName.zip, check it's under 1 GB, and push it with butler.

.PARAMETER EnginePath
  Path to the UE install root (5.9 Preview by default; must match the desktop editor version) (the folder containing Engine\Build\BatchFiles\RunUAT.bat).

.PARAMETER ProjectPath
  Path to the .uproject file.

.PARAMETER TeamName
.PARAMETER GameName
  Used to build the zip name TeamName_GameName.zip (no spaces; collapse to one token each).

.PARAMETER ItchTarget
  butler push target, e.g. "jf1shh/megajam-pretest:win64". Omit to skip the butler push
  (useful for a dry run of just the cook+zip steps).

.PARAMETER NoticeFile
  Third-party notice file (Hunyuan3D-2 requires one on any build distributed outside a hosted
  service — see stages/00_prep/references/license-check-modly-foundrylab.md). Defaults to _config/reference/NOTICE.txt next to
  this script's repo. Pass an empty string to skip on purpose for a non-shipping dry run.

.PARAMETER CheckButler
  Read-only check: print the butler path the lookup finds and its version, then exit.

.EXAMPLE
  ./package-and-push.ps1 -EnginePath C:\UE_5.8 -ProjectPath C:\jam\Throwaway\Throwaway.uproject `
      -TeamName SilentBlade -GameName Throwaway -ItchTarget jf1shh/megajam-pretest:win64
#>
[CmdletBinding(DefaultParameterSetName = 'Package')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Package')] [string]$EnginePath,
    [Parameter(Mandatory, ParameterSetName = 'Package')] [string]$ProjectPath,
    [Parameter(Mandatory, ParameterSetName = 'Package')] [string]$TeamName,
    [Parameter(Mandatory, ParameterSetName = 'Package')] [string]$GameName,
    [Parameter(ParameterSetName = 'Package')] [string]$ItchTarget,
    [Parameter(ParameterSetName = 'Package')] [long]$MaxBytes = 1000000000,  # rule 10 "under 1 GB": decimal, the strict reading (mock 16 zip was 1023.8 MiB)
    [Parameter(ParameterSetName = 'Package')] [string]$NoticeFile,
    [Parameter(Mandatory, ParameterSetName = 'CheckButler')] [switch]$CheckButler
)

$ErrorActionPreference = "Stop"

# butler is often not on PATH in non-interactive sessions (ssh to the Legion: it lives at
# C:\Users\shino\butler\butler.exe). Lookup order: $env:BUTLER_PATH, PATH, known install dirs,
# then any C:\Users\*\butler\butler.exe. Returns the full path or throws.
function Resolve-Butler {
    $candidates = @()
    if ($env:BUTLER_PATH) { $candidates += $env:BUTLER_PATH }
    $onPath = Get-Command butler -ErrorAction SilentlyContinue
    if ($onPath) { $candidates += $onPath.Source }
    if ($env:USERPROFILE)  { $candidates += (Join-Path $env:USERPROFILE "butler\butler.exe") }
    if ($env:APPDATA)      { $candidates += (Join-Path $env:APPDATA "itch\bin\butler.exe") }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA "butler\butler.exe") }
    $candidates += "C:\Users\shino\butler\butler.exe"
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c -PathType Leaf)) { return (Resolve-Path -LiteralPath $c).Path }
    }
    $found = Get-ChildItem "C:\Users\*\butler\butler.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    throw "butler not found. Tried BUTLER_PATH, PATH, %USERPROFILE%\butler, %APPDATA%\itch\bin, C:\Users\*\butler. Install butler or set BUTLER_PATH to butler.exe."
}

if ($CheckButler) {
    # Read-only: print where butler is and its version, then exit. No login, no push, no packaging.
    $butlerExe = Resolve-Butler
    Write-Host "butler: $butlerExe"
    & $butlerExe -V
    exit $LASTEXITCODE
}

# $PSScriptRoot is unreliable as a param-block default when the script also has
# Mandatory parameters (PowerShell leaves it empty while evaluating defaults in that
# case), so the NOTICE.txt default is resolved here instead, after binding completes.
if (-not $PSBoundParameters.ContainsKey('NoticeFile')) {
    $NoticeFile = Join-Path (Split-Path -Parent $PSCommandPath) "..\_config\reference\NOTICE.txt"
}

# Fail fast, before the long cook, if a push was requested but butler can't be found.
$butlerExe = $null
if ($ItchTarget) { $butlerExe = Resolve-Butler }

$runUAT = Join-Path $EnginePath "Engine\Build\BatchFiles\RunUAT.bat"
if (-not (Test-Path $runUAT)) {
    throw "RunUAT.bat not found under $EnginePath (expected Engine\Build\BatchFiles\RunUAT.bat)"
}
if (-not (Test-Path $ProjectPath)) {
    throw ".uproject not found: $ProjectPath"
}

$archiveDir = Join-Path ([System.IO.Path]::GetDirectoryName($ProjectPath)) "Packaged"
if (Test-Path $archiveDir) { Remove-Item $archiveDir -Recurse -Force }

# -prereqs stages Engine\Extras\Redist\en-us\vc_redist.x64.exe; the root launcher exe checks for the
# VC++ 2015-2022 runtime and offers to install it from there (BootstrapPackagedGame
# InstallMissingPrerequisites), so the build runs on a clean Windows PC with no extra download (Rule 1).
& $runUAT BuildCookRun `
    -project="$ProjectPath" `
    -noP4 -platform=Win64 -clientconfig=Development -serverconfig=Development `
    -cook -build -stage -pak -prereqs -archive -archivedirectory="$archiveDir" -utf8output
if ($LASTEXITCODE -ne 0) { throw "RunUAT BuildCookRun failed (exit $LASTEXITCODE)" }

$stagedRoot = Join-Path $archiveDir "Windows"
if (-not (Test-Path $stagedRoot)) {
    throw "Expected staged output at $stagedRoot, not found - check the BuildCookRun log above"
}

if ($NoticeFile) {
    if (-not (Test-Path $NoticeFile)) {
        throw "NoticeFile $NoticeFile not found - pass -NoticeFile '' to skip on purpose for a non-shipping dry run"
    }
    Copy-Item $NoticeFile (Join-Path $stagedRoot "NOTICE.txt") -Force
    Write-Host "Included $NoticeFile as NOTICE.txt in the staged build"
} else {
    Write-Host "WARNING: no NoticeFile - this build has no third-party notice, do not submit it as the real entry"
}

# RunUAT's own NonUFSFiles manifest does not stage Engine/Content/Internationalization for this
# project (confirmed missing from $stagedRoot even on a from-clean BuildCookRun, mock jam 7,
# 2026-10-30). Without it the packaged exe hard-crashes at EnginePreInit with
# "ICU data directory was not discovered" before anything else runs. Copy it straight from the
# engine install instead of relying on the stage step.
$icuDest = Join-Path $stagedRoot "Engine\Content\Internationalization"
if (-not (Test-Path $icuDest)) {
    # Copy English only. The engine's Internationalization tree holds every preset (All, CJK, EFIGS, ...);
    # copying all of it staged 29,035 loose files in mock jam 17. The game only needs <Preset>/icudt78l
    # (BaseGame.ini defaults to InternationalizationPreset=English), ~781 files, laid out as
    # Internationalization\icudt78l like UAT's own pak staging.
    $icuRoot = Join-Path $EnginePath "Engine\Content\Internationalization"
    $icuSource = Join-Path $icuRoot "English\icudt78l"
    if (-not (Test-Path $icuSource)) {
        $icuSource = Join-Path $icuRoot "icudt78l"   # engine layouts without preset folders
    }
    if (-not (Test-Path $icuSource)) {
        throw "English Internationalization data (icudt78l) not found under engine install: $icuRoot"
    }
    New-Item -ItemType Directory -Path $icuDest -Force | Out-Null
    Copy-Item $icuSource (Join-Path $icuDest "icudt78l") -Recurse -Force
    Write-Host "Copied English Internationalization data (icudt78l) from engine install (missing from UAT's own stage output)"
}

# Strip the unrenamed engine template exe RunUAT bakes into every packaged build - the
# "wrong-exe trap" documented in legion_remote_launch.ps1's own docstring and
# stages/00_prep/output/mock-jam-findings-7.md: Engine\Binaries\Win64\UnrealGame.exe looks launchable but isn't
# the game, and silently hangs/shows nothing if it's ever run by mistake (confirmed happening
# for real, mock jam 9, 2026-10-31 - a stray UnrealGame.exe process was found running
# alongside the real game, root cause never pinned down since Windows auditing was off).
# Rename instead of delete so a build that unexpectedly needs the engine template exe isn't
# broken outright.
$decoyExe = Join-Path $stagedRoot "Engine\Binaries\Win64\UnrealGame.exe"
# Content-only (Blueprint) projects have no game module: UnrealGame.exe IS the game and the root
# <GameName>.exe is a stub that launches it. Only strip it for projects that have C++ Source.
$hasSource = Test-Path (Join-Path (Split-Path $ProjectPath -Parent) "Source")
if ((Test-Path $decoyExe) -and $hasSource) {
    Rename-Item $decoyExe "UnrealGame.exe.decoy-disabled" -Force
    Write-Host "Disabled decoy exe: $decoyExe"
}

# Debug symbols out of the stage (mock jam 16, 2026-11-10): a -build Development package on the
# source engine staged a 2.5 GB PolarityFlip.pdb next to the exe, which pushed the zip toward the
# 1 GB rule-10 limit and would have gone to itch too (butler pushes the staged folder). Players
# never need symbols. Move them (not delete) to Packaged\Symbols, keeping their relative paths, so
# a crash can still be read on the Legion; the zip, the PC fetch and the butler push then skip them.
$symbolsDir = Join-Path $archiveDir "Symbols"
$symbolFiles = @(Get-ChildItem $stagedRoot -Recurse -File -Include *.pdb, *.debug, *.sym -ErrorAction SilentlyContinue)
foreach ($f in $symbolFiles) {
    $rel = $f.FullName.Substring($stagedRoot.TrimEnd('\').Length + 1)
    $to = Join-Path $symbolsDir $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
    Move-Item -LiteralPath $f.FullName -Destination $to -Force
}
if ($symbolFiles.Count) {
    $symMB = [math]::Round((($symbolFiles | Measure-Object Length -Sum).Sum) / 1MB, 1)
    Write-Host "Moved $($symbolFiles.Count) debug symbol file(s) ($symMB MB) out of the stage to $symbolsDir"
}

$zipName = "${TeamName}_${GameName}.zip" -replace '\s', ''
$zipPath = Join-Path $archiveDir $zipName
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
# Compress-Archive silently drops some deeply-nested files on long paths (confirmed separately
# with its counterpart Expand-Archive, mock jam 7, 2026-10-30); tar is long-path safe.
Push-Location $stagedRoot
tar -a -cf $zipPath *
Pop-Location
if ($LASTEXITCODE -ne 0) { throw "tar zip creation failed (exit $LASTEXITCODE)" }

$zipSize = (Get-Item $zipPath).Length
Write-Host "Zip: $zipPath ($([math]::Round($zipSize / 1MB, 1)) MB)"
if ($zipSize -gt $MaxBytes) {
    throw "Zip is $([math]::Round($zipSize / 1MB, 1)) MB, over the $([math]::Round($MaxBytes / 1MB, 0)) MB gate limit"
}

if ($ItchTarget) {
    & $butlerExe push $stagedRoot $ItchTarget
    if ($LASTEXITCODE -ne 0) { throw "butler push failed (exit $LASTEXITCODE)" }
    Write-Host "Pushed $stagedRoot to $ItchTarget"
} else {
    Write-Host "No -ItchTarget given, skipping butler push. Zip is ready at $zipPath"
}

# Runs ON the Legion Go S (legion_preflight.py copies it over and runs it with -File).
# Only READS machine state and prints one JSON object; it changes nothing.
# Facts: OBS installed, OBS websocket port answering, programs allowed by enabled inbound
# firewall rules, scheduled tasks named MJ*, whether a console session is active/locked.
param([int]$ObsPort = 4455)
$ErrorActionPreference = 'SilentlyContinue'

$obsExe = 'C:\Program Files\obs-studio\bin\64bit\obs64.exe'

$tcp = New-Object Net.Sockets.TcpClient
$iar = $tcp.BeginConnect('127.0.0.1', $ObsPort, $null, $null)
$wsOpen = $iar.AsyncWaitHandle.WaitOne(2000) -and $tcp.Connected
$tcp.Close()

# Rules only count if they apply to a network profile that is active now (Profile is a flags
# value; Any covers all). Block rules beat allow rules, so they are reported separately.
$active = @(Get-NetConnectionProfile | ForEach-Object { [string]$_.NetworkCategory })
function Test-RuleActive($rule) {
    $p = [string]$rule.Profile
    if ($p -match 'Any') { return $true }
    foreach ($a in $active) { if ($p -match $a) { return $true } }
    return ($active.Count -eq 0)
}
# One pass, not one CIM lookup per rule (that can pass the 40 s ssh cap): list the enabled inbound
# rules once, list all application filters once, and join them by rule name (filter InstanceID).
$ruleAction = @{}
Get-NetFirewallRule -Enabled True -Direction Inbound | Where-Object { Test-RuleActive $_ } |
    ForEach-Object { $ruleAction[[string]$_.Name] = [string]$_.Action }
$programs = @(); $blocked = @()
Get-NetFirewallApplicationFilter | Where-Object { $_.Program -and $_.Program -ne 'Any' } | ForEach-Object {
    $act = $ruleAction[[string]$_.InstanceID]
    if ($act -eq 'Allow') { $programs += $_.Program } elseif ($act -eq 'Block') { $blocked += $_.Program }
}
$tasks = @(Get-ScheduledTask | Where-Object { $_.TaskName -like 'MJ*' } | ForEach-Object { $_.TaskName })
# `query user` does not exist on Windows Home (the Legion), so fall back to the logged-on user
# and to explorer.exe running in session 1 (the console session).
$consoleActive = $false
if (Get-Command query -ErrorAction SilentlyContinue) {
    $sessions = @(query user 2>$null)
    $consoleActive = [bool]($sessions | Where-Object { $_ -match 'console' -and $_ -match 'Active' })
}
if (-not $consoleActive) {
    # an explorer.exe owned by the logged-in user in a non-zero session (the console is not always 1)
    $who = (Get-CimInstance Win32_ComputerSystem).UserName
    if ($who) {
        foreach ($proc in @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'")) {
            if ($proc.SessionId -eq 0) { continue }
            $owner = Invoke-CimMethod -InputObject $proc -MethodName GetOwner
            if ((($owner.Domain + '\' + $owner.User) -ieq $who)) { $consoleActive = $true }
        }
    }
}
$locked = [bool](Get-Process LogonUI)

$out = [ordered]@{
    obsInstalled  = (Test-Path $obsExe)
    obsWebsocket  = [bool]$wsOpen
    firewallPrograms = $programs
    firewallBlocked = $blocked
    mjTasks       = $tasks
    consoleActive = $consoleActive
    locked        = $locked
}
ConvertTo-Json -InputObject $out -Compress

#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Runs ON the Legion Go S, started by a Scheduled Task with Interactive logon (the console session
  that owns the real display; see legion_screenshot.ps1 for why plain ssh cannot do this).
  Plays a scripted list of steps against the running packaged game using REAL OS input
  (user32 SendInput, hardware scan codes, so DirectInput / Raw Input games see it) and saves a
  PNG of the screen at every "shot" step. Never touches the game's own autopilot.

  Driven by visual_playtest.py. Do not run over plain ssh -Command: it will not see the desktop.

.PARAMETER StepsFile
  JSON array of steps:
    {"op":"wait","seconds":2}
    {"op":"shot","label":"start"}
    {"op":"burst","label":"endstate","seconds":3,"frames":12}  frames over N seconds, NO input (idle check)
    {"op":"key","key":"w","hold":1.5}            tap or hold a key (names in $ScanCodes below)
    {"op":"click","button":"left","x":960,"y":540}  x,y absolute pixels; omit for current position
    {"op":"move","dx":300,"dy":0}                relative mouse move (mouse look)
.PARAMETER GameProcess
  Process name (prefix) of the game. At the start and before every input step the script brings that
  window to the front and stops with ERROR if it cannot; every shot records whether the game was in front.
.PARAMETER OutDir
  Folder for PNGs, manifest.json, FOCUSED and, last, the file DONE.
  FOCUSED holds one line "FOCUSED <Windows FILETIME, UTC, 100 ns ticks>": the Legion clock time the game
  came to the front, before the first step. legion_record.py --sequence cuts the video head with it.
#>
param(
    [Parameter(Mandatory = $true)][string]$StepsFile,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [Parameter(Mandatory = $true)][string]$GameProcess
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class MJInput {
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Explicit)] public struct INPUTUNION { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public INPUTUNION u; }
    [DllImport("user32.dll", SetLastError = true)] public static extern uint SendInput(uint n, INPUT[] inputs, int size);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint from, uint to, bool attach);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder sb, int max);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    public static uint ForegroundPid() { uint pid; GetWindowThreadProcessId(GetForegroundWindow(), out pid); return pid; }
    public static string ForegroundTitle() { var sb = new System.Text.StringBuilder(256); GetWindowText(GetForegroundWindow(), sb, 256); return sb.ToString(); }
    // Lets SetForegroundWindow through by sharing the foreground window's input queue. Never sends a key:
    // a bare Alt tap opens the AMD overlay on the Legion and covers the frames (mock jam 11, gap 16).
    public static void ForceForeground(IntPtr h) {
        uint pid; uint fg = GetWindowThreadProcessId(GetForegroundWindow(), out pid); uint me = GetCurrentThreadId();
        if (fg != 0 && fg != me) AttachThreadInput(me, fg, true);
        BringWindowToTop(h); SetForegroundWindow(h);
        if (fg != 0 && fg != me) AttachThreadInput(me, fg, false);
    }
    public static void Key(ushort scan, bool extended, bool up) {
        INPUT[] a = new INPUT[1];
        a[0].type = 1;
        a[0].u.ki.wScan = scan;
        a[0].u.ki.dwFlags = 0x0008 | (up ? 0x0002u : 0u) | (extended ? 0x0001u : 0u); // SCANCODE | KEYUP | EXTENDEDKEY
        SendInput(1, a, Marshal.SizeOf(typeof(INPUT)));
    }
    public static void Mouse(uint flags, int dx, int dy) {
        INPUT[] a = new INPUT[1];
        a[0].type = 0;
        a[0].u.mi.dx = dx; a[0].u.mi.dy = dy; a[0].u.mi.dwFlags = flags;
        SendInput(1, a, Marshal.SizeOf(typeof(INPUT)));
    }
}
"@

# Must come before any screen-size call: without it a scaled display (125%, 150%) reports scaled
# bounds and CopyFromScreen crops the picture to a corner (seen on the Legion, mock 10).
[void][MJInput]::SetProcessDPIAware()

# name -> @(scan code, extended?). One entry per line. MUST equal KEYS in visual_playtest.py
# (tests/test_visual_playtest.py compares them), so a key the Python side accepts is pressable here.
$ScanCodes = @{
    "esc" = @(0x01, $false)
    "1" = @(0x02, $false)
    "2" = @(0x03, $false)
    "3" = @(0x04, $false)
    "4" = @(0x05, $false)
    "5" = @(0x06, $false)
    "6" = @(0x07, $false)
    "7" = @(0x08, $false)
    "8" = @(0x09, $false)
    "9" = @(0x0A, $false)
    "0" = @(0x0B, $false)
    "tab" = @(0x0F, $false)
    "q" = @(0x10, $false)
    "w" = @(0x11, $false)
    "e" = @(0x12, $false)
    "r" = @(0x13, $false)
    "t" = @(0x14, $false)
    "y" = @(0x15, $false)
    "u" = @(0x16, $false)
    "i" = @(0x17, $false)
    "o" = @(0x18, $false)
    "p" = @(0x19, $false)
    "enter" = @(0x1C, $false)
    "ctrl" = @(0x1D, $false)
    "a" = @(0x1E, $false)
    "s" = @(0x1F, $false)
    "d" = @(0x20, $false)
    "f" = @(0x21, $false)
    "g" = @(0x22, $false)
    "h" = @(0x23, $false)
    "j" = @(0x24, $false)
    "k" = @(0x25, $false)
    "l" = @(0x26, $false)
    "shift" = @(0x2A, $false)
    "z" = @(0x2C, $false)
    "x" = @(0x2D, $false)
    "c" = @(0x2E, $false)
    "v" = @(0x2F, $false)
    "b" = @(0x30, $false)
    "n" = @(0x31, $false)
    "m" = @(0x32, $false)
    "space" = @(0x39, $false)
    "up" = @(0x48, $true)
    "left" = @(0x4B, $true)
    "right" = @(0x4D, $true)
    "down" = @(0x50, $true)
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$manifest = New-Object System.Collections.ArrayList
$t0 = Get-Date
$shotNo = 0
$lastWasInput = $false

# The game process (name starts with $GameProcess, so Game-Win64-Shipping counts) that owns a window.
function Get-GameProc {
    Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$GameProcess*" -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1
}

function Test-GameForeground {
    $p = Get-GameProc
    return ($null -ne $p) -and ([MJInput]::ForegroundPid() -eq [uint32]$p.Id)
}

# Bring the game window to the front. Input goes to the foreground window, so a key step must never
# run while anything else (a console, a notification, the lock screen) is in front: throw instead.
# A stray console window can hold focus (mock jam 11, gap 19): from the second try on, minimise every
# other window first, then retry. On failure the message names the window that kept focus.
function Hide-OtherWindows {
    Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowHandle -ne 0 -and $_.Name -notlike "$GameProcess*" -and $_.Name -ne "explorer" -and $_.Id -ne $PID
    } | ForEach-Object { [void][MJInput]::ShowWindow($_.MainWindowHandle, 6) }   # SW_MINIMIZE
}

function Assert-GameForeground {
    for ($i = 0; $i -lt 6; $i++) {
        if (Test-GameForeground) { return }
        if ($i -ge 1) { Hide-OtherWindows }
        $p = Get-GameProc
        if ($null -ne $p) {
            [void][MJInput]::ShowWindow($p.MainWindowHandle, 9)   # SW_RESTORE
            [MJInput]::ForceForeground($p.MainWindowHandle)
        }
        Start-Sleep -Milliseconds 400
    }
    if (-not (Test-GameForeground)) {
        $title = [MJInput]::ForegroundTitle()
        throw "the game window ($GameProcess) is not the foreground window; focus is held by '$title'; input would go elsewhere"
    }
}

function Save-Shot($label, $afterInput, $extra = @{}) {
    $script:shotNo++
    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $name = ("{0:D2}_{1}.png" -f $script:shotNo, $label)
    $bmp.Save((Join-Path $OutDir $name), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
    $fg = Test-GameForeground
    $entry = @{ label = $label; file = $name; t = $secs; after_input = $afterInput; foreground = [bool]$fg }
    foreach ($k in $extra.Keys) { $entry[$k] = $extra[$k] }
    [void]$manifest.Add($entry)
}

try {
    $steps = Get-Content -Raw -Path $StepsFile | ConvertFrom-Json
    # Focus first, before any step, so no shot or video opens on another app (mock 16: the first ~22 s of
    # the take showed OBS until the first key step). Throws like a key step if the game cannot be fronted.
    Assert-GameForeground
    ("FOCUSED {0}" -f (Get-Date).ToFileTimeUtc()) | Set-Content -Path (Join-Path $OutDir "FOCUSED") -Encoding ASCII
    foreach ($s in $steps) {
        switch ($s.op) {
            "wait" { Start-Sleep -Milliseconds ([int]([double]$s.seconds * 1000)) }
            "shot" { Save-Shot $s.label $lastWasInput; $lastWasInput = $false }
            "declare" { }   # end-state declaration for visual_playtest.py; nothing to do on the Legion
            "burst" {
                # N frames over `seconds` with NO input (idle-stability check). Never after_input.
                $frames = 12; if ($null -ne $s.frames) { $frames = [int]$s.frames }
                $secs = 3.0; if ($null -ne $s.seconds) { $secs = [double]$s.seconds }
                $interval = $secs / $frames
                for ($i = 1; $i -le $frames; $i++) {
                    $t1 = Get-Date
                    $extra = @{ burst = [string]$s.label; burst_index = $i }
                    if ($null -ne $s.end_state) { $extra["end_state"] = [string]$s.end_state }
                    Save-Shot ("burst_{0}_{1:D2}" -f $s.label, $i) $false $extra
                    $left = $interval - ((Get-Date) - $t1).TotalSeconds
                    if ($left -gt 0) { Start-Sleep -Milliseconds ([int]($left * 1000)) }
                }
                $lastWasInput = $false
            }
            "key" {
                Assert-GameForeground
                # "key": NAME, or "keys": [NAME, ...] held together (pressed in order, released in reverse)
                $names = @()
                if ($null -ne $s.keys) { $names = @($s.keys | ForEach-Object { [string]$_ }) } else { $names = @([string]$s.key) }
                $codes = @()
                foreach ($n in $names) {
                    $k = $ScanCodes[$n]
                    if ($null -eq $k) { throw "unknown key name: $n (a bare Alt is never sent: it opens the AMD overlay)" }
                    $codes += ,$k
                }
                $hold = 0.1
                if ($null -ne $s.hold) { $hold = [double]$s.hold }
                foreach ($k in $codes) { [MJInput]::Key([uint16]$k[0], [bool]$k[1], $false) }
                Start-Sleep -Milliseconds ([int]($hold * 1000))
                for ($j = $codes.Count - 1; $j -ge 0; $j--) { [MJInput]::Key([uint16]$codes[$j][0], [bool]$codes[$j][1], $true) }
                $lastWasInput = $true
            }
            "click" {
                Assert-GameForeground
                if ($null -ne $s.x) { [void][MJInput]::SetCursorPos([int]$s.x, [int]$s.y) }
                $down = 0x0002; $up = 0x0004
                if ($s.button -eq "right") { $down = 0x0008; $up = 0x0010 }
                [MJInput]::Mouse($down, 0, 0)
                Start-Sleep -Milliseconds 80
                [MJInput]::Mouse($up, 0, 0)
                $lastWasInput = $true
            }
            "move" {
                Assert-GameForeground
                [MJInput]::Mouse(0x0001, [int]$s.dx, [int]$s.dy)  # MOUSEEVENTF_MOVE, relative
                $lastWasInput = $true
            }
            default { throw "unknown op: $($s.op)" }
        }
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "manifest.json") -Encoding UTF8
    "ok" | Set-Content -Path (Join-Path $OutDir "DONE") -Encoding ASCII
}
catch {
    # Release anything we might be holding, then say why we stopped.
    $_.Exception.Message | Set-Content -Path (Join-Path $OutDir "ERROR") -Encoding UTF8
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "manifest.json") -Encoding UTF8
    "error" | Set-Content -Path (Join-Path $OutDir "DONE") -Encoding ASCII
}

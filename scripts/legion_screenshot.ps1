#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Runs ON the Legion Go S, launched via a Scheduled Task with Interactive logon (same
  session-isolation trick as legion_remote_launch.ps1 - a screen capture taken directly over
  SSH runs in SSH's own non-interactive session 0 and captures nothing useful; it has to run
  in the real interactive session that owns the physical display). Captures the full virtual
  screen (all monitors) to a PNG.

  Added mock jam 9 (SkyAtmosphere warning verification): the owner reported on-screen-only red
  warning text that never appears in the packaged build's log file (confirmed: zero log
  matches for the warning string both before and after the fix), so legion_playtest.py's
  log-based verification couldn't confirm or deny it. A screenshot was the only way to get real
  before/after evidence instead of trusting a background session's "the condition no longer
  holds" claim. Driven by legion_capture_screenshot.py - don't run this directly over SSH with
  -Command, it won't see the real desktop.

.PARAMETER OutPath
  Where to save the PNG. Defaults to the same scratch dir legion_remote_launch.ps1 uses.

.OUTPUTS
  A single line "SAVED:<path>" on stdout.
#>
param(
    [string]$OutPath = "C:\Dev\.legion_playtest_scratch\screenshot.png"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Must come before reading the screen bounds: on a scaled display (125%, 150%) an unaware process gets
# scaled bounds and CopyFromScreen crops the picture to a corner (seen on the Legion, mock 10).
Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public static class MJDpi { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[void][MJDpi]::SetProcessDPIAware()

$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()
Write-Output "SAVED:$OutPath"

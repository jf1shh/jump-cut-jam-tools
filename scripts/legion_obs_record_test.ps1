# OBS end-to-end recording test for the Legion Go S, driven over OBS's websocket API.
# Run over `ssh <device-host>` while OBS is open in the interactive session with its websocket server
# enabled (see stages/04_ship/references/capture-setup.md, "Verified test recording", for the full launch/close steps).
# Makes sure a Display Capture source exists, mutes Mic/Aux, records $RecSeconds seconds, then
# saves a replay-buffer clip, and prints OBS's own stats, both output paths and the StartRecord time as JSON.
param([int]$RecSeconds = 12, [int]$ReplaySeconds = 15)
$ErrorActionPreference = 'Stop'
$pw = (Get-Content "$env:APPDATA\obs-studio\plugin_config\obs-websocket\config.json" -Raw | ConvertFrom-Json).server_password
$ws = New-Object System.Net.WebSockets.ClientWebSocket
$ct = [Threading.CancellationToken]::None
$ws.ConnectAsync([Uri]'ws://127.0.0.1:4455', $ct).Wait()
function Recv { $buf = New-Object byte[] 65536; $ms = New-Object IO.MemoryStream
  do { $seg = New-Object ArraySegment[byte] -ArgumentList (,$buf); $r = $ws.ReceiveAsync($seg, $ct).Result; $ms.Write($buf, 0, $r.Count) } while (-not $r.EndOfMessage)
  [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json }
function Send($obj) { $b = [Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json -Depth 10 -Compress)); $ws.SendAsync((New-Object ArraySegment[byte] -ArgumentList (,$b)), 'Text', $true, $ct).Wait() }
function Sha($s) { [Convert]::ToBase64String([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($s))) }
$hello = Recv
$a = $hello.d.authentication
Send @{ op = 1; d = @{ rpcVersion = 1; authentication = (Sha ((Sha ($pw + $a.salt)) + $a.challenge)); eventSubscriptions = 0 } }
$null = Recv
$script:n = 0
function Req($type, $data = @{}) { $script:n++; Send @{ op = 6; d = @{ requestType = $type; requestId = "$script:n"; requestData = $data } }
  do { $m = Recv } while ($m.op -ne 7)
  if (-not $m.d.requestStatus.result) { Write-Output "FAIL $type : $($m.d.requestStatus.code) $($m.d.requestStatus.comment)" }
  $m.d.responseData }
$out = [ordered]@{}
$v = Req GetVersion; $out.obs = $v.obsVersion
$out.video = Req GetVideoSettings
$out.recordDir = (Req GetRecordDirectory).recordDirectory
$items = (Req GetSceneItemList @{ sceneName = 'Scene' }).sceneItems
$id = ($items | Where-Object sourceName -eq 'Display Capture').sceneItemId
if (-not $id) { $id = (Req CreateInput @{ sceneName = 'Scene'; inputName = 'Display Capture'; inputKind = 'monitor_capture'; inputSettings = @{}; sceneItemEnabled = $true }).sceneItemId }
$mons = (Req GetInputPropertiesListPropertyItems @{ inputName = 'Display Capture'; propertyName = 'monitor_id' }).propertyItems | Where-Object { $_.itemValue -and $_.itemValue -ne 'DUMMY' -and $_.itemName -notlike '[[]*' }
$out.monitorPicked = $mons[0].itemName
$null = Req SetInputSettings @{ inputName = 'Display Capture'; inputSettings = @{ monitor_id = $mons[0].itemValue } }
$null = Req SetSceneItemTransform @{ sceneName = 'Scene'; sceneItemId = $id; sceneItemTransform = @{ boundsType = 'OBS_BOUNDS_SCALE_INNER'; boundsWidth = 1920; boundsHeight = 1080; boundsAlignment = 0; positionX = 0; positionY = 0; alignment = 5 } }
$out.displaySettings = (Req GetInputSettings @{ inputName = 'Display Capture' }).inputSettings
$out.special = Req GetSpecialInputs
$out.desktopAudioSettings = (Req GetInputSettings @{ inputName = 'Desktop Audio' }).inputSettings
$null = Req SetInputMute @{ inputName = 'Mic/Aux'; inputMuted = $true }
$out.micMuted = (Req GetInputMute @{ inputName = 'Mic/Aux' }).inputMuted
$null = Req StartRecord
# Legion clock (Windows FILETIME, UTC, 100 ns) once OBS has answered StartRecord: legion_record.py --sequence
# subtracts it from the input script's FOCUSED time to cut the video head.
$out.startRecordFileTimeUtc = (Get-Date).ToFileTimeUtc()
Start-Sleep -Seconds $RecSeconds
$out.statsDuringRecord = Req GetStats
$out.recStatus = Req GetRecordStatus
$out.recordFile = (Req StopRecord).outputPath
$null = Req StartReplayBuffer
Start-Sleep -Seconds $ReplaySeconds
$null = Req SaveReplayBuffer
Start-Sleep -Seconds 3
$out.replayFile = (Req GetLastReplayBufferReplay).savedReplayPath
$null = Req StopReplayBuffer
$out.statsEnd = Req GetStats
$ws.CloseAsync('NormalClosure', 'done', $ct).Wait()
$out | ConvertTo-Json -Depth 6

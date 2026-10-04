param([string]$Trace='research/doom/results/map01-v39-coast-liveness-live-01')
$ErrorActionPreference='Stop'
$manifest=Get-Content -Raw -LiteralPath (Join-Path $Trace 'retention-manifest.json') | ConvertFrom-Json
$files=@{}; foreach($f in $manifest.files){$files[$f.path]=$f}
$eventPath=Join-Path $Trace 'runtime/events.jsonl'; $reportPath=Join-Path $Trace 'report.json'
$eh=(Get-FileHash -Algorithm SHA256 -LiteralPath $eventPath).Hash.ToLower()
$rh=(Get-FileHash -Algorithm SHA256 -LiteralPath $reportPath).Hash.ToLower()
if($eh -ne $files['runtime/events.jsonl'].sha256 -or $rh -ne $files['report.json'].sha256){throw 'STOP_PROVENANCE_MISMATCH'}
$events=@((Get-Content -LiteralPath $eventPath | Where-Object {$_}) | ForEach-Object {$_ | ConvertFrom-Json})
$counts=@{}; $events | Group-Object event | ForEach-Object {$counts[$_.Name]=$_.Count}
$report=Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
$visible=@($report.decisions.effect_receipts | Where-Object result -eq 'visible_change')
$score=@($events | Where-Object event -eq 'post_control_score')
$task=@($events | Where-Object {$_.event -in @('task_effect','scored_task_effect','kill','enemy_killed','map_exit','objective_complete')})
if($events.Count -ne 634 -or $counts.input_admission -ne 39 -or $counts.input_released -ne 1 -or $counts.input_release_measurement -ne 0 -or $counts.input_release_transition -ne 0 -or $score.Count -ne 1 -or $task.Count -ne 0 -or $visible.Count -ne 4 -or (@($visible | Where-Object scope -ne 'viewport pixels only').Count -ne 0)){throw 'STOP_EVENT_SHAPE_CHANGED'}
$latestOther=($events | Where-Object event -ne 'post_control_score' | Measure-Object -Property emit_ns -Maximum).Maximum
[pscustomobject]@{event_sha256=$eh;report_sha256=$rh;event_count=$events.Count;input_admission_count=$counts.input_admission;aggregate_release_count=$counts.input_released;per_key_release_measurement_count=$counts.input_release_measurement;per_key_release_transition_count=$counts.input_release_transition;post_control_score_count=$score.Count;score_emit_ns=$score[0].emit_ns;latest_other_emit_ns=$latestOther;post_control_score_after_all_other_events=([int64]$score[0].emit_ns -gt [int64]$latestOther);in_run_task_effect_count=$task.Count;visible_viewport_receipts=$visible.Count;disposition='NO_INDEPENDENT_USEFUL_FEEDBACK_ONSET_IN_RETAINED_TRACE'} | ConvertTo-Json -Compress

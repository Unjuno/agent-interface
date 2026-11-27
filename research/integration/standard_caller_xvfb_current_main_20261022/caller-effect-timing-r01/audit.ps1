$ErrorActionPreference = 'Stop'
$packet = Split-Path -Parent $MyInvocation.MyCommand.Path
$r = Get-Content -Raw (Join-Path $packet 'result.json') | ConvertFrom-Json
$f = $r.fresh_session_recovery
$ns = $r.timing_ns
$cancelAdmission = [double]$r.cancellation_terminal.admitted_monotonic_ns
$cancelToolCall = [double]$ns.cancel_tool_invoked
$cancelReturn = [double]$ns.cancel_returned
$inputStart = [double]$f.input_started_monotonic_ns
$inputReturn = [double]$f.input_returned_monotonic_ns
$appEvent = [double]$f.keypress_event_observed_monotonic_ns
$effectCommit = [double]$f.application_effect_committed_monotonic_ns
$readStart = [double]$f.effect_readback_started_monotonic_ns
$readDone = [double]$f.effect_readback_completed_monotonic_ns
$releaseStart = [double]$r.cancel.owner_release_attempt.release.release_started_monotonic_ns
$releaseRequest = [double]$r.cancel.owner_release_attempt.release.release_requests[0].requested_monotonic_ns
$releaseReadback = [double]$r.cancel.owner_release_attempt.release.readback_monotonic_ns
$intervals = [ordered]@{
  cancel_invocation_to_return_ms = ($cancelReturn-$cancelToolCall)/1000000
  cancel_admission_to_response_ms = ($cancelReturn-$cancelAdmission)/1000000
  release_operation_start_to_supervisor_readback_ms = ($releaseReadback-$releaseStart)/1000000
  key_release_request_to_supervisor_readback_ms = ($releaseReadback-$releaseRequest)/1000000
  cancel_admission_to_key_release_request_ms = ($releaseRequest-$cancelAdmission)/1000000
  cancel_admission_to_supervisor_readback_ms = ($releaseReadback-$cancelAdmission)/1000000
  input_invocation_to_app_event_ms = ($appEvent-$inputStart)/1000000
  app_event_to_effect_commit_ms = ($effectCommit-$appEvent)/1000000
  effect_commit_to_independent_readback_ms = ($readDone-$effectCommit)/1000000
  input_invocation_to_independent_readback_ms = ($readDone-$inputStart)/1000000
  input_return_to_independent_readback_ms = ($readDone-$inputReturn)/1000000
}
$recorded = [ordered]@{
  cancel_invocation_to_return_ms = [double]$r.cancel_invocation_elapsed_ms
  cancel_admission_to_response_ms = ([double]$ns.cancel_returned-[double]$r.cancel_response.cancellation.admitted_monotonic_ns)/1000000
  input_invocation_to_app_event_ms = [double]$f.effect_timing_ms.input_invocation_to_keypress_observed
  app_event_to_effect_commit_ms = [double]$f.effect_timing_ms.keypress_observed_to_application_effect_commit
  effect_commit_to_independent_readback_ms = [double]$f.effect_timing_ms.application_effect_commit_to_independent_readback_completed
  input_invocation_to_independent_readback_ms = [double]$f.effect_timing_ms.input_invocation_to_effect_readback_completed
  input_return_to_independent_readback_ms = [double]$f.effect_timing_ms.input_return_to_effect_readback_completed
}
$events = @($r.synthetic_application_effect.app_key_events | Where-Object {
  $_.window -eq $f.new_target_xid -and $_.type -eq 2 -and $_.detail -eq 54
})
$keysDownRelease = @($r.independent_release_readback.keys_down.PSObject.Properties | Where-Object { $_.Value })
$keysDownFresh = @($f.release_readback_after_input.PSObject.Properties | Where-Object { $_.Value })
$keysDownHorizon = @($f.horizon_readback.PSObject.Properties | Where-Object { $_.Value })
$oldKeysDownHorizon = @($r.late_request_horizon_readback.keys_down.PSObject.Properties | Where-Object { $_.Value })
$finite = $true
foreach ($v in $intervals.Values) { if (-not [double]::IsFinite([double]$v) -or [double]$v -lt 0) { $finite = $false } }
$matchesReported = $true
foreach ($key in $recorded.Keys) { if ([math]::Abs([double]$intervals[$key]-[double]$recorded[$key]) -gt 0.00001) { $matchesReported = $false } }
$checks = [ordered]@{
  exactly_one_fresh_c_keypress_with_commit = ($events.Count -eq 1 -and $null -ne $events[0].effect_committed_ns)
  prior_task_effect_exact = (($r.synthetic_application_effect.before_cancel_property_value -join ',') -eq '1' -and ($r.synthetic_application_effect.property_value -join ',') -eq '1')
  fresh_task_effect_exact = (($f.effect_before_input -join ',') -eq '0' -and ($f.effect_after_input -join ',') -eq '3' -and ($f.effect_at_horizon -join ',') -eq '3' -and $f.input_status -eq 'completed')
  independent_release_readback_all_up = ($keysDownRelease.Count -eq 0)
  fresh_action_and_horizon_all_up = ($keysDownFresh.Count -eq 0 -and $keysDownHorizon.Count -eq 0)
  delayed_request_horizon_all_up = ($oldKeysDownHorizon.Count -eq 0 -and -not $r.late_request_horizon_readback.late_keypress_b_observed)
  no_old_delayed_press_after_new_session = (-not $f.late_old_keypress_after_new_session -and -not $r.synthetic_application_effect.late_b_press_event_seen)
  cancellation_unknown_replay_denied = ($r.cancel.cleanup_status -eq 'UNKNOWN' -and $r.cancel.release_confirmed -eq $false -and $null -eq $r.cancel.task_success -and $r.cancel.replay_allowed -eq $false -and $r.cancel.late_server_request_possible -eq $true)
  cancellation_call_under_300ms = ($intervals.cancel_invocation_to_return_ms -le 300)
  timestamps_recompute_reported_intervals = $matchesReported
  all_recomputed_intervals_finite_and_nonnegative = $finite
}
$out = [ordered]@{ audit='independent PowerShell reconstruction from preserved result.json'; raw_test_status=$r.status; raw_reconstruction_pass=(@($checks.Values | Where-Object { -not $_ }).Count -eq 0); checks=$checks; derived_intervals_ms=$intervals; report_crosscheck_ms=$recorded; fresh_c_keypress_count=$events.Count }
$out | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $packet 'audit.json') -Encoding utf8NoBOM
$out | ConvertTo-Json -Depth 6
if (-not $out.raw_reconstruction_pass) { exit 1 }

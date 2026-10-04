$ErrorActionPreference = 'Stop'
$package = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $package '..\..\..')).Path
$doom = Join-Path $repo 'research\doom'
$wslOut = Join-Path $package 'WSL_TEST_OUTPUT.txt'
$windowsOut = Join-Path $package 'WINDOWS_TEST_OUTPUT.txt'
$linuxCommand = 'cd /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-7/work/pr7662-audit-20261005/research/doom && python3 -m unittest -v test_map01_scorer_stdio_adapter_v3 test_map01_scorer_stdio_adapter_v1 test_map01_scorer_stdio_adapter_v2 test_session_map01_v18 test_session_map01_v19.MeasuredTailCompositionTests.test_backend_capture_keeps_raw_event_names_and_requires_empty_backend test_session_map01_v19.MeasuredTailCompositionTests.test_emit_failure_does_not_publish_candidate test_session_map01_v19.MeasuredTailCompositionTests.test_main_patches_session_backend_to_the_perkey_bridge test_session_map01_v19.MeasuredTailCompositionTests.test_measured_tail_runs_before_final_sample_and_records_boundary test_session_map01_v19.MeasuredTailCompositionTests.test_missing_candidate_skips_tail_but_keeps_final_sample'
& wsl.exe -d Ubuntu -- bash -lc $linuxCommand *> $wslOut
$wslExit = $LASTEXITCODE
Push-Location $doom
try {
    & python -m unittest -v test_map01_scorer_stdio_adapter_v3 test_map01_scorer_stdio_adapter_v1 test_map01_scorer_stdio_adapter_v2 test_session_map01_v18 test_session_map01_v19 test_v39_tail_session_selection *> $windowsOut
    $windowsExit = $LASTEXITCODE
}
finally {
    Pop-Location
}
$record = [ordered]@{
    schema = 'v39-perkey-scorer-tail-a01-result-v1'
    experiment_id = 'v39-perkey-scorer-tail-a01-20261005'
    disposition = if ($wslExit -eq 0 -and $windowsExit -eq 0) { 'PASS' } else { 'FAIL' }
    scope = 'construction-only; fake-display frozen event pair and socket/session test doubles'
    commands = [ordered]@{
        wsl_core = $linuxCommand
        windows_compatibility = 'python -m unittest -v test_map01_scorer_stdio_adapter_v3 test_map01_scorer_stdio_adapter_v1 test_map01_scorer_stdio_adapter_v2 test_session_map01_v18 test_session_map01_v19 test_v39_tail_session_selection'
    }
    exit_codes = [ordered]@{ wsl_core = $wslExit; windows_compatibility = $windowsExit }
    input = 'research/doom/map01_v39_perkey_measurement_consumer_a03_20261005/INPUT_EVENTS.jsonl'
    expected_release_boundary_ns = 87811364949416
    forbidden_claims = @('live input', 'application consumption', 'task effect', 'threat response', 'bounded recovery')
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $package 'RESULT.json') -Encoding utf8
if ($wslExit -ne 0 -or $windowsExit -ne 0) { exit 1 }

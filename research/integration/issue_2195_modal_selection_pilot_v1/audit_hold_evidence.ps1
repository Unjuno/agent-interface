$ErrorActionPreference = 'Stop'
$pilot = $PSScriptRoot
$outputs = Join-Path $pilot 'evidence'

$freeze = Get-Content (Join-Path $pilot 'FREEZE.json') -Raw | ConvertFrom-Json
$result = Get-Content (Join-Path $pilot 'RESULT.json') -Raw | ConvertFrom-Json
$cases = @(Get-Content (Join-Path $pilot 'cases.json') -Raw | ConvertFrom-Json)
$raw = Get-Content (Join-Path $outputs 'responses.json') -Raw | ConvertFrom-Json
$caseIds = @($cases | ForEach-Object { $_.case_id })
$adverseCases = @($cases | Where-Object { $_.case_id -ne 'RECOVERED_MODAL_EXACT' })

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$checks = [ordered]@{
    decision_is_timeout_hold = ($result.decision -eq 'HOLD_PILOT_INFERENCE_TIMEOUT')
    six_cases = ($cases.Count -eq 6)
    case_ids_unique = (@($caseIds | Sort-Object -Unique).Count -eq 6)
    exact_case_recommends_only_candidate_action = (@($cases | Where-Object {
        $_.case_id -eq 'RECOVERED_MODAL_EXACT' -and $_.expected -eq 'REBINDED_DISMISS'
    }).Count -eq 1)
    adverse_cases_expect_non_action = (@($adverseCases | Where-Object {
        $_.expected -notin @('OBSERVE_AGAIN', 'QUERY', 'ABORT', 'ESCALATE')
    }).Count -eq 0)
    all_recovery_receipts_have_no_authority = (@($cases | Where-Object {
        $_.evidence.recovery.authority -ne 'none' -or $_.evidence.recovery.task_input_granted -ne $false
    }).Count -eq 0)
    one_request_started = ($result.requests_started -eq 1 -and $result.raw_output.records -eq 1)
    started_case_matches_raw_record = ($raw.case_id -eq $result.raw_output.record_case_id)
    raw_record_has_no_response = ([string]::IsNullOrEmpty($raw.response) -and $result.raw_output.record_has_model_response -eq $false)
    timeout_recorded = ($raw.error -like '*240 seconds*' -and $result.client_timeouts -eq 1)
    no_retries = ($result.retries -eq 0)
    five_cases_not_started = ($result.not_started -eq 5)
    no_task_input_or_model_action_execution = ($result.task_input_dispatches -eq 0 -and $result.model_action_recommendations_executed -eq 0)
    raw_record_sha256 = ((Get-Sha256 (Join-Path $outputs 'responses.json')) -eq $result.raw_output.sha256)
    plan_sha256 = ((Get-Sha256 (Join-Path $pilot 'PLAN.md')) -eq $freeze.preregistration.plan_sha256)
    cases_sha256 = ((Get-Sha256 (Join-Path $pilot 'cases.json')) -eq $freeze.preregistration.cases_sha256)
    fixture_sha256 = ((Get-Sha256 (Join-Path $outputs 'fixture.svg')) -eq $freeze.fixture.svg_sha256)
    screenshot_sha256 = ((Get-Sha256 (Join-Path $outputs 'modal.png')) -eq $freeze.fixture.image_sha256)
}

$failed = @($checks.GetEnumerator() | Where-Object { $_.Value -ne $true } | ForEach-Object { $_.Key })
[ordered]@{
    schema = 'agent-interface/issue-2195-read-only-hold-audit-v1'
    disposition = if ($failed.Count -eq 0) { 'PASS_HOLD_EVIDENCE_INTEGRITY' } else { 'FAIL_AUDIT' }
    checks = $checks
    failed_checks = $failed
    requests_planned = $result.requests_planned
    requests_started = $result.requests_started
    responses_received = $result.responses_received
    not_started = $result.not_started
    retries = $result.retries
    raw_output_sha256 = Get-Sha256 (Join-Path $outputs 'responses.json')
    scope = 'read-only integrity audit of the retained local timeout HOLD; no scientific/model-selection pass'
} | ConvertTo-Json -Depth 5

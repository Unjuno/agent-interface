$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = (Resolve-Path '.').Path
$env:AGENT_INTERFACE_RETAIN_APP_SERVER_CALC_EVIDENCE = (Join-Path (Resolve-Path 'research/integration/standard_mcp_task_ledger_57_v1/plan-evidence-join-20261104-02').Path 'raw-runtime')
python -m unittest test_plan_evidence_join_v1 test_comparison_measurement_v1 *> research/integration/standard_mcp_task_ledger_57_v1/plan-evidence-join-20261104-02/normal.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -O -m unittest test_plan_evidence_join_v1 test_comparison_measurement_v1 *> research/integration/standard_mcp_task_ledger_57_v1/plan-evidence-join-20261104-02/optimized.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score *> research/integration/standard_mcp_task_ledger_57_v1/plan-evidence-join-20261104-02/composition.log
exit $LASTEXITCODE

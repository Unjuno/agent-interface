#!/bin/sh
set -eu
cd /workspace/research/integration/standard_mcp_task_ledger_57_v1
export PYTHONPATH=/workspace
export AGENT_INTERFACE_RETAIN_APP_SERVER_CALC_EVIDENCE=/evidence/raw-runtime-final-10
python3 -m unittest test_plan_evidence_join_v1 test_comparison_measurement_v1 > /evidence/normal.log 2>&1
python3 -O -m unittest test_plan_evidence_join_v1 test_comparison_measurement_v1 > /evidence/optimized.log 2>&1
python3 -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score > /evidence/composition.log 2>&1

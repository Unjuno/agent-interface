#!/bin/sh
set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 runtime.guarded_x11_v1.test_calc_profile_v1 runtime.guarded_x11_v1.test_calc_task_artifact_v1 runtime.cli_v1.test_mcp_guarded runtime.cli_v1.test_mcp_owned_process test_mcp_endpoint_composition test_comparison_measurement_v1 test_app_server_file_spool_v1 test_app_server_spool_worker_v1 test_app_server_provider_to_public_mcp_v1 > /evidence/normal.log 2>&1
normal=$?
cat /evidence/normal.log
python3 -O -m unittest runtime.guarded_x11_v1.test_calc_symbolic_plan_v1 runtime.guarded_x11_v1.test_calc_profile_v1 runtime.guarded_x11_v1.test_calc_task_artifact_v1 runtime.cli_v1.test_mcp_guarded runtime.cli_v1.test_mcp_owned_process test_mcp_endpoint_composition test_comparison_measurement_v1 test_app_server_file_spool_v1 test_app_server_spool_worker_v1 test_app_server_provider_to_public_mcp_v1 > /evidence/optimized.log 2>&1
opt=$?
cat /evidence/optimized.log
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
exit $((normal || opt))
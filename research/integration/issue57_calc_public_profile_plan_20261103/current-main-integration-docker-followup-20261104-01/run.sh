#!/bin/sh
set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_parent_custodied_calc_launch_is_opt_in_and_gates_profile > /evidence/normal.log 2>&1
normal=$?
cat /evidence/normal.log
python3 -O -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_parent_custodied_calc_launch_is_opt_in_and_gates_profile > /evidence/optimized.log 2>&1
opt=$?
cat /evidence/optimized.log
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
exit $((normal || opt))

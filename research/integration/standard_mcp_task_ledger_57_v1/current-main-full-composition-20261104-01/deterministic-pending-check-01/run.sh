#!/bin/sh
set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prearmed_cleanup_can_precede_retired_owners_queued_down > /evidence/normal.log 2>&1
n=$?
python3 -O -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prearmed_cleanup_can_precede_retired_owners_queued_down > /evidence/optimized.log 2>&1
o=$?
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$n" "$o" > /evidence/exit-status.json
cat /evidence/normal.log
cat /evidence/optimized.log
exit $((n||o))
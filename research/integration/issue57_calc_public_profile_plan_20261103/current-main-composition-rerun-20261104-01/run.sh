#!/bin/sh
set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py > /evidence/normal.log 2>&1
normal=$?
cat /evidence/normal.log
python3 -O -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py > /evidence/optimized.log 2>&1
opt=$?
cat /evidence/optimized.log
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
exit $((normal || opt))

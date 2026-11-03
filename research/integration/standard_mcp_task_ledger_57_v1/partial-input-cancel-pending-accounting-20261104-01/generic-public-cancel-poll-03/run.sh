#!/bin/sh
set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
AGENT_INTERFACE_RETAIN_PARTIAL_PENDING_COMPOSITION=/evidence/normal-retained python3 -m unittest test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_generic_compiled_partial_input_cancel_polls_same_call_in_ledger > /evidence/normal.log 2>&1
normal=$?
cat /evidence/normal.log
AGENT_INTERFACE_RETAIN_PARTIAL_PENDING_COMPOSITION=/evidence/optimized-retained python3 -O -m unittest test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_generic_compiled_partial_input_cancel_polls_same_call_in_ledger > /evidence/optimized.log 2>&1
opt=$?
cat /evidence/optimized.log
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
exit $((normal || opt))

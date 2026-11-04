set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_allows_release_to_finish_after_three_seconds runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_deadline_kills_blocked_worker_and_preserves_unknown runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown > /evidence/normal.log 2>&1
normal=$?
python3 -O -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_allows_release_to_finish_after_three_seconds runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_deadline_kills_blocked_worker_and_preserves_unknown runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown > /evidence/optimized.log 2>&1
opt=$?
cat /evidence/normal.log
cat /evidence/optimized.log
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
exit $((normal || opt))

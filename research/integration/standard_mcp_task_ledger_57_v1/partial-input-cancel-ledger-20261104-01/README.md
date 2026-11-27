# Partial-input cancellation joined to provider accounting

## Scope

This is a synthetic Windows/Fake X integration run on top of `main` commit
`7fec81be08a756979335a060008ac7588fc6b9e2`. It reuses
`OwnedProcessMCPTests.test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown`
and wraps its public MCP server with `RecordedPublicMcpCaller` and
`ProviderAttemptRecorder`.

One completed Fake App Server generation returned the registered Calc compiled
request. The server admitted the call, returned `pending` at the first-transition
cancel boundary, accepted one cancellation for that exact call ID, and retained
the terminal cancellation/result/close operations in the same ledger as
unlinked orchestration calls. The test asserts one provider attempt and one
compiled call, then refuses further compiled/input/recovery calls.

## Outcome

- Ledger reconciliation is complete: 1 model attempt, 14 tool calls, 30 raw
  request/response references verified against their SHA-256 digests.
- The provider attempt completed with reported usage of 61 input and 13 output
  tokens; the original compiled tool response was `pending` and remains distinct
  from later cancellation/results responses.
- The owner process was retired, but cleanup is `UNKNOWN` and
  `release_confirmed=false`. Task success remains unknown and replay is denied.
- Cancel, results, and close tool calls have no model-attempt parent. No second
  model attempt, compiled call, input call, or input-recovery call follows the
  uncertain post-input cancellation.

This records the fail-closed boundary. It does not prove that input release
succeeded, score the workbook effect, exercise a live Calc/provider, or complete
Issue #57. The synthetic attempt/token figures are not an efficiency comparison.

## Verification

Commands run with Windows Python 3.11:

- `python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_partial_input_cancel_accounting.py -v` — PASS, 1 test.
- Same command under `python -O` — PASS, 1 test.
- `python -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_prestarted_supervisor_allows_release_to_finish_after_three_seconds` — PASS, 2 tests; also PASS under `python -O`.
- `python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py -k test_cancelled_model_attempt_waits_for_worker_and_retains_cost_and_raw` — PASS, 1 test; also PASS under `python -O`.
- `python -m py_compile research/integration/standard_mcp_task_ledger_57_v1/test_partial_input_cancel_accounting.py` and `git diff --check` — PASS.

Raw Fake X files, provider-call files, App Server protocol bytes, recorder JSONL,
and reconciled events are retained beside this report. `SHA256SUMS` covers every
file in this packet except itself.


## Custody correction

The original manifest referenced six local test stdout logs that were not present in the committed packet. Those files are not claimed as retained and have been removed from the corrected manifest. The corrected manifest covers all 169 files present in this packet, excluding itself.

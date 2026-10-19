# Standard-caller guarded recovery through private Xvfb

This packet preserves four sequential runs for the added standard-MCP caller recovery discriminator. It separates three test/harness failures from the selected-test PASS and keeps every original Actions artifact ZIP byte-for-byte. The experiment used GitHub-hosted Linux Xvfb and a synthetic app; it did not use WSLc.

## Scope and result

Run [39251992654](https://github.com/Unjuno/agent-interface/actions/runs/39251992654), source head `5c4522fff6ceb373d0a6dd6cd3d1e0e37184077a`, passed the selected test `test_process_and_window_generation_flow_through_standard_mcp`. The workflow's `Run private Xvfb integration` step still failed because a separate existing XRes disconnect test raised a `JSONDecodeError` while reading its marker file. The selected test's result is `PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY`; this does not turn the overall job green.

The test injects a post-press acknowledgement `OSError` and a one-shot automatic-release `OSError`. The synthetic app and a separate X client first observed the key held; the explicit `interface_guarded_recover_input` call then returned a verified release, the app observed KeyRelease, and an independent keymap read found the key up. Recovery took 4.894443 ms in this run. Review invalidated the old alias, and a freshly minted alias produced the next synthetic application property `[3]`, independently observed. The runtime `task_success` field remained `null`.

This is one scoped Xvfb caller result. It does not establish release through indefinitely blocked X-server/backend I/O, a universal physical-release deadline, MAP01 or game success, native Windows/XWayland behavior, or end-to-end efficiency. Do not treat the synthetic application property as a real task score.

## Conditions and custody

The final raw JSON records the exact source observation, target XRes PID and process-generation digest, Xvfb binary/version and hash, keycodes, event sequence, independent reads, monotonic timestamps, runtime release receipts, and cleanup. The conditions summary is in [`conditions.json`](conditions.json). `runs.csv` records each workflow head, result, artifact ID, and reason. `SHA256SUMS` covers every preserved ZIP, JSON, and PNG.

The GitHub artifact ZIP digests were checked against the API-provided SHA-256 before extraction. The ZIPs remain in `raw/run_<id>/` alongside the unmodified extracted JSON and observation PNG. No failure artifact was replaced or rewritten.

## Sequential run ledger

| Run | Source head | Selected-test result | Overall private-Xvfb step | Interpretation |
|---|---|---|---|---|
| [39249700568](https://github.com/Unjuno/agent-interface/actions/runs/39249700568) | `eded2f39270d19b975c0aae3359e6a7696391ae7` | FAIL before fault injection | FAIL | Fixture alias `recovery-b` was refused by the documented alias grammar. No input was dispatched. Harness input error, not a release result. |
| [39249983453](https://github.com/Unjuno/agent-interface/actions/runs/39249983453) | `44b09d2a348f13eae2a463082c8146f593c747c8` | ERROR | FAIL | Test referenced `asyncio` without importing it. No recovery result. |
| [39251551454](https://github.com/Unjuno/agent-interface/actions/runs/39251551454) | `1a3117db5d3b0631a6dc29350ce7f15ea987392c` | FAIL | FAIL | Assertion expected cancellation-style `session.interrupted_execution` for a normally returned `execution_failed` call. Raw output instead showed the returned execution receipt, `recovery_required=true`, and retained key obligation. The test had not reached explicit recovery. |
| [39251992654](https://github.com/Unjuno/agent-interface/actions/runs/39251992654) | `5c4522fff6ceb373d0a6dd6cd3d1e0e37184077a` | PASS: `PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY` | FAIL in a separate XRes marker-file reader | The selected test completed all stated fault, held-state, explicit recovery, app effect, independent keymap, stale-alias, and fresh-action checks. The unrelated suite failure is retained separately in the job log. |

The first three runs are retained as method/test failures and were not recoded as scientific negatives. The final run is a scoped positive result, with its suite-level failure stated separately.

# R10 independent assessment — held native effect and cancellation

## Result

**Native recovery, key-up, and completion before the configured deadline were established.** The original `RESULT.json` remains unchanged and reports `FAIL_OR_UNKNOWN`; its `success_gate` reads the immediate `interface_cancel` response (`pending`, `release_confirmed=false`) rather than the terminal dispatch and retained cancellation result. The independent adjudicator `assess_attempt.py` reads the preserved evidence and exposes the later state without rewriting the original record.

The preserved `dispatch-after-cancel.json` raw report has `result.status=recovered`, `release_confirmed=true`, `task_success=null`, and `replay_allowed=false`. `results.json` retains both action and cancellation as `recovered`, with cancellation `release_confirmed=true`, producer exit code `-15`, and phase `recovered`. The independent native observation in `RESULT.json` reports the same target generation and `shift_down=false`; during the hold it observed `shift_down=true`. This confirms that an accepted SHIFT-down effect was followed by observable key-up after supervised recovery. No task-success claim is made.

## Boundedness and limits

The recovery helper's cleanup deadline was 530007296000000 ns, exactly 3,000,000,000 ns after hold entry at 530004296000000 ns. The final completion timestamp was not persisted, so exact recovery latency is unavailable. However, on this pinned source (`16dfc8843564d3768a767aaa85b165fd3c8c0cd3`), `OperationOwner.recovery_completed` sets status to `recovered` only when its monotonic clock is strictly before `cleanup_deadline_ns` (`runtime/guarded_win32_v1/operation_owner.py:397`, status decision at line 416). The recovery helper also rejects a late receipt before observer/readback (`runtime/guarded_win32_v1/process_cancellation.py:331`). Thus the retained terminal `recovered` result, paired with the independent neutral readback and release receipt, proves it passed the configured deadline gate. The focused local cancellation suite passed 12 tests. `cancel_elapsed_ms=0` still measures only the initial nonblocking cancel call and is not the recovery latency.

The fault injection holds the producer **after the native SendInput call returned**. It does not stall inside the Windows API and does not prove bounds for arbitrary platform-I/O hangs. The in-process MCP function path was used; this was not a stdio transport test. This establishes one recovery completion inside the configured bound, not a bounded-reliability estimate across repeated trials. No WSLc allocation, Docker operation, replay, task success, or target-generation change occurred.

## Evidence

- `RESULT.json` — original run record; preserved unchanged, including its preliminary gate.
- `dispatch-after-cancel.json` — later terminal dispatch receipt.
- `results.json` — retained action and cancellation states.
- `cancel.json` — immediate asynchronous `pending` response.
- `observe.json` and `observe-1.png` — preflight/observation evidence.
- `close.json` — session close receipt; its `release_confirmed=false` is separate from action/cancellation recovery and is not treated as release proof.
- `run_blocked_native.py` — fault-injection harness.
- `assess_attempt.py` — read-only strict adjudicator; run with `python assess_attempt.py`.

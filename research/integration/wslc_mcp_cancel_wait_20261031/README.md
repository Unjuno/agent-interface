# Guarded MCP cancellation during a fixed wait

Main base: `eed7265d6bfa9dccd458d533de91cb96e77f6256`. The guarded backend used to sleep until the full wait or lease deadline without checking cancellation. In the before-fix a02 trial, cancellation was acknowledged during a 2 s wait, but the wait completed and execution ended 1572.869 ms after the request. The failure is recorded at the next operation with effect unknown.

The patch checks the existing cancellation state during guarded waits, with sleep slices of at most 10 ms, retaining the original lease deadline and release path. This is cooperative polling, not a real-time guarantee or a way to retract input already sent.

| Allocation | Source | Condition | Observed outcome |
| --- | --- | --- | --- |
| a01 | main | no cancel | wait and later operation completed |
| a02 | main | cancel | wait completed; next operation failed; release verified |
| a03 | patched | no cancel | wait and later operation completed |
| a04 | patched | cancel planned | STALE refusal before entry input; no MCP cancellation trial |
| a05 | patched | cancel | wait interrupted; later operation absent from completed operations; release verified |

In a05 execution ended 5.824 ms after the recorded request; this is one observation, not an SLA or statistically reliable benchmark. In every completed trial Calc was SIGSTOPed before the save, its file was still blank at the mid check, and after SIGCONT the previously sent save produced A1=731 and A2=864. Cancellation therefore did not undo already dispatched input or its later effect. The execution receipt retains `failed_op_effect` as unknown. All completed trials observed neutral keys/buttons; a04 was refused before input. The initial pending response is only a response wait, and all polling used the same call ID without replay.

Each zip contains inputs, runner, conditions and top-level raw outputs, including screenshot and file snapshots. Nested receipt journals are retained locally and represented by hashes and sizes, rather than published raw. `python audit.py` checks the recorded distinctions. The test uses a private Xvfb and Calc on WSLc with one CPU and no network; it does not establish MAP01 behavior, unrestricted scheduling latency, model performance, or cancellation of effects already queued in the application.

Local verification: `python -m unittest runtime.guarded_x11_v1.test_deadline runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_target_queries` and the same command under `python -O`: 84 tests each, pass. The new deterministic test failed before the patch and passes afterwards.

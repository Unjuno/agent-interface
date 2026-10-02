# T3V shared-clock v6 runner boundary — result

Issue: [#6261](https://github.com/Unjuno/agent-interface/issues/6261)
Parent: #6252 / #59. Preserve the earlier T3U STOP_CONSTRUCTION_GATE_MISMATCH_RAW_INCOMPLETE and PR #6254 unchanged.
Allocation: MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3V-20261002-01
Frozen main: 4cf0a3dfde1219671b671bf0a9079a11dcb2e159
Candidate source commit: a8652bee5b52dfb0d06c97aa2e86afdaadefb6e0

## H / T / D / C / U

**H.** Exact v6 _run_arm, Executor-v10 and Lease, sharing a monotonic clock, should show (A) a timer crossing followed by matched cooperative cancellation while the Lease remains live; (B) Lease expiry and verified release during a longer blocked planner-clock call, followed by an unmatched late cancel. Planner-window end must be the exact clock return. Executor's terminal semantics are preserved: normal backend return after observing cancellation is completed; deadline expiry is expired.

**T.** The frozen source manifest is in FREEZE.json; its three Git blob IDs and SHA-256 values matched main. Host CPython/macOS arm64 executed the exact main v6 runner, Executor-v10 and Lease Git objects through a fake session/backend, with only the Executor Lease-constructor seam injecting the common monotonic clock. No shared container lease was available, and the issue permits this no-external-effect host path. No game, GUI, model/provider, network, GPU, physical input or live application was used.

Exact execution environment: Python 3.14.5, macOS 26.6.2, arm64.

Construction command, exactly once:

    python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/run_t3v.py --construction

It exited 0; construction row, stdout and stderr are retained. Then the formal candidate command ran exactly once and exited 0. The separate raw-only auditor ran exactly once after candidate success and exited 0. Retries: 0. Raw candidate and auditor outputs are retained; the auditor does not import the candidate.

## Observed result

Construction: PASS. Exact runner planner end equaled returned clock sample; cancel was matched and observed; verified release occurred; exact Executor terminal was completed.

| Case | Clock-return boundary | Cancellation / terminal | Release |
|---|---|---|---|
| A — timer 600 ms, clock delay 400 ms, lease 2,000 ms | Planner end exactly equaled return. | Cancel matched; backend observed it 29.333 ms after request; terminal completed. | Verified; 422.424 ms after timer expiry; 36.166 ms after cancel request; 55.791 ms after clock return. |
| B — timer 600 ms, clock delay 1,600 ms, lease 1,500 ms | Planner end exactly equaled return. | Lease terminal expired; later runner cancel was unmatched and unobserved. | Verified 0.741 ms after planner-start + lease deadline and 740.876 ms before clock return. |

The raw-only audit reports PASS_AUDIT, two cases, zero errors. Its input is the byte-retained raw trace plus frozen manifest. Candidate's executable gates passed in both cases.

## Conservative D adjudication

The Issue and frozen Plan say case A's verified release is “within 50 ms after clock return/cancel,” without naming one timestamp as the threshold origin. The candidate and independent auditor code frozen before execution use cancel_requested.requested_ns as the origin, and the observed 36.166 ms satisfies that executable gate. The stricter literal clock-return origin yields 55.791 ms, exceeding 50 ms by 5.791 ms.

Because the prose criterion does not resolve this distinction, the overall result is **HOLD_D_CLOCK_RETURN_BOUND_AMBIGUOUS**, not an unqualified scientific PASS. The candidate and audit PASS statuses are retained as raw sub-results and are not relabeled. No post-hoc gate edit or rerun was made. Any follow-up must freeze one exact origin prospectively in a distinct successor allocation.

## Scope and uncertainty

This is a fake-session/fake-backend runner boundary check only. It does not measure natural RPC latency, OS process scheduling, X11 behavior, real MAP01 control, task effect, physical occupancy, safety/efficacy, human tempo, production behavior, or completion of Issue #59. The shared-clock hypothesis's two specified event orderings were observed, but the ambiguous latency threshold prevents promoting the frozen D as written.

## Reproduction record

The source tree is frozen at FREEZE.json; generated outputs are hashed in SHA256SUMS. Historical commands and first outcomes are evidence, not authorization to rerun this one-shot allocation:

    python3 -m unittest discover -s research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01 -p 'test_*.py' -v
    python3 -m py_compile research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/run_t3v.py research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/audit_t3v.py research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/test_t3v.py
    git diff --check

Construction unit tests: 7/7; Python compilation: PASS; pre-freeze git diff --check: PASS. Candidate and auditor stdout/stderr, all raw rows, and the exact executed environment metadata are included in results/.

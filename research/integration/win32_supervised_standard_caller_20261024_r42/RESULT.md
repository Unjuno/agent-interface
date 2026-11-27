# R42 result — 2026-10-24

Status: phase 1 PASS_SCOPED (strict release gate 11/11); paired overall FAIL_OR_UNKNOWN (combined audit 3/12). Raw evidence and outputs are sealed in `SHA256SUMS`.

The input-free preflight passed all 12 checks against main `e6192a4294aac0d94d51e75b24583216c718d654`. Both CUA receipts matched the unique fixture windows, and independent `GetForegroundWindow`/owner-PID checks matched each window before the marker was written.

Phase 1 passed the frozen release gate: one dispatch and one cancel; the exact call was `running` before cancellation; callback hold after cancel was 1,262.5311 ms against a 1,250 ms requirement; 80 same-call result polls completed; an independent same-generation sampler recorded Q-up after the injected key-up return; the producer retired, hook exited, fixture exited with code 0, session closed, and prior foreground was restored. No phase-1 task_success is claimed.

The strict gate authorized phase 2. Its unique fixture became ready and the CUA marker was written, but the phase-2 harness raised `NameError: name 'user32' is not defined` in `wait_for_user_foreground` before it consumed the marker or made any public API call. The phase-2 fixture event log contains only `ready`; the effect file and oracle receipt are absent; `steps` is empty; fixture exit code is 0. Thus no phase-2 input or task effect occurred, and task_success remains null. The paired question did not pass. Do not rerun R42; fix the harness in a separately frozen attempt.

`audit_r37.json` is the original combined-audit output path produced by the frozen script; `audit_r42.json` is a byte-identical named copy for packet indexing. Both are preserved. The frozen audit script has the same output-path naming defect and is not represented as having written `audit_r42.json` itself.

This native-PC result does not establish WSLc allocation eligibility, WSLc GUI behavior, MAP01, matched efficiency, broad reliability, or real-application transfer.

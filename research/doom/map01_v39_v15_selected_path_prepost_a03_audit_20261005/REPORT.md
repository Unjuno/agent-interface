# A03 result — retained V39/V15 lost-key audit

## H — Hypothesis
A corrected independent raw-only auditor can separate input admissions from release transitions, recompute per-key status from samples, detect a simulated lost SPACE KeyRelease at post-sample, and verify terminal cleanup fails closed while keycode 65 remains held.

## T — Test
One audit-only run of the byte-frozen A02 candidate stdout, A02 PRE-RUN and original A02 AUDIT. Candidate/runtime invocations 0; auditor invocation 1; retries 0. Seven preregistered mutation controls challenge the baseline checks. The original A02 audit is an immutable historical input, not replaced.

## D — Data and outcome
PASS_AUDIT_V2_LOST_RELEASE_DETECTION_SCOPED (auditor exit 0): 50/50 baseline checks and 7/7 mutation controls rejected. All three input SHA-256 values match the frozen preregistration; see RESULT.json and SHA256SUMS.txt. The normal case has an empty post-sample and successful close. In the simulated lost-SPACE case the UP is suppressed, keycode 65 remains down at post-sample, is classified STILL_DOWN_AT_POST_SAMPLE, and terminal close fails closed with the key retained. A02 audit status remains FAIL (21/32) and is not edited.

Docker execution STOP: daemon image listing encounters containerd content-store `operation not supported`. The authorized host standard-library fallback ran via an in-memory adapter because the workspace could not allocate temporary files (`No space left on device`). This is a runtime deviation recorded in RUN_RECORD.md; no container execution is represented as successful.

## C — Claims and boundaries
Supported: this auditor catches the specified simulated lost-key and admission/release distinction in the frozen fake-X trace, and rejects the seven tested mutations.

Not supported: real X11 behavior, physical key state, application/game effect, useful feedback, latency, recovery efficacy, threat response, or gameplay. XSync denotes server synchronization only. This is not evidence of end-to-end live-game control.

## U — Unresolved / next step
Use this scoped result to repair the audit contract lineage without rewriting A02. The main #59 gate remains open: assign an authorized live-game lane and independently measure timely per-key release, useful feedback before model return, bounded recovery, ammo/progress, and terminal outcome. Treat this PR as review-required and draft until independent review confirms the artifacts and scope.

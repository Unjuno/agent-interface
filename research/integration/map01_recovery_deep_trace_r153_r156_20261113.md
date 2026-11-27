# MAP01 expiry recovery and caller failure R153–R156 (2026-11-13)

## R153/R154 prior checkpoint

R153 stopped before input at the stale foreground gate. R154 passed one native public compiled-supervised MAP01 attempt: the expiry-to-neutral outer QPC bracket was 10.0353 ms (fixed limit 20 ms), same-generation neutral readback and a two-second horizon passed, ammo independently changed 50→49, and scoped demo adjudication found no recorded forward command. Its helper exchange-to-recovery interval was attributed at 1.1148 ms. This single run did not explain R151's 7.9521 ms tail.

## R155 fresh replication

R155 passed the same scoped public action/task/release/demo gates once. Its outer expiry bracket was 12.03 ms; W remained down 10.0008 ms after expiry. The joined QPC stage trace attributed 1.3152 ms exchange-entry to helper recovery entry: lock wait 2.6 μs, lock-to-send 27.8 μs, send 1.1253 ms, send-return-to-helper-receive 109.9 μs, and receive-to-recovery 40.1 μs. It did not reproduce R151's tail. This one replication does not estimate reliability or resolve the outlier.

## R156 fresh attempt

R156 used frozen main `a1fc6d32d50ea9b097caca225d8f67044e3db141`, one owned fresh process, one compiled dispatch, the unchanged 20 ms limit, and no retry. The expiry sampler verified a 10.1136 ms outer bracket. W stayed down 8.0001 ms beyond the serialized deadline; the first fully post-deadline up read was 9.2503 ms after expiry. Recovery stage traces recorded a cancellation request, release accepted by the helper for the bound generation, and a later independent W-up read.

The composed attempt **failed/unknown**. The runner raised `FileNotFoundError` while unconditionally reading `expiry-held-w-samples.json`; this R156 code path wrote `expiry-boundary-key-samples.json` instead. The public server reported `PermissionError` resolving the pending dispatch; dispatch status was uncertain, action-level release remained unconfirmed, the task-effect oracle did not run, and ammo/task success are unknown. The initial release API receipt reported busy while recovery remained pending. After the attempt, the owned target received a normal close request and exited; no forced termination was used.

The single post-run W-up sample is not a verified two-second horizon. The demo ending with the player killed is suggestive only, so R156 is **not** classified as a pass for delayed-operation exclusion. Preserve the conservative task/replay semantics and do not replay this attempt.

## Decision and next step

R155 did not reproduce the trace tail. R156 separately verifies the expiry boundary and helper-side release acceptance but exposes a concrete caller evidence-join bug and an unresolved public release/task result. No runtime behavior change is justified by these samples. Fix the runner's held-input artifact join and ensure exception paths keep the session alive long enough to obtain same-generation release readback plus the full late-input horizon; add a regression for a missing held-sample artifact. Then repeat only in a new preregistered attempt, without changing the 20 ms gate or accepting `UNKNOWN` as success.

## Provenance

R156 packet final SHA-256 manifest: `8ee725a06356549d860ed8c0d74f5164582e1ac1ce6ee1c74bb62719c47e084f` (64 manifested files, all readback verified). Conditions and private raw remain in task-local packet `map01_native_windows_deep_trace_20261113_r156`. R153/R154 details and manifest hashes remain in git history and the preceding checkpoint.

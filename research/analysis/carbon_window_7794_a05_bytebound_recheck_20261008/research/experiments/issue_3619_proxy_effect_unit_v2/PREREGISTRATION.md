# Issue #3619 — proxy effect-binding formal-02

Successor to #3610's immutable one-shot startup STOP. Allocation ID: `issue3610-proxy-effect-unit-formal-02`; fresh path, source freeze, and output. This is not a retry under #3610.

## H/T/D/C/U

- **H:** Four authority-neutral presentation arms can complete the same non-destructive GTK counter operation while stale, replaced, unavailable, ambiguous and macro-failure conditions refuse; an acknowledged no-effect click yields instead of reporting success.
- **T:** One fresh GTK3/Xvfb fixture per row; four arms × seven cases = 28 rows. The seven cases are positive, no-effect, stale version, target/process replacement, unavailable target, ambiguous duplicate targets, and macro failure. Freeze source, preregistration, runner/auditor, image, source/metadata mounts, and evidence path. Before formal, run a fail-closed shell launcher (`set -euo pipefail`) which validates the exact image ID/platform, all mounted source/freeze/preregistration hashes, the `wait_state(pid_hint=...)` call-signature regression test, and an empty fresh output path. The launcher must exit before the runner if any check fails. Formal runs once, no retry, in OrbStack Linux/arm64 with network none, read-only root/source, and fresh writable output.
- **D:** `PASS_PROXY_BINDING_EFFECT_UNIT` only if all 28 unique rows complete; positive rows independently verify exactly 0→1; all six negative controls per arm cause zero task effects and refuse/YIELD (the explicit no-effect case may emit a click but must yield); source/target/version binding, acknowledgements, release, process/socket cleanup, audit and hash closure reconcile. Any unsafe task effect is FAIL; startup/evidence gap STOP/HOLD. No arm winner.
- **C:** Same fixture/task/geometry/schema/executor and controls as #3610. Only new allocation identity/output, corrected `wait_state` signature, source-mount manifest boundaries, and fail-closed launcher differ.
- **U:** No model/human comparison, usability, token/cost, latency benefit, general GUI safety, production authority, or integrated desktop claim.

## Immutable predecessor

#3610 formal-01 is `STOP_AFTER_FIXTURE_START_BEFORE_STATE_OBSERVATION`, 28/28 startup errors, zero emissions/effects, and has an independently retained raw hash/row hash list. It is not changed by this successor.

# Formal-01 operation log

- Allocation: `issue3610-proxy-effect-unit-formal-01`; one formal runner invocation, zero retries.
- Pinned image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64; network disabled; read-only root; source/freeze/manifest mounted read-only; fresh evidence output mounted read-write.
- The raw matrix contains exactly 28 distinct arm/case row records. All 28 start one Xvfb and one GTK fixture. Every row then raises `TypeError: wait_state() got an unexpected keyword argument 'pid_hint'` before state resolution. No row captured an initial state or emitted input; all emission counts and input acknowledgements are zero.
- Fixture processes were terminated/reaped (exit `-15`), Xvfb processes exited/reaped (exit `0`), and all X sockets disappeared. No task-effect inference is permitted.
- Raw JSON SHA-256: `4cddcbe9f3cb9e686fcf8dd183be7b997de2357e53f1113294a410e1982d7dc8`.

## Pre-formal integrity-gate failure

The separate read-only hash preflight was invoked with `/src` bound to the source-only `src/` directory while `SOURCE_MANIFEST.json` also included the parent `PREREGISTRATION.md`. It exited non-zero with `FileNotFoundError: /src/PREREGISTRATION.md`. The orchestration did not stop on that non-zero result and continued to the formal runner. This is an operator control failure, preserved explicitly; the formal matrix was nevertheless consumed once and cannot be retried under this allocation.

## Classification

This is a setup STOP, not a proxy safety result. The original runner, freeze and formal raw remain immutable. A new successor allocation is required to correct the `wait_state` signature and integrity-preflight fail-closed boundary.

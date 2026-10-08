# A03 run record

- Frozen base: current main `e561b25b700680df4e6ffd2b92faf1dde1682ef7`.
- Runtime: CPython 3.14.5, macOS arm64; stdlib-only, no isolation/resource enforcement.
- Probe invocation: one, exit 0, `PASS_PAIRED_EPOCH_FAIL_CLOSED`, 10/10 expected cases.
- Independent auditor: one, exit 0, 44/44 checks.
- Formal live allocation: 0; retries: 0.
- No full controller/runtime integration, game, model, GUI, OS input, actual cover, cancel/release, task effect, or live threat exposure.
- No Docker daemon probe in A03; A01's exact OrbStack cached-blob failure remains the known environment limit.

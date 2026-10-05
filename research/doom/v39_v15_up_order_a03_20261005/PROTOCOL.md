# A03: synthetic normal release-batch UP-order trace

Successor to A02, which is preserved as STOP after the candidate started but before its first DOWN because the test-only parent backend omitted the step telemetry context. A03 fixes only that parent-shim contract: it sets and clears `_input_event_context=(identifier,index)` around the raw input sequence. The target and A02 candidate test logic otherwise remain unchanged. No candidate has started.

## H/T/D/C/U
- H: Exact frozen release-batch backend v1 with exact transition-owner v4/v3 and input-owner v12/v10 sources, two distinct keys held under one lease: reverse-order XTest KeyRelease calls, no query_keymap between them, then the backend's single input_state call; two emitted rows bind to matching owner-thread receipts and final owned_keycodes is empty.
- T: One execution through FakeXlib. A minimal typed-backend-v2 parent shim drives two DOWNs and reverse UPs while honoring the parent telemetry-context contract. No error branch/retries, real X server, app/game/model, or OS input.
- D: Ordered fake trace, owner records, backend-published release rows, post-batch owner state, final synthetic key set. All executable/source SHA256 values are frozen in FREEZE.json; the runner verifies them before starting the candidate.
- C: Five executable source snapshots from main 69dd261430cb1ed875f5a76411c4a2a54777c114; pinned Python 3.11.9 linux/arm64 digest; network none, read-only root, bounded tmpfs/CPU/memory; explicit FakeXlib and parent shim.
- U: Does not cover V39 CLI selector/V15 session wrapper, real X11, production startup, live input/task effect, useful feedback, latency, recovery, or permission/lease availability. No live allocation is implied or consumed.

## One-shot protocol
Verify every package SHA256 with frozen runner.py, then run runner exactly once. It starts candidate once and auditor exactly once only if valid raw JSON is produced. Any pre-start setup/hash failure is STOP; candidate start forbids rerun. Adjacent release-error/non-neutral dimensions remain excluded because of #7847/#7858.

## Decision gate
PASS only if independent audit verifies two distinct DOWNs, reverse UP injections, zero keymap queries between explicit UP injections, backend input_state call after both UP calls, two matching identity-bound owner receipts, completed rows with verified empty post-batch ownership, and empty final synthetic keys. Otherwise FAIL (counterexample) or STOP. Any PASS is synthetic component/call-order evidence only.

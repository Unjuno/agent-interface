# A04: compact, independently audited synthetic release-batch UP-order trace

Successor to A03, which preserved the observed candidate trace but its auditor counted admission telemetry as release rows, and the desktop truncated the oversized JSON stdout. A04 emits only the two release-transition projections while retaining the complete ordered call trace and owner receipts, keeping raw JSON compact enough for the configured output capture. Candidate and auditor are frozen before run.

## H/T/D/C/U
- H: Exact frozen release-batch backend v1 plus transition-owner v4/v3 and input-owner v12/v10 sources, for two distinct keys and one lease: reverse-order XTest UP, no keymap query between UPs, then backend input_state; two identity-bound receipts and empty final synthetic ownership.
- T: One FakeXlib normal-path execution. Minimal typed-backend-v2 parent shim drives two DOWNs and reverse UPs with the required step context. No error branch or retry; no actual X server, application/game/model, or OS input.
- D: Compact raw JSON includes complete ordered call trace, exactly the two event-filtered release rows, owner records, post-batch state, final synthetic keys and scope flags. Independent auditor checks identities/order/sample/state. Runner validates candidate/auditor/runner/source SHA256 values before candidate start.
- C: Exact source snapshots from main 69dd261430cb1ed875f5a76411c4a2a54777c114; pinned Python 3.11.9 linux/arm64 image; network none, read-only root, 1 CPU/512 MiB and bounded tmpfs; explicit FakeXlib and parent shim.
- U: Synthetic component/call-order only; not V39 CLI selector/V15 session startup, real X11, live input/task effect, feedback, latency, recovery or lease availability. No live allocation.

## One-shot protocol
Run frozen runner exactly once after package hash verification. It launches candidate once; if raw JSON is emitted, launches auditor once and outputs compact combined result. Any setup/hash error before candidate start is STOP; after candidate starts, no rerun. Adjacent error/non-neutral dimensions from #7847/#7858 remain excluded.

## Decision gate
PASS only if independent audit confirms two distinct DOWNs, reverse UP order, no keymap query between explicit UP injections, backend input_state after both UP returns, exactly two release rows with matching per-key owner receipts/owner identity/token, completed batch and empty post-batch/final synthetic key state. Otherwise record FAIL or STOP. PASS is synthetic construction evidence only.

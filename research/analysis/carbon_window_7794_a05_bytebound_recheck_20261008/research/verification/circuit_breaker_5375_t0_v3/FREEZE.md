# Issue #5375 T0-v3 — half-open races, misclassification, fallback boundary

Allocation: `circuit-breaker-5375-half-open-boundary-20260930-01`
Branch: `research/circuit-breaker-5375-boundary-v3-20260930`
Path: `research/verification/circuit_breaker_5375_t0_v3/`
Frozen current main: `cf8ad3d1a675af9e64c1be356d03e35699548b33`

## H / T / D / C / U

**H.** A generation-bound half-open breaker that admits at most one probe per circuit generation, requires current non-contradictory verified evidence to close, and constrains fallback to typed non-authoritative outcomes will preserve the circuit/safety boundary under the three gaps left by #5375 T0-v2: misclassification, stale/duplicate half-open completions, and fallback misuse.

**T.** One deterministic discrete-event replay over nine frozen cases: valid recovery; open timeout; semantic contradiction mislabeled transient; late prior-generation PASS; duplicate concurrent probe requests; containment fallback; attempted action-authorizing fallback; stale evidence; expired probe. Candidate receives only each case, not the literal expected result. A separate literal auditor checks raw. Eight host construction tests run before one T0 invocation. No verifier is dispatched.

**D.** PASS requires exact candidate/oracle agreement on all nine cases, no more than one accepted half-open probe in the duplicate-request case, all stale/contradictory/expired results refused to close the circuit, all fallback paths non-authoritative, and a clean independent audit. Any action authority or race-induced close is FAIL.

**C.** This is a deterministic state-machine replay, not a concurrent-thread scheduler. It holds the sequence and oracle fixed; no performance comparison with the T0-v1 policies is repeated. The prior T0-v1/v2 issue comments remain unchanged.

**U.** Does not establish runtime synchronization, cancellation, threshold calibration, observability of semantic misclassification, correlated failure resilience, fallback correctness, latency, task/GUI safety, or production resilience.

## Execution boundary

Candidate blob SHA-1: `f58c822487a65b37a7832278c5eb1e39a64ffd39`
Corpus blob SHA-1: `db1ed31c93ebb92521a0a5d7c48d5f0012dc9747`
No Docker CLI is permitted by the current #5085 coordination note until owner release and exact assignment. This tiny deterministic CPU replay is host-only with source streamed from GitHub readback into CPython `-B`; no local outputs, model, GPU, network, GUI/input, dispatch, or external effects. Container execution is explicitly not claimed.

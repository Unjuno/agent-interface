# #5941 T0 — peer-verdict exposure and independence credit

**Status:** frozen method-construction experiment; no LLM, GUI, task-effect, or verifier-product result.

## H / T / D / C / U

- **H:** In a three-verifier quorum, a later first-pass verdict that had prior peer-verdict exposure must not be counted as an independent vote. Incomplete, invalidly committed, or capture-inconsistent exposure history yields UNKNOWN_INDEPENDENCE.
- **T:** Enumerate all 2 truth states × 8 binary verdict vectors × 8 time-respecting peer-exposure graphs (three possible directed edges V1→V2, V1→V3, V2→V3): 128 rows. Compare ordinary vote counting with exposure-aware counting. Independently recompute the exact case inventory and outcomes from raw receipts. Exercise the planted counterexample and three fail-closed provenance controls.
- **D:** METHOD_PASS_SCOPED only if all 128 unique rows match an independently implemented raw-only oracle, no exposed receipt contributes to the independent set, the known wrong-majority witness changes from INCORRECT_QUORUM_PASS to NO_QUORUM, three incomplete/invalid/mismatched-history controls return UNKNOWN_INDEPENDENCE, and the auditor rejects a dropped row and a result mutation. Any mismatch is FAIL; absent authoritative capture is outside this simulator and remains UNKNOWN.
- **C:** The simulation assumes the receipt's history/commitment/capture flags are produced by a trustworthy call-bound capture layer. Static shared observation/model failure domains are not removed; this test isolates dynamic peer-verdict exposure only.
- **U:** This establishes a finite accounting rule, not that real agents copy peers, that the capture flags can be authenticated, or that blinding improves verifier accuracy/availability. Identical evidence may cause correlated errors. T1 needs frozen non-live effect traces and a model study; no action authority is granted.

## Frozen scope

Issue #5941; additive path `research/analysis/peer_verdict_exposure_5941_t0_v1/`; allocation `PEER-VERDICT-EXPOSURE-5941-T0-20261001-01`; base main `e1ebee404930401665c1fef64022b0ad3c373793`. CPU-only deterministic simulation. No GPU, container, model/provider, GUI, network, live task, or shared runtime change. One construction-test run before freeze; candidate once after source freeze; separate raw-only auditor once if candidate exits 0; no retries.

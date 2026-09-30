# Issue #5348 T1 — causal cut with asynchronous channel evidence

Allocation: causal-cut-5348-t1-20260930-01
Branch: research/causal-cut-5348-t1-20260930-01
Path: research/analysis/causal_cut_5348_t1/
Frozen main: 8265c1a19cbba7ab0f5316f27bdb59509269399d

## H / T / D / C / U

**H.** A vector-clock cut check plus explicit in-flight channel accounting distinguishes a causal-consistent evidence cut from individually fresh but incoherent records in a bounded asynchronous two-stream model. It preserves complete reordered and independent concurrent cuts while classifying receive-without-send, missing/dropped delivery, missing metadata, and conflicting duplicate delivery as incomplete, UNKNOWN, or contradictory rather than authority-bearing.

**T.** Exhaustively enumerate every process-prefix cut over three frozen DAG fixtures: a two-way action/receipt exchange with an independent local event; two sends delivered in reverse order; and independent concurrent local observations (25 prefix cuts total). Add six controls: explicit in-flight, dropped ACK, missing channel, missing causal metadata, identical duplicate, and conflicting duplicate. Compare per-record freshness-only admission with vector-clock candidate classification. A separately authored graph-parent auditor recomputes all row labels. All records are synthetic and marked individually fresh; no external effects.

**D.** PASS scoped only if independent auditor exactly reconstructs all 25 cuts and six controls; no non-CONSISTENT row is certified; at least one complete cross-stream bundle is preserved; receive-without-send never confirms an effect; missing channel/metadata and dropped ACK fail closed; identical duplicate delivery does not create extra logical evidence; conflicting duplicate is contradictory. Any disagreement is FAIL/UNCERTAIN and retained without retry.

**C.** If source-local causal parents or bounded channel state cannot be observed, return UNKNOWN/INCOMPLETE rather than inferring coherence. Single-source actions may use local evidence without a global cut. Existing freshness and action admission remain independent hard gates.

**U.** Synthetic deterministic traces only. No GUI/backend events, real observer instrumentation, clock synchronization, performance, model, runtime, or product claim. A consistent cut establishes causal compatibility, not truth, freshness, effect success, or authority. The fixture corpus is finite and hand-specified; it does not cover arbitrary stream count or hidden channels.

Terminology follows the distributed-snapshot safety condition: a cut cannot include a receive without its causal send. See Chandy & Lamport (1985), DOI 10.1145/214451.214456, and Lamport (1978), DOI 10.1145/359545.359563.

## Frozen source Git blob SHA-1 identities

- causal_core.py: 302595c32bdfffc88b54c78c3fc4f54ac4e5c03e
- run_t0.py: 6cfc154d4d15e35db28f1496b9a45616dd5721fc
- test_core.py: 05b20b25e78d1dd31e2fc0872ca5bc5030268d51
- audit_t0.py (independent, frozen pre-run): a79b9a918a9b7971dcf903fd632b5a5960f6c7b3

## Source files

- Candidate: causal_core.py
- Runner: run_t0.py
- Construction suite: test_core.py
- Independent graph oracle (frozen before formal run): audit_t0.py

Formal run is one local Python 3.11.9 host invocation from exact GitHub readback source strings, python -B; output remains in memory. No file is written locally. Container/GPU/model/network/GUI/action use: none. Container is not used because current #5085 explicitly forbids Docker/OrbStack CLI until exact task/allocation/window assignment. C: free space is 0 bytes.

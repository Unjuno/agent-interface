# Issue #5970 — recovery reachability with causal-cut evidence T0

## H / T / D / C / U

- **H:** Coupling a staged recovery dependency witness to a causal-consistent evidence cut removes false `READY` outcomes that graph reachability plus individually fresh records admits, without rejecting a valid same-epoch recovery path.
- **T0:** Freeze six finite three-stream traces (root query, surface/focus+lease, invalidation/release): valid same-epoch positive; cross-epoch invalidation; delayed release still in flight; missing causal parent; reset midway; and genuine alternative root from the wrong epoch. Enumerate all prefix-/causality-closed cuts, compare graph-only with graph-plus-cut, and independently enumerate expected legal cuts in a separate auditor. No model, GUI, user data, external service, or actuation.
- **D:** Scoped PASS only if the positive control is reachable and authorized, graph-only falsely admits the five adversarial cases, the cut-aware candidate denies all five as `CONTRADICTORY`, `INCOMPLETE_IN_FLIGHT`, or `UNKNOWN`, and candidate cut counts equal the independent enumeration. Any false READY or rejected positive is FAIL; unrepresented provenance is UNKNOWN, not success.
- **C:** An atomic, single-source bootstrap may make cut validation redundant; this fixture does not establish how often real recovery combines asynchronous sources or the latency cost of coherence metadata.
- **U:** A consistent cut establishes causal compatibility only—not semantic truth, root independence, authorization, or external effect. No runtime efficacy or user benefit is measured.

## Frozen one-shot protocol

1. Freeze source commit and all fixture/candidate/auditor/test hashes in `FREEZE.json` after construction checks and before running the candidate.
2. Run candidate once and preserve its raw output. Freeze the output and auditor hashes in `AUDIT_FREEZE.json`.
3. Run the independent auditor once. No output is overwritten; any correction requires a separately named successor.

The local Docker Desktop service is stopped and the shared container lane is occupied/ambiguous, so this finite standard-library T0 will run as isolated host processes only. It makes no claim of container-level isolation; no container will be started or inspected.

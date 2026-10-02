# Skill-registry top-k starvation — scoped method result

Parent: [Issue #751](https://github.com/Unjuno/agent-interface/issues/751) · prior distinct rung: [PR #759](https://github.com/Unjuno/agent-interface/pull/759), which tested hard applicability semantics, not candidate-generation starvation.

## H — hypothesis

Applying a hard applicability filter only after semantic top-k can omit an eligible skill beyond k. Exact filter-then-rank avoids that omission by scanning the registry; bounded widening recovers only within its declared budget.

## T — test

Eight frozen deterministic registries, `k=2`, widening budget 6, three retrieval orders. Candidate ran once and a separate independent auditor ran once in pinned CPython 3.12.14 WSLc containers, with networking and pulling disabled. The frozen protocol and exact source hashes are in [`PREREGISTRATION.md`](PREREGISTRATION.md) and [`FREEZE.json`](FREEZE.json); construction history is retained in [`CONSTRUCTION.md`](CONSTRUCTION.md).

## D — result

`METHOD_PASS_SCOPED`: candidate exit 0; independent audit exit 0; 8/8 cases × 3 methods reconstructed with no errors; no non-ALLOW candidate selected. Fixed top-k missed seeded eligible ranks 3 and 6, reporting bounded uncertainty. Widening recovered the rank-6 eligible skill within six checks; rank 7 remained `UNKNOWN_NOT_FOUND_WITHIN_BUDGET`. Exhaustive filter-then-rank found the rank-7 skill. Unknown applicability remained UNKNOWN and did not become an eligible selection.

**Adaptive-stop limitation:** every fixture has at most one `ALLOW` item with `k=2`, so none exercises stopping after finding k eligible cards. The candidate scans the full six-record prefix on the bounded arm, as the raw output reports. Thus this is evidence about fixed-budget prefix recovery and uncertainty—not adaptive early stopping, retrieval-work savings, or behavior when k eligible cards are present.

Machine-readable run, raw output, and audit are retained under [`results/formal_01/`](results/formal_01/), with interpretation in [`results/formal_01/RESULTS.md`](results/formal_01/RESULTS.md) and file digests in [`results/formal_01/SHA256SUMS.txt`](results/formal_01/SHA256SUMS.txt).

## C — limits and counter-explanations

This uses authored rank order and fixture truth, not an embedding or approximate index. Full scan may be expensive; a larger fixed k could reduce misses; stale or incorrect applicability metadata is not tested. No short-circuit/work-saving case was included. WSLc reported that cgroup memory enforcement is unavailable, so although 512 MiB was requested, that limit is not claimed as enforced.

## U — scope

This is only a finite retrieval-method discriminator. It measures no real registry scale, embedding recall, model choice, token/latency economics, GUI behavior, task outcome, or execution safety. It provides no runtime promotion or deployment claim. Any model-facing follow-up needs a separately frozen protocol.

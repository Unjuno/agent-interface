# Issue #6003 A01 — executed shared-prerequisite comparator

Result: **PASS_METHOD_SCOPED**. The candidate and the separately implemented raw-only auditor each ran once in a different WSLc container. Both foreground invocations exited 0. The auditor reconstructed all 72 primary/disjoint/null outcome rows, passed every frozen selector/control gate, and rejected 8/8 effective corruption controls.

This is an executed finite synthetic method experiment. Candidate output retains `SYNTHETIC_METHOD_CONSTRUCTION_ONLY` and `scientific_support_events=0`. Passing these gates does not establish that the card improves real research decisions.

## Frozen comparison

| Selector | Chosen experiment | Maximum changed eligible top claims |
| --- | --- | ---: |
| Cheapest first | E-cheapest-inert | 0 |
| Declared node degree | E-degree-decoy | 0 |
| Authored robust decision reversal | E-verify-unique | 1 |
| Graph aware | E-shared-prerequisite | 2 |

In the primary graph, failing the necessary shared premise changes both CAPTURE and VERIFY from eligible to ineligible. The degree decoy has 12 declared outgoing diagnostic edges but changes neither decision. The robust comparator uses authored worst-case reversal masses: unique 0.75, shared 0.45, correlated source 0.30, degree/invalid-edge 0.20, inert 0. Its scores are illustrative, not empirical probabilities.

The disjoint graph replaces VERIFY's shared premise with an independent premise. Failing P_SHARED then changes only CAPTURE. Every test changes at most one top claim; the graph selector chooses E-verify-unique by the frozen cost tie-break. The null portfolio has zero changed claims and returns UNRANKABLE. The actual selector also returns UNRANKABLE when graph coverage is incomplete.

The correlated source test changes both same-origin predicates together, while independent alternatives keep CAPTURE eligible. The unvalidated edge is reported and ignored. HOLD and STOP leave every decision set unchanged. The mandatory safety sentinel consumes one unit of a four-unit budget and remains reserved for every feasible test.

## Independent audit

The auditor imports no candidate code. It reconstructs feasibility, all four selectors, source groups, edge validity, every before/after decision set, the null/disjoint tables, and the incomplete-coverage gate from the frozen raw fixture. Its first retained output reports `errors=[]` and `primary_selectors_reconstructed=true`.

All eight effective result corruptions were rejected: selecting the degree decoy as graph winner; dropping the sentinel; trusting the false edge; splitting a correlated source group; making STOP decisive; inventing null value; ranking incomplete coverage; and inventing a two-claim effect in the disjoint graph.

## Execution provenance

- Allocation: SHARED-PREREQUISITE-6003-A01-WSLC-20261003-01.
- Owner: Unjuno / Codex thread 01a0b97a-cec4-7141-b37f-31f9f5565543.
- Base main: `165575f4e7c4baf5433f8a36d6a452fd6caefb3c`.
- Source freeze published before execution: `91b40d0bd5f4e7b8f6495b4aa22c8697d30d6432`.
- FREEZE SHA-256: `254e315ecc63ecfe13da5cfa1e40d52863446823191ea5af354bc1251c886d9f`.
- Candidate receipt: 2026-10-03 11:34:35.136580–11:34:38.882083 UTC; exit 0; one invocation.
- Auditor receipt: 2026-10-03 11:34:54.639661–11:34:55.819327 UTC; exit 0; one invocation.
- WSLc 3.0.1.0; pinned cached Python image `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; Python 3.12.14; Linux 6.18.40.1-microsoft-standard-WSL2 x86_64.
- No image pull or network, model, GPU, GUI, or host-input work. Source/candidate input read-only; each result directory separately writable. Exact argv is retained in FREEZE and each attempt/receipt.
- Candidate raw SHA-256: `f62bad4070108bc2c185aa42a5f0a82be8839bafe8061a88c0c43c548d8c5c96`.
- Auditor raw SHA-256: `2c706966b5721b1725a1396986e3bdb3a29ba7d02b27baf25dcdf19293b45cf8`.

Both invocations emitted the same retained stderr:

> wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.

CPU 0.25 and memory 512m were requested. The warning and successful execution do not prove effective memory/swap limits, OOM protection, speed, or Docker parity. Invocation wall times in the receipts include launcher overhead and are not a paired performance comparison.

The host run directories remain at the original frozen locations. Their ten files were copied byte-for-byte into `results/`; the two raw result hashes still match. No frozen candidate, auditor, fixture, construction-test, or capture-runner byte changed after execution. No formal retry occurred.

Prospective record: [#6003 comment 5968766069](https://github.com/Unjuno/agent-interface/issues/6003#issuecomment-5968766069). Scoped CPU allocation and completion: [#5085 allocation](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5968766205), [release](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5968797155).

## Integration and next research rung

The package is additive. It changes no runtime default and preserves the original #6003 host T0, #6744 reproductions, and #5332 graph-evaluator work. Issue #6003 remains open for empirical usefulness.

For retained evidence revalidation, run `python -B verify_packet.py` in this directory. It checks frozen bytes, the complete delivery manifest, exact invocation receipts, chronology, all raw tables, and the original auditor's corruption results without invoking WSLc or producing a new formal result. The 13 construction tests can be run with `python -B -m unittest -v test_method`.

The remaining scientific question is whether a card built from independently adjudicated repository claims changes a real next-experiment decision enough to justify graph construction and maintenance. Coverage, source correlation, graph-authoring cost, and independent adjudication must be measured rather than assumed in that next allocation.

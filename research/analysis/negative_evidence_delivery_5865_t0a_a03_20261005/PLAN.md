# Issue #5865 T0a A03 — origin-bound negative evidence delivery

## Allocation identity and explicit delta

A03 is a separate, prospective CPU-only allocation for the same finite
reuse/delivery hypothesis proposed in the 2026-10-03 Issue #5865 refinement.
It does not rerun A02 or reinterpret its output. A02 remains
`STOP_AUDITOR_ERROR`; its candidate output had mutable event snapshots, its
auditor mutation addressed a nonexistent `A` key instead of `B:A`, and its
unknown-clock case omitted the forwarding step needed to exercise receipt
delivery. A03 repairs those three construction defects and preserves A02
unchanged as predecessor evidence.

## H / T / D / C / U

**H.** In a finite three-tier delivery model, immutable source-evaluation
deadlines plus typed route-failure records prevent false freshness and false
absence while retaining valid repeated-query reuse and healthy independent
routes. The naive sliding, untyped control exposes planted errors.

**T.** Compare (A) no reuse, (B) untyped/sliding-expiry negative reuse, and (C)
typed origin-bound evidence. The standard-library simulator covers cyclic
forwarding, exact expiry, predicate drift, insertion plus invalidation,
missing writer coverage, an explicitly forwarded unknown-clock receipt, route
timeout with an independent healthy route, copied failure cooldown, eviction,
and fresh source reevaluation. Events capture detached state snapshots and
request/route attempts. The independent oracle remains separate from candidate
input.

**D.** `METHOD_PASS_SCOPED` only if unsafe controls expose the intended false
freshness, target-present false negatives, incomplete-provenance claims and
healthy-route suppression; typed handling avoids unsupported negatives and
expired-origin reuse, preserves valid reuse with fewer producer attempts than
no reuse, allows the healthy route after a route-specific failure, accounts
for every request and retained byte/entry, emits no authority, and passes all
independent corruption controls. Otherwise preserve `FAIL_METHOD` or `HOLD`.
Auditor/instrumentation failure is `STOP_AUDITOR_ERROR`, not a scientific
result.

**C.** Fixed integer time, deterministic source outcomes, three cache tiers, a
single target-query family, explicit writer-coverage and clock-mapping bits,
and fixed retry deadlines. Costs and timing are synthetic.

**U.** No live GUI inventory producer, cross-process clock, receipt transport,
production cache, latency, target-effect oracle, or production failure-domain
map is exercised. This cannot prove that a real negative certificate is
complete or current.

## Freeze and run protocol

The prospective freeze pins repository/main identities, governing source
documents, candidate, oracle, auditor, inputs and construction regression
tests. Construction tests execute the finite code in memory only; they do not
write formal candidate outputs or count as the frozen candidate invocation.
After freeze, run the candidate once into `run-01` and the independent auditor
once. Preserve the first output. No retries or source edits are permitted.

## Predecessor and provenance

- A01: pre-candidate freeze-integrity STOP, preserved at
  `../negative_evidence_delivery_5865_t0a_20261005/STOP.md`.
- A02: candidate run retained but unaudited, preserved at
  `../negative_evidence_delivery_5865_t0a_a02_20261005/STOP.md`.
- A03: fresh allocation identity and new path; no prior formal invocation.
- Issue #5865 remains the owner. Its earlier query-completeness T0 and #4174
  history are unchanged.

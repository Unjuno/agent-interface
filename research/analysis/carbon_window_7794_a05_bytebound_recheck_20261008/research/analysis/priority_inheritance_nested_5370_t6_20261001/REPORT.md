# T6 result — nested priority inheritance and post-service aging

**Disposition: `STOP_PROTOCOL_DEVIATION`**. The candidate was frozen and run once, but post-freeze final verification re-ran both the valid-fixture audit test and the standalone raw auditor after the preregistered audit had already passed. All three evaluations returned no errors; the extra evaluations violated the one-audit limit. The raw bytes did not change, but the one-shot audit gate is not satisfied. Preserve the observed synthetic pattern below as unaccepted diagnostic evidence, not a PASS. This is host-CPU evidence, not a Docker result or production scheduler validation.

## Result

The frozen 20-tick replay produced four rows. The first raw-only oracle invocation reported `PASS_AUDIT_V1_SCOPED`, 4 rows, `errors=[]`. Final verification later called the valid-fixture unit test on the same raw and the standalone oracle a second time; both also returned no errors. All three observations are retained in `results/formal-01/AUDIT_RECEIPTS.md`.

| Case | Verifier outcome | A/B service | Background finding |
|---|---|---:|---|
| No inheritance | Deadline missed | 0 / 0 | U receives no service during the 20-tick horizon |
| Transitive inheritance | Completes at tick 6 | 2 / 2 | Critical chain is `M,A,A,B,B,H`; inheritance-only leaves U unserved in this horizon |
| Inheritance + aging | Completes at tick 6 | 2 / 2 | U first runs at tick 6, then ticks 9, 12, 15, 18; M also runs after U begins; maximum observed U wait is 6 ticks including initial wait |
| Waiter cancels at tick 2 | Cancelled at tick 2 | 1 / 0 | Inherited boost disappears; A/B/H do not resume after cancellation |

As observed in this bounded trace, transitive inheritance resolves this particular priority inversion, but inheritance alone does not provide background fairness; post-service wait aging shares CPU in this trace while preserving the deadline path and later M service. Because of the audit protocol deviation, this remains unaccepted synthetic evidence.

## Construction failure caught before the frozen run

An initial aging implementation accumulated U's age permanently. A new regression failed with U occupying every remaining tick and M receiving no service. Resetting U's aging debt at each service made the sequence alternate between three M/U turns while retaining H's tick-6 completion. The red failure and corrected 9/9 suite are preserved in the task record; the final candidate was frozen only after this correction.

Pre-freeze exploration included an intermediate candidate output that was superseded during construction. It is not represented as formal evidence and is not part of the bundle. The only claimed raw result is the single post-freeze `results/formal-01/raw.json` invocation.

## Scope and limitations

This is a hand-authored deterministic one-CPU schedule with two resources, a complete wait-for chain, fixed service durations and a 20-tick horizon. The oracle is separately implemented and imports no candidate code, but it shares the preregistered synthetic contract. No randomized tail behavior, nested cycles, partial/hidden wait graphs, remote workers, adversarial resource claims, real freshness deadline, actual verifier, GUI, or runtime was exercised. Inheritance fairness and aging policy need a larger scheduler model and independent workload traces before implementation claims.

No prior #5370 result or STOP is modified. This does not close #5370, Issue #59, or any roadmap gate. Docker Desktop was intentionally not invoked: #5085's serialized shared-container policy was not explicitly transferred to this allocation. The runnable host commands and complete raw artifact are retained alongside this report.

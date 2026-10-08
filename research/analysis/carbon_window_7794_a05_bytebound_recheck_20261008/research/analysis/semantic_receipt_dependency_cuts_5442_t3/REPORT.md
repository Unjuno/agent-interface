# Issue #5442 T3 — provenance-derived observer fault domains

## Disposition

`PASS_DEPENDENCY_CUT_METHOD_SCOPED`. Across five frozen synthetic scenarios,
two-observer agreement falsely committed once when both observers shared a
failed cache and reported the intended state while ground truth contradicted
it. The independently audited provenance-pair policy excluded both affected
receipts and did not commit. A separately labeled trusted endpoint C reported
the stipulated contradictory state and did not commit. The same conservative
provenance policy also abstained in the actuator-readback-fault row even though
A/B agreed with the true goal, because their declared dependency closures
overlap. This is a scoped safety/availability trade-off in the model, not a
production recommendation.

## Execution

- Issue: [#5442](https://github.com/Unjuno/agent-interface/issues/5442),
  allocation `5442-receipt-provenance-dependency-cuts-t3-20261001-01`.
- Base: `51dd32406fe64c10eb8c2408ffc4682f0939dc41`.
- Host: CPython 3.14.5, standard library. No Docker/OrbStack, network, model,
  GUI, or external effect; shared container provenance/assignment remains
  unresolved in #5085.
- Candidate invocation: 1, exit 0; no retry or tuning.
- Raw-only auditor: 1, exit 0; 5 rows, PASS, zero errors. It derived each
  observer's faultable dependencies by traversing provenance-DAG edges and
  independently recomputed excluded observers, disjoint pairs, and policy
  outcomes. It also checked the frozen scenario inputs.
- Corruption controls: 6/6 rejected (forged provenance edge, erased failure,
  altered report, forged ground truth, flipped summary, changed trusted endpoint).
- Construction tests: 4/4 PASS before source freeze.

## Outcomes

| Scenario | A/B agreement commits | Independent-pair gate | Trusted-C gate |
|---|---:|---|---|
| No fault | yes | confirms | confirms |
| Parser A fault | no | confirms from B+C | confirms from C |
| Parser B fault | no | confirms from A+C | confirms from C |
| Shared-cache common lie; actual state contradicts goal | **false commit** | abstains | reports contradiction; no commit |
| Actuator readback fault; A/B correct but correlated | commits correctly | abstains | UNKNOWN |

The graph-derived closure shows A and B share `shared_cache`; C uses the
separate `actuator_readback` path. In this stipulated fault model, provenance
invalidation prevented the shared-cache false commit. It also incurred one
false abstention when the independent endpoint was declared faulty and the
remaining pair shared a dependency.

## Reproduction and hashes

Exact H/T/D/C/U, commands, and frozen source hashes are in `PLAN.md` and
`FREEZE.json`. Raw SHA-256:

- candidate JSONL: `ce5de7339fe314072211d8aab4c3595c9946923bfcc89c2a42851c3b5899b496`
- audit JSON: `1e9ae888f280c34f6380485a2b5389d2bc9155fd43ae0a93112f92661bba8843`
- corruption controls JSON: `55e06f97db31b26352e6111688d66e9f8f7b9f49eda732a0e85c5552720f7609`

## Scope and residual

The provenance DAG, failures, ground truth, receipt values, and C trust status
are hand-authored. This does not measure real observer independence, detect
unmodeled failures, validate provenance extraction, or establish Byzantine
robustness, GUI/effect correctness, timing, latency, or product safety. The
trusted-C branch is conditional on a trust assumption supplied by the model.
Issue #5442 remains open for real provenance and endpoint-fidelity validation.

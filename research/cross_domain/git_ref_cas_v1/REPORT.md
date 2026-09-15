# Git ref CAS delayed-delivery experiment

Decision: **RETAIN scoped effect-owner compare-and-swap** for this local Git ref boundary. Issue #287.

## Question
Can the effect owner itself reject a delayed update when the exact target identity/version changed after planning, without globally blocking an unrelated ref change?

## Frozen experiment
Git 2.47.3; CPython 3.13.5. Sixty fresh local repositories: 2 policies x 3 schedules x 10 repetitions. Policy is either naive `git update-ref target B` or effect-owner CAS `git update-ref target B A`. Schedules are stable, target changed A→C before delivery, or an unrelated ref changed while target remained A.

The schedule was frozen before the first measured case. A defect in the independent auditor was discovered with **zero measured cases consumed**: the first version treated the deliberately unsafe `naive + target_changed` negative control as audit corruption instead of retaining it as a valid negative result. Only that audit interpretation/test was corrected; schedule, experiment code, policies, ground truth and decision gates were unchanged. The final premeasurement freeze is commit `d1e2024d9d9c108d642bee8a03ba1c198ff0148a`.

## Results
- naive / target-changed: **0/10 ground-truth correct**; all 10 overwrote intervening C with B.
- CAS / target-changed: **10/10 correct**; all 10 returned nonzero and preserved C.
- CAS / stable: **10/10 correct**, B written.
- CAS / unrelated-change: **10/10 correct**, B written while unrelated C remained intact.
- naive stable/unrelated controls were also 10/10 correct.

All 60 cases pass the independent integrity audit: recorded A/B/C objects exist as Git commits, final refs equal repository state, unrelated refs match the schedule, return-code behavior matches the invoked policy, and target reflogs equal the retained rows. No measured case ID was rerun.

The CAS rejection is performed by the real Git effect owner at the same ref update operation: the stderr identifies the actual current C and expected plan-time A. It is not a caller-only precheck followed by an unguarded write.

## Interpretation
This transfers the semantic-revalidation idea from a synthetic receiver to a real effect owner. Git's authoritative old-OID comparison prevents the stale write without a global context epoch and without blocking an unrelated ref mutation.

The result does **not** establish arbitrary GUI validity, multi-ref transaction semantics, network/distributed consensus, power-loss behavior, or semantic equivalence between different commit OIDs. Exact OID equality may reject a different commit that is semantically acceptable; that is the next discriminating rung rather than something inferred here.

## Verification
Prefreeze tests after the audit correction: 6/6 PASS. A separate extraction of the retained evidence reruns the six tests and the independent audit: 60/60 cases reproduce exactly. The retained manifest covers 2,293 files with zero SHA-256 mismatches.

Full raw evidence is a conversation/container artifact rather than byte-complete GitHub retention: `git_ref_cas_evidence.tar.xz`, 83,964 bytes, SHA-256 `b2df85b36e773222edf2a498ddf7f7ce272fe3aa5f2f6807d34b210a3f3cdcee`.

## H / T / D / C / U
**H:** commit-time old-OID validation prevents stale delayed delivery.

**T:** 60 frozen first outcomes over fresh repositories, with stable, target-changed and unrelated-change schedules.

**D:** scoped PASS / retain. CAS stale overwrite 0/10 and false reject 0/20 controls; naive exposes 10/10 stale overwrites.

**C:** the candidate consumes authoritative target identity/version evidence that the naive arm does not.

**U:** one Git build/host/ref and an authored exact-identity dependency. No timing, natural fault-rate, model, GUI or general performance claim.

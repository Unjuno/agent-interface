# Issue #5275 deterministic ontology-gap discriminator — preregistration

Allocation: ontology-gap-5275-deterministic-t0-20260930-01
Frozen current-main intake: 322faf504a5ac993b092f154733d83bc13767e60
Branch: research/ontology-gap-5275-deterministic-t0-20260930
Path: research/verification/ontology_gap_5275_v1/

## H / T / D / C / U

**H.** A deterministic schema/coverage detector over the frozen Verification IR v0.1 can distinguish the four supported Agent Action cases from five explicit and semantic ontology-gap cases, without silent false PASS and without abstaining on supported cases.

**T.** One finite no-task-input allocation. The nine-case corpus includes three IID and one compositional supported case, three explicit malformed/unknown cases, one novel external-side-effect case, and one adversarial superficially familiar legal-hold case. Candidate sees only each typed plan; the oracle annotation and family labels are not passed to it. Candidate is a deterministic allow-list/schema checker over primitives, evidence roles, verifier class, subject reference and IR version. Frozen runner emits raw JSON once. A separate literal raw-only auditor does not import the candidate. Seven host-only construction tests run before the one T0 invocation. No model or verifier is dispatched.

**D.** PASS only for exact predictions on all nine rows, zero false OOD PASS, zero false IID abstention, zero dispatch/authority creation, and independent audit with no integrity error. Any false OOD PASS is FAIL; malformed/unavailable/unknown must yield. Audit success validates evidence integrity, not the hypothesis.

**C.** All cases and labels are synthetic and authored for this finite probe. A deterministic schema detector is intentionally not a semantic parser; task-summary text can contain a requirement absent from its typed checks. No model comparator is included in this first rung.

**U.** No semantic OOD recall beyond these cases, calibration, learned-router comparison, runtime escalation behavior, task/GUI quality, latency, safety improvement, or cross-domain generalization. This does not establish ontology completeness.

## Freeze and execution boundary

Registry source Git blob: d7e35205daf8b7385a189ef5d1a78bd07ded3cbd.
Corpus source Git blob: 81e15afc954eac6687269ff5971d690bb1170208.
Runner source Git blob: dbea4672730b8617e29cdeeb63df37c3657d423d.
No Docker invocation is authorized or needed for this tiny bounded CPU-only construction; formal runner is executed on host via Python 3.11 with source streamed from GitHub readback, no local result files, no model/GPU/network/dispatch. C: had 0 bytes free, and the concurrent container queue has unresolved allocations. All code/corpus are frozen on branch before the one runner invocation. Raw result is retained in the subsequent additive report/Issue comment.

# Issue #5275 T1 — lexical novelty boundary probe

Allocation: `ontology-gap-5275-t1-lexical-boundary-20260930-01`
Intake main: `1e34cef0b9c9b729aa0fbd32785dd658a4b6c94f`
Branch: `research/ontology-gap-5275-t1-v1-20260930`
Path: `research/verification/ontology_gap_5275_t1_v1/`
Predecessor: #5275 T0, `research/verification/ontology_gap_5275_v1/`; immutable.

## H / T / D / C / U

**H.** A one-class lexical confidence signal trained only on supported Agent
Action descriptions will flag the two T0 semantic false-pass requirements,
while abstaining on at most 1/6 supported challenge cases. Combining that
signal with the existing schema/coverage boundary will retain explicit
structural-gap detection and avoid false PASS on semantic OOD, including
paraphrase and known-vocabulary-dilution probes.

**T.** Freeze 8 synthetic supported training summaries and 13 held-out
evaluation rows in `corpus.json`. Evaluation has 6 supported IID/compositional
rows, 3 explicit schema/role/malformed gaps, the two exact T0 semantic false
passes, and two semantic-OOD dilution variants that append only in-domain
vocabulary. Compare (1) T0 deterministic-plan outcomes as retained in
`../ontology_gap_5275_v1/FORMAL-01.json` for its original nine rows and
deterministic coverage for new rows, (2) lexical novelty only, and (3) the
combined fail-closed OR. The lexical model is vocabulary OOV-token fraction,
trained only on the eight training task summaries; threshold is `> 0.20`.
Candidate input excludes labels, family, and plan. No model/service/verifier
dispatch or task input.

**D.** Scoped PASS requires all 6/6 supported evaluation rows non-abstaining,
all 7/7 OOD rows abstaining under combined policy, and independent raw-only
audit with no integrity errors. Also report each arm's OOD false passes and
IID false abstentions; any gate miss is retained as FAIL, not tuned away.
Construction tests precede one frozen host-CPU run. One independent auditor
recomputes token novelty and policy outputs without importing candidate code.

**C.** Corpus/labels are hand-authored synthetic and small. Vocabulary novelty
is not semantic understanding; familiar vocabulary can describe a novel
requirement, and harmless domain words can cause false abstention. Appending
known words is an explicit adversarial dilution test. This probe cannot support
calibration, population recall, or a safety guarantee.

**U.** No learned semantic router, semantic generalization, real action effect,
escalation behavior, operational verifier, latency/cost benefit, safety gain,
IR completeness, or runtime/product claim. Even a scoped PASS would justify
only a larger preregistered study, not promotion. Container gate was not
available to this host-only probe; no container command will be represented as
having run.

## Freeze and command

Frozen from current main at the intake SHA above; source and corpus are additive
and hashed in `FREEZE.json`. Construction:
`python3 -m unittest research.verification.ontology_gap_5275_t1_v1.test_candidate`.
Formal:
`python3 research/verification/ontology_gap_5275_t1_v1/run_t1.py`.
Independent audit:
`python3 research/verification/ontology_gap_5275_t1_v1/audit_t1.py FORMAL-01.json`.

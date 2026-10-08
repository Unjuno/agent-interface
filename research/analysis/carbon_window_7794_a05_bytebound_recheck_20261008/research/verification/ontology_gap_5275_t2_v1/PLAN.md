# Issue #5275 T2 — lexical novelty on genuinely held-out surface forms

Allocation: `ontology-gap-5275-t2-heldout-20260930-01`
Intake main: `30d98dcf65e9d5a1772083b416b84753f28f0b4e`
Branch: `research/ontology-gap-5275-t2-heldout-v1-20260930`
Path: `research/verification/ontology_gap_5275_t2_v1/`
Successors: T0 #5374 immutable; T1 PR #5457 remains unchanged.

## H / T / D / C / U

**H.** The T1 one-class lexical OOV signal at its unchanged `>0.20` threshold
will abstain on at most 2/8 supported cases whose exact summaries were not in
training, and the fail-closed combination will not false-PASS any of 8 OOD
cases, including two known-vocabulary repetition attacks.

**T.** Fit only on the same eight synthetic supported training summaries used
in T1. Freeze 16 non-identical evaluation summaries: 8 supported IID or
compositional cases written with held-out surface forms; 3 explicit structural
gaps; 3 semantic requirement gaps; and 2 semantic gaps padded by repeated
known training vocabulary. Compare deterministic coverage, lexical-only, and
their fail-closed OR. The algorithm and threshold are carried over unchanged
from T1; no threshold/model selection or post-hoc corpus expansion. Candidate
sees only task-summary text for the lexical arm. No task input or dispatch.

**D.** Scoped PASS requires combined OOD false passes 0/8, combined supported
false abstentions ≤2/8, and independent raw-only audit `errors=[]`. Report
OOD recall, IID abstention, and row/family counts for every arm. Any gate miss
is FAIL, not a tuning trigger. Construction tests run before the one frozen
host CPU invocation; auditor independently recomputes each score and policy.

**C.** Corpus and semantic labels are synthetic, hand-authored and finite.
Surface-disjoint paraphrases can be ambiguous or semantically mislabelled.
Repeated-token dilution is adversarial and not a natural-language population
sample. The lexical signal is not a semantic model or calibrated confidence.

**U.** No operational semantic generalization, calibration, verifier/effect
truth, escalation behavior, latency/cost benefit, safety improvement, ontology
completeness, runtime integration, or product claim. T1's apparent lexical
separation cannot be promoted on this successor alone.

## Freeze / execution

Frozen from current main `30d98dcf65e9d5a1772083b416b84753f28f0b4e`.
Construction: `python3 -m unittest discover -s
research/verification/ontology_gap_5275_t2_v1 -p 'test_*.py'`.
Formal: `python3 research/verification/ontology_gap_5275_t2_v1/run_t2.py`.
Independent audit: `python3
research/verification/ontology_gap_5275_t2_v1/audit_t2.py
research/verification/ontology_gap_5275_t2_v1/FORMAL-01.json`.

Container gate: no exact exclusive Docker/OrbStack lease is granted in current
#5085 coordination. Therefore one CPU-only host run is authorized by this
preregistration; no container command, model, network, GPU, GUI, or verifier
invocation is made or claimed.

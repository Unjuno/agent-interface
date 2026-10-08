# Issue #5275 T2 — held-out surface and vocabulary-dilution test

## Result

**FAIL_HELDOUT_LEXICAL_BOUNDARY**. The T1 lexical OOV rule at its unchanged
`>0.20` threshold could not separate non-identical supported wording from
semantic ontology gaps in this finite synthetic benchmark.

| Arm | OOD false-PASS | OOD recall | Supported false-abstain |
|---|---:|---:|---:|
| Deterministic coverage | 5/8 | 3/8 (0.375) | 0/8 |
| Lexical-only | 2/8 | 6/8 (0.750) | 8/8 (1.000) |
| Combined fail-closed | 2/8 | 6/8 (0.750) | 8/8 (1.000) |

The lexical arm abstained on every supported held-out surface form. It caught
the three undiluted semantic OOD rows, but a customer-export/recipient case at
OOV fraction 0.1923 and a preservation-hold case at 0.1731 fell just below the
unchanged threshold and were `PLAN_COVERED`. Both pre-registered combined
acceptance gates failed. No threshold change, post-hoc corpus extension, or
rerun was performed.

## H / T / D / C / U and execution

The complete preregistration is in [`PLAN.md`](PLAN.md); exact cases and row
results are in [`corpus.json`](corpus.json) and [`FORMAL-01.json`](FORMAL-01.json).
The independent raw-only auditor returned `integrity_pass=true`, `errors=[]`
in [`AUDIT-01.json`](AUDIT-01.json), and 11 corruption mutations were rejected.

- Frozen intake main: `30d98dcf65e9d5a1772083b416b84753f28f0b4e`.
- Pre-run construction: `python3 -m unittest discover -s
  research/verification/ontology_gap_5275_t2_v1 -p 'test_*.py'` — 5/5 PASS.
- One frozen invocation: `python3
  research/verification/ontology_gap_5275_t2_v1/run_t2.py` — exit 0; CPython
  3.14.5 on macOS CPU; no container/model/verifier/GPU/network/GUI/dispatch or
  authority grant.
- Independent audit: `python3
  research/verification/ontology_gap_5275_t2_v1/audit_t2.py
  research/verification/ontology_gap_5275_t2_v1/FORMAL-01.json` — exit 0,
  `errors=[]`; auditor recomputes each lexical score and each policy output
  without importing candidate or runner code.
- Post-run construction suite: 7/7 PASS; 11/11 auditor mutation controls
  rejected. JSON parse and `git diff --check` passed.
- Raw JSON SHA-256: `a1db4a23028d91ce2dba0f92c62c24833678845df4721794cb7e8f1334087321`.
- Candidate SHA-256: `74d9c5e75cde6a5834418c96d44f69b0055e9e77ddb3304593be9d25d4e4fe48`.

## Interpretation / limits / next step

All data and semantic labels are synthetic and author-created. The held-out
phrases are string-disjoint from training, but this is not a population sample;
the semantic oracle is a declared fixture, not an operational verifier. The
result is a concrete counterexample to relying on raw vocabulary novelty as
confidence: supported paraphrases trigger universal abstention while repetitive
known vocabulary hides two novel requirements. It is not evidence about a
semantic language model or runtime escalation behavior.

The shared container allocation gate remains ungranted in #5085, so the formal
run is host-only and explicitly `container:false`. Keep T0, T1, and this T2
separate and immutable. Any successor must use a different, semantically
grounded confidence signal or deterministic requirement representation and a
new independently labelled corpus; merely tuning this threshold would not
resolve the opposing error modes shown here.

# Issue #5275 T1 — lexical novelty boundary probe

## Result

**PASS_SCOPED_LEXICAL_BOUNDARY**, strictly for this 13-row synthetic host-only
probe. The deterministic-plan baseline false-passed 4/7 oracle-UNKNOWN cases
(OOD recall 3/7 = 0.429). The lexical-only arm and combined fail-closed arm
false-passed 0/7 and falsely abstained on 0/6 supported rows. The combined
pre-registered gates passed. Exact scores and row outcomes are in
[`FORMAL-01.json`](FORMAL-01.json); the independent auditor returned
`integrity_pass=true`, `errors=[]` in [`AUDIT-01.json`](AUDIT-01.json).

The two semantic false-pass cases from immutable T0 #5374 were retained as-is.
Two additional versions padded with known vocabulary were also flagged; their
OOV fractions were 0.303 and 0.324, above the frozen 0.20 threshold. This does
not establish resistance to stronger dilution or semantic paraphrase.

## H / T / D / C / U

See [`PLAN.md`](PLAN.md) for the preregistered H/T/D/C/U and gates. The actual
experiment was an eight-summary one-class vocabulary fit and a fixed threshold
comparison across deterministic, lexical-only, and combined policies. The
candidate reads only the task summary; it makes no action decision. Corpus,
candidate, runner and auditor identities are in [`FREEZE.json`](FREEZE.json).

**Important validity limitation:** although the plan called the six supported
evaluation rows paraphrases, they are verbatim copies of six training
summaries. Thus the 0/6 IID abstention result is a training-overlap check, not a
held-out IID generalization estimate. The two diluted OOD texts also contain
many copied training phrases. The PASS label is retained for the stated
finite gates, but this corpus cannot support the intended generalization claim;
the useful finding is only that this simple signal separates these authored
phrases and that the deterministic baseline retains four misses.

## Execution and audit

- Frozen main: `1e34cef0b9c9b729aa0fbd32785dd658a4b6c94f`.
- Construction before the formal run: `python3 -m unittest
  research/verification/ontology_gap_5275_t1_v1.test_candidate` — 5/5 PASS.
- One formal invocation: `python3
  research/verification/ontology_gap_5275_t1_v1/run_t1.py` — exit 0; CPython
  3.14.5, macOS, CPU-only host; no container, model, GPU, network, verifier,
  GUI/input, dispatch, or authority grant.
- Independent raw-only audit: `python3
  research/verification/ontology_gap_5275_t1_v1/audit_t1.py
  research/verification/ontology_gap_5275_t1_v1/FORMAL-01.json` — exit 0,
  `errors=[]`. It does not import the candidate and recomputes lexical scores
  from the frozen training and evaluation text.
- Post-run construction suite including audit controls:
  `python3 -m unittest discover -s
  research/verification/ontology_gap_5275_t1_v1 -p 'test_*.py'` — 7/7 PASS.
  Nine audit mutations were rejected by the mutation-control test.
- `python3 -m json.tool .../FORMAL-01.json` and `git diff --check` — PASS.
- Raw SHA-256: `ce1219edc12ed3526c0be90043bfe3428db3d36e42c6337e6f532e18ae2c72d6`.
- Auditor SHA-256: `b174f1f5c44b5bfb61111d3d0535637afcdcbee6b3313143ae430b4f51aa9104`.

## Resource gate, limits, and next rung

No exact container lease is granted. Live #5085 states that Docker/OrbStack
work waits for owner-specific explicit slot assignment/release; latest visible
request remains ungranted. Therefore this experiment is explicitly
`container:false`; no container command was attempted. Full-repository checks
that require the complete checkout are not claimed from this sparse checkout.

All data and labels are author-created and finite. No calibrated probability,
semantic generalization, true task effect, operational escalation, latency or
cost result, safety improvement, ontology completeness, runtime integration,
or product claim follows. Keep T0 unchanged. A successor should preregister
lexically disjoint held-out supported summaries and much stronger known-token
dilution (including repeated-token and paraphrase controls) before any further
formal run; do not tune this frozen T1 after observing its output.

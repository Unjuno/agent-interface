# Issue #8574 T0 A01 — result

**Disposition: `NO_INCREMENTAL_VALUE_SCOPED`.** On this frozen synthetic contract set, perspective-guided review found no source-supported cross-invariant omission that both comparison procedures missed. The ordinary checklist, free-form decomposition, and perspective-guided reviewers all identified the same-record-across-views omission in Q11 (2/2 reviewers per arm). The preregistered incremental-rescue condition therefore did not pass.

The raw-only audit completed with 16 cases, six reviewers, 79 adjudicated findings, zero audit errors, zero unsupported additions on clean controls, and zero forced-ambiguity failures. It independently reconstructed two reviewers per arm and the counterbalanced case order. Q04 was found by all arms as well, although the blind adjudicator did not credit those findings for the narrower cross-invariant relation criterion. The result does not depend on that classification: Q11 alone was credited in every arm.

Reviewers in all three arms also flagged Q01’s added payment-card preservation check as unsupported. On Q03, the perspective arm framed the wrong-customer target as an unsupported addition while the other arms treated it as a source-supported omission; this did not affect the primary decision rule. Q09 and Q14 remained ambiguous in every review. These observations are retained in the raw outputs and blind adjudication.

This is method-scoped evidence from 16 authored synthetic contracts reviewed by six isolated Codex subagent contexts from the same configured model family. It does not estimate human reviewer performance, real-world omission prevalence, GUI safety, production correctness, or product benefit. No GUI, live data, model API, or application runtime was used; the Issue’s T0 is a source-contract review and does not require an operational environment.

## Reproduction

From this directory, run:

```sh
python3 audit.py
python3 -m unittest discover -s . -p 'test_audit.py' -v
python3 -O -m unittest discover -s . -p 'test_audit.py' -v
```

The first command writes `results/AUDIT.json` and exits successfully for either scoped method outcome. It reports `NO_INCREMENTAL_VALUE_SCOPED` for these observations. The tests cover incremental-rescue detection, missing-case rejection, and ambiguity rejection; they are auditor construction checks, not additional experiment evidence.

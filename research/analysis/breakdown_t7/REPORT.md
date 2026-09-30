# Evidence breakdown T7 — generated UNKNOWN-authority scenario family

Issue: [#5444](https://github.com/Unjuno/agent-interface/issues/5444)
Task: `ISSUE-5444-BREAKDOWN-T7-20260930`
Disposition: `PASS_SCOPED_SYNTHETIC_GRID`

## Decision

The complete 320-cell generated grid reproduces the expected action-class/compensation Pareto pattern. Permitting an UNKNOWN high-authority receipt as zero evidence allows the four low-weight receipts to produce 20 commits, including 10 unsafe and 10 irreversible UNKNOWN commits. A reversible-only compensation filter avoids irreversible UNKNOWN commits, but as its threshold rises from 0 to 4, commits rise from 2 to 10 while unsafe commits rise from 1 to 5. No threshold was selected or recommended.

All rates below are proportions of this deliberately constructed exhaustive grid, not probabilities or confidence intervals. The result shows a policy tradeoff in the authored model; it does not calibrate compensation, weights, safety, provenance, or real evidence.

## H/T/D/C/U

- **H:** UNKNOWN-as-zero can create unsafe commits from low-weight unanimous votes. Reversible-only compensation filtering blocks irreversible UNKNOWN cases but relaxing the threshold increases both availability and unsafe commits.
- **T:** Enumerate action class × oracle truth × compensation cost × all four-vote profiles; compare fail-closed, UNKNOWN-as-zero, and reversible compensation thresholds 0–4. Independently reconstruct every cell with exact rational arithmetic.
- **D:** PASS if the auditor reproduces 320 unique cases and all summaries; fail-closed has 0 commits; UNKNOWN-as-zero has 20 commits including 10 unsafe and 10 irreversible; reversible thresholds have commits `2,4,6,8,10`, unsafe commits `1,2,3,4,5`, and zero irreversible UNKNOWN commits. Four corruption controls must be rejected.
- **C:** A different evidence-generation mechanism, low-vote threshold, or compensation distribution could change the Pareto curve. This does not imply every reversible UNKNOWN action should be permitted.
- **U:** Scenario variables and labels are authored; grid fractions are coverage only. It has no real source binding, adversarial model, empirical calibration, confidence intervals, or product behavior.

## Frozen experiment

Preregistration was posted to Issue #5444 before formal execution (comment ID `5910699630`). Source hashes are in `SOURCE_MANIFEST.md`.

- Command: `docker run --rm --network none -v "$PWD/research/analysis/breakdown_t7:/work" python:3.12-slim sh -c 'python /work/experiment.py > /work/raw/formal.json'`
- Engine: OrbStack Docker Engine `29.4.0`, `linux/arm64`.
- Image: `python:3.12-slim`, immutable local digest/ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Formal invocations: 1; RNG: none.
- State space: `2 × 2 × 5 × 16 = 320` cases. Every case has one UNKNOWN authority receipt; each of four low receipts weighs 0.075, scoring +0.075 for support and -0.075 for oppose. Low-evidence COMMIT threshold is 0.3, requiring unanimous support.

## Full threshold sweep

| policy | compensation limit | commits / 320 | unsafe commits | safe abstentions / 160 | irreversible UNKNOWN commits |
|---|---:|---:|---:|---:|---:|
| `UNKNOWN_FAIL_CLOSED` | — | 0 | 0 | 160 | 0 |
| `UNKNOWN_AS_ZERO` | — | 20 | 10 | 150 | 10 |
| reversible compensation filter | 0 | 2 | 1 | 159 | 0 |
| reversible compensation filter | 1 | 4 | 2 | 158 | 0 |
| reversible compensation filter | 2 | 6 | 3 | 157 | 0 |
| reversible compensation filter | 3 | 8 | 4 | 156 | 0 |
| reversible compensation filter | 4 | 10 | 5 | 155 | 0 |

All policies cover all 320 scenarios at every threshold. The four-vote profile is fully enumerated; only `1111` reaches the low-evidence score threshold. In committing cells, changing any one of those votes removes the score margin, so the generated score certificate reports one vote flip to break the decision. In non-committing cells, `4 - support_count` is the number of flips needed to reach unanimous support.

## Independent audit and raw hashes

The independent auditor rebuilds all cells with `Fraction(3,40)` and `Fraction(3,10)`, then recomputes every policy and aggregate. Audit: PASS, 320 scenario rows, five thresholds, zero errors. Four corrupted copies (missing scenario, changed vote profile, altered unsafe count, missing threshold) were all rejected.

| artifact | SHA-256 |
|---|---|
| `experiment.py` | `73affba3041088cf1e80bbe7c90730ee204b902548ced640872c6e0ab70e4115` |
| `audit.py` | `16e16b9011f35eff6d3744d807a310fc75b64a5976ebc810b50fc1e3ebb0a4f8` |
| `corruption_controls.py` | `86a1e968d8e7409c49452b31d7b30808450d7e446345d1c29fe58ba915dcb300` |
| `raw/formal.json` | `97225e6504d82cdb67eb64e5d2156066f7b502a2fb1765f2920dcacf6add5b86` |
| `raw/audit.json` | `4707b191d508ecd6a67c4b515351c29826db63f77164bb70479d8dd8f9310236` |
| `raw/corruption_controls.json` | `0afa9d27b7ad9804a33a922fbadfad6115efc2cb80b26e14d2823ad40a18e0fe` |

## Stop

Stop this exact scenario allocation. Do not select a compensation threshold from these grid counts. A successor would need independently grounded compensation/reversibility contracts and provenance-backed evidence, or a separately preregistered alternative scenario family.

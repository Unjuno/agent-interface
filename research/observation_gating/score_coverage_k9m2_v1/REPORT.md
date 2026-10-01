# #4356: marginal calibration is not candidate-set coverage

**PASS_SCORE_COVERAGE_BOUNDARY_SYNTHETIC**. This is one completed synthetic
statistical/software experiment, not calibration of a real GUI detector.

## Chronology and first outcome

Intake main4a1f3957e91b412a64769199f78f2c4b0102d28b. All11 readable preformal
source/plan/config/environment/construction/freeze files were committed at
876855587ba9e57783355e3237b924ca16b2bf38 and read back before execution.
Issue #4356 comment5832511484 is the preformal commitment; comment5832534844
records the first result. Formal invocations1; reruns/replacements/exclusions/
post-freeze tuning/pooling0. Preserve #4276/#4146 and all parallel studies.

The three frozen seeds produced2997 calibration rows and6000 evaluation rows.
Each row has four latent permuted integer scores and separately retained
uniform/error draws. Predictors see only observed scores and calibrated radii.
Each seed estimated marginal radii[0,0,0,0] and joint radii[10,10,10,10]; the
implementation did not force those values. Full H/T/D/C/U, conditional proofs,
variable/unit table and exact PRNG/split rules are in PLAN.md and CONFIG.json.

## Observed results (each profile3000 rows)

| Profile | Policy | Winner omissions | Retained candidates, total | Mean set size |
|---|---|---:|---:|---:|
| IID | TOP1_POINT |265|3000|1|
| IID | MARGINAL95 |265|3000|1|
| IID | JOINT95 |0|12000|4|
| SHIFTED_AMPLITUDE | TOP1_POINT |256|3000|1|
| SHIFTED_AMPLITUDE | MARGINAL95 |256|3000|1|
| SHIFTED_AMPLITUDE | JOINT95 |256|11003|3.6677|

MARGINAL95 IID coordinate coverage across the12 seed-coordinate cells is
96.0-97.8%, yet true-winner omissions are8.8333%. Seed omission counts91/84/90
are descriptive blocks, not different workloads. Marginal joint containment is
2642/3000; it is not the same endpoint as winner retention.

JOINT95 IID never omits the winner but retains all4 candidates on every row:
there is **no demonstrated pruning utility**. Reusing it after outlier amplitude
changes10 to30 loses256/3000 winners (8.5333%; seed counts89/81/86). This profile
violates the exchangeability assumption deliberately, not the conformal theorem.
Every actually jointly covered row retains the winner under both interval arms.
Point TOP1 is not an interval and receives no interval-coverage certificate.

## Verification and evidence

All five frozen scientific gates pass. Actual formal child and outer supervisor
exit0, timeout=false. Separate endpoint-enumeration/histogram auditor:90013
checks, errors=[]; twelve effective copied-evidence corruptions all reject.
Audit/control subprocesses exit0 with empty stderr. Construction12 unit tests
and6 postformal lossless-codec tests pass. Same-author separate implementations
and processes are not independent human review. No missing outcome was inferred.

RAW.json is807398 bytes, SHA256
10a1bb579b354d2f1f39d73255f04e074397776558c91aa3d21996f8b1c8c6db.
Original raw audit SHA256
400915662b1d727f3cedfba2b736effa5622c31d8ab81ce99b27245d4959d3fd.
Original controls SHA256
ac8414faa97253989790829ec7e741b3923ef9c60cca70f8a32b00286cb0c7f0.

The repository stores a lossless column codec, not a substitute rerun:
all draws, latent permutations, observed score deltas and actual candidate masks
are encoded. PACK.json preserves metadata; nine Base64 parts contain XZ bytes.
Restoration reproduces the exact original RAW hash before any file is accepted.
verify.py checks all manifest hashes, actual execution receipts and byte-identical
raw audit/control stdout on restored data without running execute.py/run.py.

One publication-only transcription added a character to part02. Its returned
Git blob disagreed and was excluded, never attached to any tree. Corrected
upload matches original local bytes; original source/raw are unchanged. Exact
identities are retained in PUBLICATION_INCIDENTS.json. No science was repeated.

## Decision and limits

REJECT the claim that a nominal95% coordinate interval automatically certifies
95% target retention. HOLD practical pruning adoption: simultaneous coverage
alone may retain every candidate, and unrecognized distribution shift breaks
its premise. The concrete #18/#2789 observation-interface requirement is to name
coordinate/vector/candidate coverage, calibration population and shift limits.
This does not select a production threshold or confer input/task authority.

Provided Linux6.18.44/x86_64, CPython3.13.5 stdlib, Intel Xeon Platinum8370C
host-reported CPU,5 available CPUs, uncontrolled frequency/load. No attested
Docker/OrbStack image, package install, GUI/model/provider/OS input or experimental
network. Times are diagnostics only, not benchmarks. Integer arithmetic removes
numeric tolerance from comparisons, not physical uncertainty. No calibrated
combined physical uncertainty or population reliability estimate is invented.
Real-detector quality, useful attention cost, model tokens, latency, live task
correctness, cross-platform transfer and production adoption remain untested.
Only this study's bounded gate is complete; global ROADMAP remains open.

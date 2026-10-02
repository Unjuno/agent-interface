# Issue #6680 — finite safe-diagnosis/recovery policy comparison

This additive T0 tests one limited contrast: after a timestamped trajectory residual and confirmed input release, does one bounded read-only observation support better recovery decisions than fixed-reobserve/fixed-reset policies in identifiable synthetic worlds, while remaining UNKNOWN/YIELD on mixed, unsupported, or ineligible evidence?

The hypothesis and stopping rules are in [PREREGISTRATION.md](PREREGISTRATION.md). The initial label-only construction attempt is retained as historical construction evidence; the formal-candidate source set is now [temporal_fixture.json](temporal_fixture.json) and [temporal_oracle.json](temporal_oracle.json), with separate standard-library [temporal_candidate.py](temporal_candidate.py) and [temporal_auditor.py](temporal_auditor.py). Candidate sees the frozen trajectory, predictor, numeric timestamped observations, lease receipts and signature/action map, but never hidden fault or effect labels. The independent auditor reads raw output and oracle.

## Current disposition

Latest source-review base: `a28fd4456ebfd0c181e14e5f018627d7e57b856a`; #6709 is unrelated #6695 postrun documentation, while #6708's unrelated pre-Python auditor launch STOP was inspected for execution-path lessons. No same residual-recovery comparison was found; #6705's explicit input guard/release semantics remain complementary.

**Preformal construction only; formal candidate/auditor/container/retry counts are 0/0/0/0.** Temporal-model tests pass 13/13 and legacy construction tests 5/5; a fresh host candidate run emitted 20 rows and the independent auditor returned `PASS_METHOD_SCOPED`, zero errors. Re-run raw/audit hashes match the retained temporal construction outputs. The retained report includes wrong-recovery, useful-effect, and separately modeled post-recovery residual metrics. These host runs are not formal outcomes. Full chronology and superseded artifacts are in `CONSTRUCTION_LOG.md`. Formal execution requires the already requested exact exclusive CPU/container assignment and a fresh source/main/image freeze. WSLc is unavailable on this macOS host; no shared Engine or another task's machine may be borrowed.

The assay is deterministic and synthetic. Even a method-scoped PASS cannot establish real fault identifiability, safe recovery in a GUI, live control benefit, or authority.

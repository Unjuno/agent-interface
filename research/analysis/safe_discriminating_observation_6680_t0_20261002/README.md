# Issue #6680 — finite safe-diagnosis/recovery policy comparison

This additive T0 tests one limited contrast: after a timestamped trajectory residual and confirmed input release, does one bounded read-only observation support better recovery decisions than fixed-reobserve/fixed-reset policies in identifiable synthetic worlds, while remaining UNKNOWN/YIELD on mixed, unsupported, or ineligible evidence?

The hypothesis and stopping rules are in [PREREGISTRATION.md](PREREGISTRATION.md). The initial label-only construction attempt is retained as historical construction evidence; the formal-candidate source set is now [temporal_fixture.json](temporal_fixture.json) and [temporal_oracle.json](temporal_oracle.json), with separate standard-library [temporal_candidate.py](temporal_candidate.py) and [temporal_auditor.py](temporal_auditor.py). Candidate sees the frozen trajectory, predictor, numeric timestamped observations, lease receipts and signature/action map, but never hidden fault or effect labels. The independent auditor reads raw output and oracle.

## Current disposition

The prior allocation's source review and construction history are retained below. A fresh successor allocation used `main` at `c33380b3b08792a331ee11f7aee05e3d41437e3e`, refreshed this branch before formal execution, and checked the intervening main delta for collisions.

**Latest status: formal OrbStack successor A01 `PASS_METHOD_SCOPED`.** One candidate and one separate raw-only auditor completed in a dedicated OrbStack VM; 20/20 rows, zero audit errors, zero OOM, no retries. On the two identifiable synthetic cases, diagnosis had 0 wrong recoveries / 0 repeated residuals / 2 useful effects; each fixed recovery baseline had 1/1; immediate YIELD had 0 wrong and 0 useful effects. Mixed, ineligible, and unsupported diagnosis cases YIELDED without probes. See [the A01 report](FORMAL_A01_REPORT.md), [pre-registration](FORMAL_A01_PREREGISTRATION.md), and retained raw/audit receipts in `formal_a01_orbstack_20261003/`.

The predecessor allocation remains **`HOLD_RESOURCE_BEFORE_FORMAL_START`** with its original formal counts 0/0/0/0; it is not relabeled by A01. Temporal, posthoc and legacy construction tests passed 28/28 before the fresh formal run. V2/V3 failed-gate construction artifacts and all prior outputs remain unchanged. A01's byte-identical candidate/audit hashes to the deterministic v4 construction output are explicitly disclosed in its report; this is a fresh execution receipt, not an independent scientific replication.

The assay is deterministic and synthetic. Even a method-scoped PASS cannot establish real fault identifiability, safe recovery in a GUI, live control benefit, or authority.

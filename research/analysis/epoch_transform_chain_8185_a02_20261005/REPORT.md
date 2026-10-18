# A02 exact affine oracle result

**Disposition: PASS_METHOD_SCOPED — finite method scope only.**

The frozen corpus contains 20 cases and 25 exact hidden edge-assignment worlds. The candidate saw public affine coefficient bounds and calibration events; it did not receive exact matrix assignments, strata, or invalid labels. The independent auditor separately composed oracle-only matrices and checked mapped point/region hulls and decisions. All mapped hulls and decisions matched the exact oracle.

The typed graph admitted all 3 exact-safe composed-affine cases. The calibrated single-map baseline also processed every row and returned UNKNOWN on 3 of those cases; the graph returned UNKNOWN on 0, a 100% false-UNKNOWN reduction. There were 0 false admissions; all 11 invalid controls failed closed. The independent auditor verified the inverse-shear pair composes to identity and the epoch path is exactly 7→8→9.

The baseline uses only the predeclared uniform scale/offset calibration table. A public `calibration_event.refresh_to` changes its state immediately before scoring that row. It never refuses because a transform graph contains multiple edges. The three composed baseline refusals therefore result from its mapped geometry under that frozen comparator, not a path-length rule.

Candidate and independent auditor each ran once in the pinned linux/arm64 Python 3.12.15 OrbStack container with networking disabled, one CPU, 512 MiB memory, and read-only root. The 5-test construction suite passed before freeze. No formal retries or post-result repairs occurred.

This result covers authored finite affine arithmetic only. It does not validate Windows DPI virtualization, native APIs, GUI/input behavior, hit testing, timing, semantic effect, or product readiness. T1 remains out of scope.

Allocation: `UNJUNO-8185-EXACT-ORACLE-A02-20261005-01`. Freeze SHA-256: `f3e39af8d33beb57579d265fb62685b1e128aeacdce0138cda475e4b0002148f`. Candidate SHA-256: `d749d94fed88382f8724136a6d4e6d43b30a487ae84b0f8444eb8fa69d01df96`. Auditor SHA-256: `a309709aebca7ce3f9cc851f64c73eb804fd654c0c0d69b03e439ed654fb2989`.

Manifest note: a pre-formal broad file scan also hashed construction-only CPython cache files. The formal one-shot commands mounted only the frozen candidate/auditor scripts and data; those cache files were never used. After cache cleanup/reconstruction their hashes did not match. `RUN_FREEZE_AMENDMENT.json` records the discrepancy and verifies that every actual formal dependency remains byte-identical to its freeze hash. No formal role was rerun.

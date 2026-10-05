# Issue #8157 A04 audit-only result

**Disposition: `PASS_RAW_RECONCILIATION_ONLY`.** The new independent auditor reconstructed all 200 preserved A02 sequences and 2,400 public prefixes with zero mismatches. It independently confirmed 434 numeric intervals on eligible in-model hazard prefixes, with no oracle-containment error. All ten profiles contribute 240 prefixes each.

The original A02 auditor report contains exactly 98 reconstruction mismatches: 49 point estimates and 49 intervals, all in the `occlusion` profile. A04 reproduced the candidate outputs from each prefix alone, without using later samples to classify earlier prefixes. Published A02 source and artifact manifests and all A04 frozen raw/source hashes pass. The bound, timestamp, removed-sample, oracle-hazard-label and interval-endpoint mutations were each rejected (5/5).

This result only reconciles retained A02 bytes and the recorded auditor discrepancy. A02's original `FAIL_METHOD` remains unchanged and unscorable; A03's `STOP_AUDITOR_RUNTIME_ERROR` remains preserved. A04 is not a TTC method PASS, does not rerun a candidate, and says nothing about real vision, GUI/game behavior, runtime policy or safety.

Candidate and generator invocations: 0. A02 and A03 roles were not repeated. The A04 auditor ran once and exited 0, with zero retries.

Post-run local validation: the A04 mutation/consistency suite passed 8/8, the analytical-index unit suite passed 17/17, and `research/analysis/check_index.py` exited 0 in sparse-checkout mode (it reported only that absent sibling directories were not treated as removals). The frozen A04 auditor was not rerun.

Execution used WSLc 3.0.1.0 and cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/amd64`), `--pull never --network none --cpus 1 --memory 512M`, a read-only source mount, and a separate output mount. WSL reported that swap-limit capabilities/cgroup are unavailable; no swap-isolation or hard memory-enforcement claim is made. See `AUDIT_REPORT.json`, `RUN_RECORD.json`, `FREEZE_A04.json`, and `SHA256SUMS_A04.txt`.

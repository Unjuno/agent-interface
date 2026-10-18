# T0b calibration STOP — Issue #7765

The separate-seed fixed-gain calibration did not pass independent replay. Candidate produced the complete 240-row grid and internally selected 0.9, but the frozen auditor exited 1 with 605 reconstruction errors. Subsequent code inspection localized the defect to the auditor's independent cross-coupling RNG reconstruction: the plant consumes provisional coupling draws before replacing them, while the auditor did not. Because the sole auditor invocation was spent, the auditor was not corrected/re-run against this allocation. No fixed gain is certified and no held-out candidate/auditor run occurred.

Raw table, candidate selector output, failed auditor output, and the STOP receipt remain immutable in this directory. A corrected protocol must use a fresh allocation and seed range; the earlier gain=0.9 output is not calibration evidence.

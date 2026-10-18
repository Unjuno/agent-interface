# Current-main replay of the V39 cancel/release candidate

This additive replay checks whether the already-frozen cancellation/release candidate still composes with current main after it advanced from the original A01 source freeze. It does not alter or replace the original A01 result.

**H:** The frozen bridge/owner candidate and its existing fake-display tests remain compatible with current-main ExecutorV12 and the retained owner/V39 bridge contracts.

**T:** On the integration tree formed by candidate commit `61502e45d40b67b6d588b4e8357e42fde05a9dbe` and current main `563f636203ffd4c71e6a81968f6ad950dc53eaff`, run the six suites listed in `FREEZE.json`, retain stdout/stderr and exit codes, then run the independent raw-only audit.

**D:** PASS only when suite counts and exits match the freeze and `audit.py` verifies the exact main/candidate commits, selected Git blobs, all raw logs, exit receipts, and package hashes. Any mismatch is FAIL; no GUI/game claim is permitted.

**C:** Passing fake-display composition tests may still miss X server timing, OS input behavior, application consumption, useful feedback, recovery, or gameplay effects.

**U:** This is a deterministic host regression replay only. It is not real X11, application or game behavior, live threat response, useful feedback, bounded recovery efficacy, safety, latency, or an allocation.

Run `python3 run_replay.py` once in a clean checkout of the frozen integration tree, then `python3 audit.py`. The runner refuses to overwrite `raw/`. `SHA256SUMS.txt` covers the complete replay package.

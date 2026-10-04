# Current parent qualification (evidence-only stack)

PR #7662's current head at this qualification is `efb712b1aa6f01d67ed119b266ef479645cfb96a`, based on PR #7602 head `a7f9e9e3c4bd31199bde3a14761783ead619ad08`. PR #7602 already contains the sample-layer guard and its six-layer regression. The child branch was rebased onto #7662 and now changes no controller or test source; it retains the separate frozen six-layer A01 matrix and its parent-sync history as evidence only.

The test/source freeze is `PARENT_SYNC3_FREEZE.json` (candidate code commit `df8f3e4d96d96fcbb76396ba958fb0edc0d456da`). The focused current-parent command passed 1/1. It covers 60 contradictory/malformed values across both DOWN/UP rows and six evidence layers, checks interval withholding, and preserves the positive pair. Exact output and exit code are in `raw/PARENT_SYNC3_TARGET_OUTPUT.txt` and `raw/PARENT_SYNC3_TARGET_EXIT.txt`.

The frozen A01 comparison remains tied to original baseline `a1cbc360d59ca90ceb6cc5cf2ca31be5e64c0414`: 20 parent false accepts, 0 candidate false accepts. No historical raw or source snapshot was rewritten. The raw-only saved-result/hash audit output and exit code are retained under `raw/PARENT_SYNC3_AUDIT_*`. The final recheck ran on a disposable copy after those records entered `SHA256SUMS`; it matched the saved audit output exactly and returned `PASS_SAVED_RESULT_AUDIT`.

This is deterministic projection evidence only. It does not establish physical key timing, application consumption, useful feedback, recovery, live threat-control, or MAP01 completion. No game/model/GUI/input/allocation ran.

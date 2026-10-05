# Construction pilot result — Issue #5865

**Disposition:** `PASS_AUDIT_CONSTRUCTION_ONLY`; **formal T1:** `HOLD_T0_CLASSIFIER_SOURCE_UNAVAILABLE`.

Allocation `T1-CONSTRUCTION-PILOT-20261005` executed one candidate over 12 fixed producer cases and one independent audit against a separate oracle truth file. The audit found 0 errors and 0 false negatives. The candidate certified 5 of 8 oracle-eligible negative requests (62.5% overall): stable controls 5/5, virtualized no-match requests 0/2, and mutation no-match requests 0/1. It returned a match for the stable positive control and abstained on partial virtualized/mutation producer receipts, including a below-viewport target.

The pilot supports freezing an 80% minimum useful-coverage threshold for a later held-out stable-control set. The threshold is specific to this fixture and is recorded in `threshold_pilot.json` before a held-out run. No formal held-out run occurred because the prior T0 negative-search classifier, which Issue #5865 requires remain unchanged for T1, could not be recovered from current `main`, open PR #8136, or the available local worktrees. The newly implemented producer helper is not a substitute for the missing T0 classifier.

CUA inspected a local synthetic browser page: stable controls were individually present in its accessibility tree; the virtualized canvas exposed only a viewport description and visible rows 0–5, while target row 17 (“Delete”) was absent. This is not a native app or accessibility API measurement.

Construction tests: `python3 -m unittest -v` — 13 passed. Reproduction of the retained pilot requires running `python3 run_candidate.py` and `python3 audit_pilot.py` once each; these are preserved outputs and should not be rerun as a new scientific allocation. No runtime, live application, user task, latency, action-authority, or product claim follows.

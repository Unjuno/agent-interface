# V39 HUD diagonal anchor search A04

Offline CPU construction comparison on current main `677e95fce6e5d7357d3c4c16588cdedfa31bfd69`.
The candidate compares the retained eight-axis anchor fallback with a 24-offset
radius-2 square fallback on one fixed set of historical HUD frames and new
synthetic diagonal translations. No candidate retry was made.

## H/T/D/C/U

- **H:** Adding diagonal offsets to the exact-center-first V39 HUD reader lets
  its bounded fallback recover diagonal pixel translations that the existing
  eight-axis fallback reports as `unknown`, while retaining zero wrong observed
  values and unknown results for blank HUD regions.
- **T:** On 13 retained, manually labelled health frames, test the unmodified
  eight-axis policy and a 24-position square policy against each baseline frame,
  all 16 diagonal shifts in `{−2,−1,1,2}²` (208 cases), and 13 blank-ROI
  controls. Record elapsed CPU time for each policy on the same inputs.
- **D:** PASS if both policies read 13/13 baselines correctly, the square policy
  reads 208/208 diagonal cases correctly, has no wrong observed value, and
  returns `unknown` for all 13 blank controls. Otherwise retain the failure.
- **C:** These are fixed historical pixels with synthetic integer translations;
  they do not model capture jitter or live HUD changes. The 24-offset policy
  may encounter conflicting neighboring glyphs; the reader must fail closed.
- **U:** One local Windows CPython 3.11.9 / NumPy 2.4.6 / Pillow 10.2.0 run and
  one 13-frame corpus. No cross-domain images, brightness/contrast/JPEG change,
  live capture, GUI/game, model, OS input, physical release, task effect, or
  MAP01 progress was tested.

## Relation to the neighboring A04 diagnostic

PR #8680 tested the unchanged A03 axial policy on eight diagonal translations per frame (104 cases) and found 2 correct reads, with the rest unknown. This package tests a different candidate policy: a 24-offset radius-2 square fallback across all 16 frozen diagonal translations (208 cases), while retaining the axial policy as comparator. It is a policy successor on the same fixed corpus, not a rerun of the same candidate arm.

## Result

The frozen candidate passed its decision gate. The existing eight-axis policy
read 4/208 diagonal cases and left 204 unknown; the square policy read 208/208
correctly. Neither policy produced a wrong observed value. Both policies kept
all 13 blank controls unknown.

Across 221 timed inputs (baseline plus diagonal cases), the single-run median
was 11.51 ms for eight-axis search and 34.57 ms for square search; nearest-rank
p95 was 12.73 ms and 37.14 ms. This is approximately 3.0× scan time in this
one local run, so the expanded scan remains an offline candidate and is not
adopted into runtime. The result demonstrates bounded synthetic diagonal
recovery on this corpus, not general HUD robustness.

After the candidate run, main advanced through PR #8669 to `0455b0079ca29bcfe85153f280e592f5e96528f6` and then to `743ae74ec5be2472ff27fa06fe13d5ecf8534de5` for an unrelated cleanup-ID experiment. The reader v1-v3 modules, transfer freeze, 13-frame corpus, and A03 result/audit remain unchanged between the frozen A04 base `677e95f` and current main `743ae74`; the path-scoped Git comparison is retained in `results/current_main_continuity.json`. The candidate was not rerun.

The candidate ran once. Audit v1 failed before reading the result because its
repository-root calculation pointed outside the checkout; the raw failure is
retained. Audit v2 changed root selection, independently recomputed all 234
candidate/blank rows, and passed 5/5 mutation controls. The candidate result was
not rerun. See `FREEZE_A04.json`, `FREEZE_AUDIT_V2.json`, `RUN_RECORD_A04.json`,
and `results/` for source identities and raw output.

## Runtime availability follow-up

A host preflight on 2026-10-09 found WSL `2.7.13.0` and no `wslc.exe` command; the repository runbook identifies WSLc as included with WSL `2.9.3+`. The original Windows CPython result is therefore retained as exploratory evidence and does not meet the preferred WSLc route. No WSL update or restart was performed. See `results/wslc_host_preflight.json`; a future WSLc execution must be a separately frozen successor, not a replay or relabeling of this consumed candidate.

Ubuntu remained listed as a running WSL distribution after the probe and a 10-second idle interval. To preserve the shared environment, WSL was not updated or restarted. The WSLc successor is therefore deferred until the required host runtime can be made available without interrupting active work.

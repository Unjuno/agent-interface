# Construction attempt 1 — retained failure

The initial checker expected an id on each input_admission row and returned STOP_UNEXPECTED_UNMATCHED []. The frozen schema omits id/step on that row. This was a checker-construction failure, not a raw experiment failure. The corrected checker rebuilds scope from the preceding step_started event and verifies all 634 rows; the failed attempt was not relabeled.

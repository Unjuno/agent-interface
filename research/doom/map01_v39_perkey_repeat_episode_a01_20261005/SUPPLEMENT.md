# A01 observed result and mutation follow-up

The frozen baseline refused the four-row stream with `exactly one retained down/up pair is required`. The successor candidate retained two non-overlapping F8 episodes under distinct actuation IDs; both intervals were 50,417–58,458 ns as inherited from duplicated source rows. The independent raw-only audit reproduced both rows and returned `PASS_RAW_RECONSTRUCTION_SCOPED`. These numbers remain synthetic fake-display brackets; the 1 ms shift is fixture construction, not measured timing.

The initial mutation-suite attempts exposed two test assertion construction errors. Their failed transcripts are retained in `results/a01/test-output-a01.txt` and `results/a01/test-output-v2.txt`; they did not rerun the baseline, candidate, or independent audit. The final separate supplement (`test_repeat_final.py`) passes five checks: positive raw/candidate agreement and rejection of duplicate actuation collapse, incomplete pair, mixed context, and overlap. A failure transcript is not silently replaced by the final one.

This supplement was written after the one-shot baseline/candidate/audit runs. It does not change or rebind the A01 freeze and is not part of the frozen candidate source set.

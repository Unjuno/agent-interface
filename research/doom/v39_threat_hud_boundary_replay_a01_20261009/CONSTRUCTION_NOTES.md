# Construction stops (preserved)

These were harness setup stops before scientific evaluation; neither is a live or candidate outcome.

1. The initial source-row selector expected the source observation (sequence 166) to have the cover ID used by later rows. It was actually emitted under the preceding `plan-4-primary-0-1` ID. Correction: bind the one exact source sequence independently, then require cover ID only for later rows.
2. The next count check expected 52 rows including source. The frozen interval is one source row plus 52 subsequent rows (sequences 167–218), 53 total. Correction: distinguish source from post-source observation count.
3. A later audit run used `HERE.parents[3]` as repository root even though `HERE` is the package directory; the correct root is `HERE.parents[2]`. The audit could not open the frozen input path. The candidate uses `Path(__file__).parents[3]` because `__file__` is the script file. Preserve the first candidate result and reproduction-02/03 candidate outputs; the audit STOP is a checker path error, not a scientific outcome. The corrected audit uses the exact worktree root.
4. The first audit after adding current-source identity checks stopped because candidate JSON omitted the Git blob ID, although the candidate had checked it before processing input. Preserve reproduction-04's candidate output and audit STOP. The corrected candidate serializes the blob and writes to the separate reproduction-05 output, which is the final candidate/audit pair.
5. The adjacent 36-test controller suite first stopped in one case before its body because Windows C: had no free space for `tempfile.mkdtemp()` (`WinError 112`), in normal and optimized modes. The same exact suite then passed 36/36 in each mode with `TEMP` and `TMP` redirected to an existing D: scratch directory. No cleanup or mutation of C: was attempted.

`reproduction-03/AUDIT.json` passed the earlier raw-row/transition checks before the independent auditor was strengthened to require the candidate to serialize the exact Git blob. `reproduction-04` preserves that stricter audit's initial STOP; `reproduction-05` and `reproduction-06` pass the strengthened audit.

Both corrected conditions are frozen and exercised by `replay.py`; the original successful `RESULT.json` is retained without overwrite.

# #1825 disposition — superseded predecessor drift

Final disposition: **STOP_SUPERSEDED_PREDECESSOR_DRIFT** for the intended successor claim.

The retained #1825 formal and independent audit are internally valid for the source-frozen #1825 model:
- candidate/oracle mismatch 0;
- stale/contradicted ACTION_SAFE admissions 0;
- exact independent digest agreement;
- formal1 / reruns0.

However, #1825 was opened from the earlier #1817 construction state. Before #1825 could be proposed for main, #1817 completed its source freeze and then stopped at the monolithic formal execution envelope; its final frozen source was retained. The final #1817 model is not byte/semantic-equivalent to the #1825 model.

Decisive discriminator:
- final #1817 frozen source Git blob: `acea97ab251c7a603ae95e0041b4643cad800c60`;
- #1817 operation alphabet: `OBS0, OBS1, VALIDATE, COMMIT, ADVANCE, CONTRADICT, REOBSERVE, ACTION` (8 operations);
- #1825 operation alphabet: `OBS0, OBS1, VALIDATE, COMMIT, ADVANCE, CONTRADICT, TRY_ACTION` (7 operations);
- exhaustive depth-8 node cardinality: #1817/#1829 = **19,173,961**, #1825 = **6,725,601**.

Therefore #1825 does not preserve the exact final #1817 corpus/semantics and cannot be represented as the planned one-factor construction-gate successor. Its PASS is retained only as model-local evidence on this branch and is **not eligible for main promotion under the stated successor claim**.

The canonical successor is #1829, merged by PR #1846, which explicitly preserves the exact final #1817 depth-8 universe and changes only the execution envelope through immutable top-level-prefix batches. #1829 passed with independent DP audit.

No #1825 formal rerun, replacement, source tuning, runtime change, or PR-to-main is authorized from this disposition.

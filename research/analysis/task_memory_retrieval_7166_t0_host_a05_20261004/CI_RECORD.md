# Local validation record

- Targeted construction suite: `python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a05_20261004/test_package.py` — PASS, 4/4. Includes the no-op regression: all six mutation functions must change raw rows.
- `python3 -I -m py_compile` on builder, candidate and auditor — PASS.
- Analysis result index: `python research/analysis/check_index.py --write` refreshed 653 entries; subsequent `python research/analysis/check_index.py` PASS.
- Analysis checkout-dependency test: `python -B -m unittest discover -s research/analysis -p 'test_analysis_checkout.py' -v` — PASS, 1/1.
- Research workspace index tests: `python -B -m unittest discover -s research -p 'test_*workspace*.py' -v` — PASS, 22/22; `python research/check_workspace_index.py --git-tree` PASS (159 top-level directories).
- Formal candidate — exit 0, 72 rows.
- Formal independent auditor — exit 0, base audit PASS, mutation effectiveness 6/6, mutation rejection 6/6, `PASS_METHOD_SCOPED`.
- Full analysis-index GitHub workflow and full repository CI were not run; no workflow was added or changed. Do not generalize selected local checks to full repository CI.

Container was not used: the same-day OrbStack content-store failure is retained
at Issue #7383 comment #5976132398 and was not retried. This is not container
enforcement evidence.

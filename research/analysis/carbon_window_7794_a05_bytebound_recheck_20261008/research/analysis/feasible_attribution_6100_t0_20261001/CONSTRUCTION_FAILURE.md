# Construction audit/test failures — preserved

The first pre-freeze construction run produced 5 cases, 23 feasible coalition arms and 460 attempt rows. Its baseline independent audit passed. The 9-test mutation suite then exposed a fail-closed robustness defect: the omitted-arm and swapped-label mutations caused the auditor to raise `KeyError` while attempting Shapley recomputation on an incomplete coalition map, instead of returning a structured audit failure. Candidate data and the baseline independent audit were not altered to hide this.

The auditor was changed to stop attribution recomputation unless the observed feasible coalition map is structurally complete. The mutation tests were rerun; exact construction outputs remain under `construction_raw.jsonl` and `construction_audit.json`. This was a construction/auditor robustness failure, not a scientific result or official frozen run.

Initial Docker command sequence was candidate → auditor → `python -m unittest -v test_attribution.py`. Candidate: 5 cases / 23 coalitions / 460 attempts. Baseline raw audit: `PASS_METHOD_SCOPED`, errors `[]`. Mutation suite: 7/9 passed; exact failing controls were `test_auditor_rejects_omitted_feasible_arm` (`KeyError: 'B'`) and `test_auditor_rejects_swapped_factor_labels` (`KeyError: 'A'`) at Shapley lookup. The shell exited 1; no official freeze/run had begun.

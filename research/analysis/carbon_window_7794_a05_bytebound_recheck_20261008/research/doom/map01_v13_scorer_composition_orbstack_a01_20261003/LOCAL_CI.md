# Local CI record

On CPython 3.14.5, the existing `map01-finite-clear-artifact-successor-3156.yml` construction/guard commands were run locally after the one-shot candidate and auditor had completed:

```text
python3 research/orchestration/o3-g7/global-owner/test_formal_allocation_global_owner_v1.py       12/12 PASS
python3 research/doom/test_map01_scorer_stdio_adapter_v1.py                                      5/5 PASS
python3 research/doom/test_session_map01_v13.py                                                  4/4 PASS
python3 research/doom/test_audit_map01_measurement_integration_v1.py                            5/5 PASS
python3 research/doom/test_audit_map01_terminal_score_agreement_v1.py                            5/5 PASS
```

This is repeatable CI construction/guard verification, not another candidate or auditor allocation. The frozen candidate/auditor counts remain 1/1, retries 0. The workflow's GitHub allocation-owner gate and live MAP01 one-shot were not invoked. `git diff --check`, JSON parsing of the retained manifests, and Python compilation of `audit.py` also passed locally.

The PR's two additional checks were also replayed locally while GitHub runners were queued:

```text
python3 .github/check_public_navigation.py                                      PASS (26 documents, 1,622 links)
python3 -B -m unittest discover -s research -p 'test_*workspace*.py' -v       21/21 PASS
python3 research/check_workspace_index.py --git-tree                           PASS (156 top-level directories)
```

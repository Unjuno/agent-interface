# Action-only adaptation A02: label-blind pipeline audit

Successor to the explicitly conditional action-only adaptation branch in [Issue #5749](https://github.com/Unjuno/agent-interface/issues/5749). This new rung addresses A01's noted target-label/scorer coupling, not the original human-preference question. Historical A01/T0 outputs remain unchanged.

H/T/D/C/U, the frozen input split, one-shot commands and limits are in `PROTOCOL.md`; exact identities are pinned in `FREEZE.json`. The policy input and scoring key are intentionally separate files under `fixtures/`. The candidate output does not carry target labels or score outcomes. Candidate, scorer, and independent raw-only auditor run in distinct interpreter processes; this is dataflow separation, not hostile-code isolation.

Construction suite:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

After preregistration and freeze are published, formal command order is candidate → scorer → auditor, exactly once each. Full repository CI remains GitHub Actions; local applicable validation is the package suite, Python compilation, `git diff --check`, and sparse-aware analysis-index check.

# Issue #57 paired route analysis T0

This study exercises a synthetic paired all-attempt estimator requested on
[Issue #57](https://github.com/Unjuno/agent-interface/issues/57). It is a
measurement-method prerequisite, not a new live benchmark or a result about
integrated-route performance.

- `PLAN.md`: H/T/D/C/U and frozen interpretation
- `fixture.json`: 7 pairs / 14 attempts, null, planted effect and route failures
- `candidate.py`, `audit.py`: separate analyzer and independent reconstruction
- `test_t0.py`: local construction and mutation checks
- `FREEZE.json`: one-shot Docker allocation and source digests
- `results/<allocation>/`: runner, image, raw output and audit

Construction command:

```powershell
python -B -m unittest research.analysis.paired_route_estimator_57_t0_v1.test_t0 -v
```

No adjustment, causal estimate, live-task completion, safety, cost or speed
claim follows from the synthetic output. See the retained report after the
formal allocation completes.

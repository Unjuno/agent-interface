# Issue #6684 — relational coordinate-bounds finite method result

## Result

Allocation `relational-coordinate-bounds-6684-t0-20261002-06` completed as
`PASS_METHOD_SCOPED`. One candidate process and one separately implemented
exhaustive auditor process ran; retries: zero. All nine cases and 98,414
concrete integer states were audited. There were zero false admissions.

In the three exactly safe common-mode translation cases, BOX returned
`UNKNOWN_REOBSERVE` in all three while RELATIONAL admitted all three. On the
three independent-error controls, both methods made identical decisions. The
unsafe scale-boundary, adjacent-collateral, and independent-measurement-error
controls were refused. The conclusion is limited to this authored finite model;
it is not GUI, runtime, action-authority, safety, or product evidence.

## H / T / D / C / U

The exact preregistered hypothesis, enumerated cases, decision gates, controls,
and uncertainty are in [`PREREGISTRATION.md`](PREREGISTRATION.md), frozen by
[`FREEZE.json`](FREEZE.json). Briefly: retaining a shared translation variable
reduces conservative refusals on the specified safe common-mode cases without
false admissions, but gives no advantage on independent-error controls. The
auditor reconstructed exact extrema and safety for every state and verified
candidate bounds were supersets.

## Reproducible evidence

- Formal output: `results/relational-coordinate-bounds-6684-t0-20261002-06/formal-01/`
- `RUN_RECORD.json` binds freeze digest, source commit, commands, exit statuses,
  process counts, retry count, and the raw artifact hashes.
- `SHA256.json` covers the environment, candidate raw output, independent audit,
  and candidate/auditor stdout and stderr; all seven entries were independently
  rehashed after the run.
- Main was updated disjointly between baseline and launch. The runner recorded
  the exact changed paths; none touched the protected paths. The result was
  executed on local arm64 CPU without a container. Two unrelated OrbStack
  containers were left untouched because this finite method fixture needs no
  GUI, Engine API, special isolation, or application runtime.
- The first construction test exceeded a responsive runtime at 9,529,569
  worlds/case and was interrupted before formal execution. The fixture was
  bounded to at most 100,000 states/case and the corrected 11-test construction
  suite completed in about 1.04 seconds. T0 preflight records remain at
  `results/preformal/source-preflight-failure.json` and
  `results/prelaunch-01/STOP.json`; the allocation-04 preformal STOP remains at
  `results/relational-coordinate-bounds-6684-t0-20261002-04/preformal/`.
  Allocation 05 raised a `KeyError` before formal output creation because the
  runner looked for `protected_paths` at the wrong JSON level; its retained
  process log is in the task execution transcript. Allocation 06 is the first
  completed formal allocation. No STOP/exception invoked candidate or auditor,
  and none was erased or counted as a retry.

## Revalidation

```bash
python3 -B -m unittest discover -s research/analysis/relational_coordinate_bounds_6684_t0_20261002 -p 'test_*.py' -v
python3 research/analysis/check_index.py
```

The local construction suite passed 11/11 after the formal run; retained-results
index and `git diff --check` passed. References for the mathematical analogy
are in the preregistration; they motivate the abstraction only and do not
validate this experiment's GUI relevance.

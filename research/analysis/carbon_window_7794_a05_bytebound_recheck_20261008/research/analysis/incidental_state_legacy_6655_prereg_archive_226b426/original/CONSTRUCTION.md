# Construction evidence

- Base main: `9a573b00dc595e64d09387e567c85e10b61a46c1`.
- Runtime: local Windows CPython 3.11.9; standard library only.
- Command: `py -3.11 -B -m unittest -v` from this package directory.
- Result: 9 tests passed, exit 0 (0.082 s) after current-main source freeze.
- `py_compile` of fixture, candidate, auditor and tests had passed before the base-SHA-only fixture update; the post-update unittest import/execute also parsed all four modules.
- Controls cover the full seven-case grid, positive/negative/null scenarios, required-effect retention, missing/relabelled diffs, crossed seed, incomplete restoration, unowned shared state, and assignment-order corruption.
- These are construction tests, not candidate/auditor formal invocation counts. Formal remains 0/0 here.
- No container, GUI, model, network request, GPU, user data, or external state was touched.

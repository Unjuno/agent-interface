# Preformal design STOP — Issue #6503

Allocation `QUIET-SUPERVISION-VIGILANCE-6503-T0-20261002-01` was **not frozen or formally invoked**.

## Construction checks

- Host: macOS arm64; CPython 3.14.5.
- `python3 -B -m unittest -v test_t0.py`: 6/6 passed.
- `python3 -B -m py_compile candidate.py auditor.py run_candidate.py run_auditor.py`: passed.
- `git diff --check`: passed.
- Formal candidate: 0 invocations. Formal auditor: 0 invocations. Retries: 0.

## Stop reason

Independent preformal protocol review found that the package only constructs and audits opportunity/display rows. It does not implement response-category scoring for hit, miss, false alarm, response delay, or no-response, despite those being central to Issue #6503's T0 material/scorer gate. There are no human observations, and no prespecified response-scoring fixture. Calling the current ledger a scorer validation or vigilance result would exceed the code and data.

Disposition: `STOP_PREFORMAL_SCORER_GATE_MISSING`. Do not infer participant behavior, perceptual sensitivity, response criterion, time-on-task decline, checkpoint efficacy, or human benefit from the 6/6 construction suite. This is a design STOP, not a formal method FAIL and not evidence for or against the Issue hypothesis. The partial package and tests are retained for transparent diagnosis; a useful successor requires a separately reviewed scoring contract and must not treat invented responses as human data.

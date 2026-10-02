# T12 construction log (pre-freeze)

Construction is not the formal allocation. Both attempts occurred before source freeze; no formal raw was generated.

## Attempt 1 — FAIL

- Command: `python3 -B -m unittest -v test_candidate.py`
- Exit: 1; five tests ran, three passed, and the 15-control test failed for `boolean_tolerance_alias` and `boolean_output_alias`.
- Exact failure: the mutation harness raised `AssertionError: ... identity mutation` at its ordinary Python `==` comparison.
- Root cause: Python considers `False == 0`; the JSON values are different (`false` and `0`), but mutation precondition, identity and whole-document comparisons used Python structural equality. This made valid type-confusion mutations appear unchanged before the auditor could test them.
- No formal invocation or raw output existed at this point.

## Repair and construction attempt 2 — PASS

- Test-first reproduction already existed in `test_candidate.py`; it failed on the two boolean/integer mutation controls above.
- Minimal repair: use canonical JSON bytes (`sort_keys`, compact separators, `allow_nan=False`) for mutation preconditions, identity comparisons, corpus-change checks, and mutation-result nonidentity. Strict input/output validators separately use exact Python types so booleans cannot pass as integers.
- Command: `python3 -B -m unittest -v test_candidate.py && python3 -m py_compile candidate.py run_experiment.py audit_raw.py test_candidate.py && git diff --check`
- Exit: 0; five tests passed, including all 15 nonidentity/rejection controls; compile and whitespace checks passed.

The corrected construction suite is run again after freezing the refreshed current-main base. The first construction failure remains part of the record and is not silently erased by the corrected result.

## Index-check command correction — tool-path STOP

- A post-refresh shell chain ran the unit suite, `py_compile`, and `git diff --check` successfully, then exited 2 because it invoked `research/analysis/check_index.py` relative to the experiment subdirectory. The script was not found at that path; no index check ran in that invocation.
- This was a command working-directory error, not a test or scientific failure. Corrected invocation is from the repository root, where the script path resolves. Preserve the original exit and use only the corrected command for the freeze gate.

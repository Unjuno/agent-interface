# Run record

## H / T / D / C / U

- **H:** the v1 audit omitted material fields already published in its result and could false-pass saved-result corruptions; A01 also failed to distinguish an absent key from a key explicitly set to null.
- **T:** compare the retained RESULT against pinned raw Git blobs; replay the original five corruptions plus missing-null-key against v1, A01 and A02.
- **D:** A02 PASS only for exact unchanged-result reconstruction, six reproduced v1 false passes, and 6/6 rejection by each A02 path.
- **C:** scope metadata such as the posthoc label and absence of live allocations comes from the pinned package; this test does not validate the meaning of a game effect.
- **U:** deterministic host-CPU reanalysis only. No formal experiment or live control allocation.

## Freeze

- Repository: Unjuno/agent-interface
- Analysis input base: b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3
- Parent evidence package: c837ad535eed085d95744ad0a9680535a5bb7143
- Raw report SHA-256: 719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687
- Raw event stream SHA-256: 2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381
- Runtime: Windows host, Python 3.11, standard library only
- Scope: saved artifacts and temporary copies; no GUI, game, model, input, Docker, GPU, or WSLc
- Candidate output: CANDIDATE.json (one-shot; refuses overwrite)
- Independent output: AUDIT.json (one-shot; refuses overwrite)
- A02 outputs: CANDIDATE_A02.json and AUDIT_A02.json (one-shot; refuse overwrite)

## Executions

1. A pre-freeze reproduction copied each mutated RESULT and the frozen original v1 auditor into temporary directories. The first five mutations returned exit 0 and v1 PASS 5/5. The original package and its saved RESULT/AUDIT were not changed.
2. A01's test suite rejected those five mutations, then A01 candidate and independent-audit outputs were run once and retained as CANDIDATE.json and AUDIT.json.
3. Code review found A01's get-based comparator accepted deletion of a field whose expected value was null. That result and source were retained unchanged.
4. A02 freezes the same b67 raw report/event blobs and c837 parent result package, plus A02-specific source hashes and the sixth missing-null-key corruption. Its test suite was run before the candidate: v1 passed all six, A01 passed the new sixth case, and both A02 paths rejected all six. MUTATION_TEST_A02.json records the test-source SHA-256 and every mismatch field.
5. audit_v2_a02.py was run once to create CANDIDATE_A02.json. independent_audit_v2_a02.py was then run once to create AUDIT_A02.json using a separate grouped-stream reconstruction.
6. After the A02 outputs, the final mutation test was rerun without recording, package hashes and Python source compilation were checked, the workspace-index workflow's 22 tests passed, its index check found 159 directories, and git diff --cached --check passed.

The exact outcomes and corrupted fields are retained in the A01 files and in MUTATION_TEST_A02.json, CANDIDATE_A02.json, and AUDIT_A02.json. The raw traces remain Git blobs at the commits recorded in FREEZE.json and FREEZE_A02.json.

# A05 run record — terminal baseline expectation failure

- Allocation: `V39-V15-PREPOST-A05-AUDIT-FIX-20261005-01`
- Candidate/runtime invocations: 0
- Auditor invocations: 1
- Retries: 0
- Auditor source SHA-256: `4eb14ceba50c01773349f3783c46ee8da4998deb87a03f53d6096a2573078701`
- Freeze SHA-256: `849a3c7b6b53517ac245d1a58ad961dc34123e1f5d6f656e2f84ec3985a3d49d`
- Runtime: WSLc; image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; network disabled; one CPU
- Formal launch UTC: `2026-10-05T09:00:57.9494241Z`
- Formal exit UTC: `2026-10-05T09:00:58.6984483Z`
- Container exit: 1

Input hashes and provenance matched; 51 of 52 baseline checks passed; all 12/12 frozen mutations were rejected. The sole baseline failure was `a05_normal_trace_sample_binding`: the validator expected the normal-case `pre_batch_sampler` query to hold `[]`, but the immutable raw contains `[65, 74]` in both the named query and its immediately following `keymap_sample_result`. The raw result and query agree. The defect is an incorrect hard-coded expected pre-sample value in the validator; no conclusion about raw trace inconsistency follows.

The auditor emitted a complete JSON result to stdout and exited 1 by the preregistered decision rule. Preserved bytes:

- `RESULT_A05.json` / stdout SHA-256: `aa71aee28c51af4abf857f78d69618e15d07afcbfd4f14f737e0f6ef6c7e2118`
- stderr SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty)
- exit file SHA-256: `6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b`
- pre-run context SHA-256: `76c7c3f763a5824b313120a8f8355fc4b3985abe9d399ae71e3e2847e66fb75c`
- start time SHA-256: `b8fd1e76b34705803a6b86965d25c01c8186b2f9d917d571a139b98e908df9bb`
- end time SHA-256: `cd846b8f10dd8c840f171c92cd9c12e99d116f7f5152ef1b3d90a06f70c0f4cd`

A05 is terminal and was not rerun. Any correction requires a new audit version/allocation. The retained raw, A02 failure, and A03 result are unchanged.

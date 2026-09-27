# Formal result: Issue #3873 / seed 284936

Status: `PASS_INDEPENDENT_RAW_AUDIT` / `RETAIN` (`frozen_efficiency_and_correctness_gates_passed`). OrbStack formal launcher returned 0. All 17 planned host calls have one request, one raw response, one successful broker receipt and a unique thread ID; retries 0. All host receipts state `authority_granted=false`.

| Arm | Task calls | Correct tasks | Input tokens, incl. preflight | Output tokens, incl. preflight | Reasoning tokens, incl. preflight | Elapsed |
|---|---:|---:|---:|---:|---:|---:|
| plain | 6 | 6/6 | 76,126 | 754 | 306 | 60.79 s |
| ephemeral | 6 | 6/6 | 84,539 | 1,136 | 331 | 76.75 s |
| persistent | 2 | 6/6 | 34,739 | 422 | 79 | 35.85 s |

Frozen gates passed: persistent beats both references on cumulative input tokens and planner generations by task 6; cumulative-input break-even is task 2; persistent is descriptively faster than both. Persistent's required task-4 repair succeeded; old-target pointer admissions are zero. All 18 independent fixture submission-history rows (6 per arm) match exact task IDs and expected submissions, and every task's release is verified.

## Scope

This is one finite same-model allocation on the deterministic local Chromium fixture, model `gpt-5.6-luna` / low effort. The observation does not establish production readiness, population performance, broad GUI reliability, human-speed performance, general efficiency, or behavior outside this fixture/protocol. The persistent wall-time advantage is descriptive only for this allocation.

## Reproduction and audit artifacts

- Preregistration: `evidence/formal-seed-284936/run-01/formal-output/preregistration.json`
- Raw requests/responses/receipts, broker mirrors, workspaces and task/runtime histories: `evidence/formal-seed-284936/run-01/`
- Launcher result: `evidence/formal-seed-284936/run-01/launcher-result.json`
- Independent raw audit (also rerun separately after the launcher): `evidence/formal-seed-284936/run-01/independent-audit.json`
- Scored evaluation: `evidence/formal-seed-284936/run-01/formal-output/evaluation.json`
- Frozen source lock SHA-256: `efd0af7e07730c8d0a7d156d6c95a22c7976411eb66f1cfdaa4fc43c5acaa8cc`
- Key result SHA-256 values: preregistration `2c678c177b8ce2aae438153081ef5ae4acb64b3d8c9496d662aac02c0b5c96b0`; evaluation `c00667c499744b9088e83edd5007c0dc8e9b0c656f4dd62c6a303c4131211503`; independent audit `d639f8b790995c256f1b6459539ef1ed7696284e80030d2f3dca1125a698d753`; launcher result `77988bb58989cf4edf75de80ef825693f9a9caaf28327ef3f39999b490b5c11e`.

Predecessor seeds 284932, 284933, 284934 and 284935 retain their distinct STOP outcomes and were not replayed or modified.

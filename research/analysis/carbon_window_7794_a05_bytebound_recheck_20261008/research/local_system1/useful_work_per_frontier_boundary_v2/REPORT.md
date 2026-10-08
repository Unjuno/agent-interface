# Useful work per frontier boundary v2 result

Decision: **`PASS_USEFUL_WORK_PER_FRONTIER_BOUNDARY_RECONSTRUCTED_SCOPED`**.

Fresh harness-only successor to #931. #931 remains retained `FAIL_INTEGRITY`; none of its rejected numeric output is pooled or relabelled.

## Exact retained Chromium accounting

| arm | verified tasks | task-time planner generations | tasks / task-time generation | total generations incl. preflight | tasks / total generation | frontier-free task-time tasks | local observations | durable calls | task6 phase-complete wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plain | 6 | 6 | 1.0 | 7 | 6/7 = 0.8571 | 0/6 | 105 | 36 | 62.754198912 s |
| ephemeral | 6 | 6 | 1.0 | 7 | 6/7 = 0.8571 | 0/6 | 129 | 96 | 80.378859099 s |
| persistent | 6 | 2 | **3.0** | 3 | **2.0** | **4/6** | **136** | **114** | **51.627109593 s** |

Persistent routes were `cold, reuse, reuse, repair, reuse, reuse`; task-time frontier-free tasks are 2,3,5,6. The task4 layout repair uses one planner generation and is not counted as frontier-free.

The persistent arm therefore used one third as many task-time planner generations as each control while completing the same six retained verified tasks. This is not a claim that total work fell by 3x: persistent deliberately increased local observations and durable calls. Those counts, model-visible images, planner generations and wall time remain heterogeneous units and are not added into a synthetic score.

Retained cumulative-wall accounting is preserved: persistent first beats plain by task2 and ends task6 11.127089319 s ahead of plain and 28.751749506 s ahead of ephemeral.

## Integrity / scope

Formal runner invocation1, reruns0. Executed runner/auditor/fixture Git-object hashes exactly matched the pre-formal freeze. Independent audit PASS/errors `[]`. RESULT SHA-256 `62e22091d2e8b6712491b68618a82f1b2714c82436ed78209c33e5c6cc22d5f8`; AUDIT SHA-256 `5b0b3e466b30e301bd49ce02b23cb76d6a2eb5661a0fb7a53a74cb39c24197d8`.

This is posthoc accounting over one retained six-task Chromium allocation. It does not establish population reliability, second-domain transfer, work performed concurrently during an active frontier wait, monetary/energy equivalence, human tempo, or a production System-1 ABI.

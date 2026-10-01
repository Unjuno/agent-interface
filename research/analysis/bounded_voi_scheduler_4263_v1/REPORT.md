# #4263 bounded value-of-information scheduler v1

Decision: **PASS_BOUNDED_VOI_SCHEDULER_SCOPED**.

One source/hash-frozen standard-library formal enumeration compared `FIXED_CASCADE`, `CHEAPEST_FIRST`, and `FROZEN_VOI_POLICY` on the separate frozen evaluation distribution. Formal invocations/reruns/replacements/post-result tuning: **1/0/0/0**.

## Formal result

All three policies had:
- weighted incorrect decision rate: 0;
- required-YIELD violation rate: 0;
- deadline-miss rate: 0.

Primary frozen endpoint, weighted total evidence/computation cost:
- FIXED_CASCADE: **4.32**;
- CHEAPEST_FIRST: **4.32**;
- FROZEN_VOI_POLICY: **2.70**.

The VoI policy therefore reduced this synthetic cost endpoint by **1.62 units / 37.5%** relative to both baselines while preserving the frozen correctness/YIELD/deadline gates. Weighted latency also moved from 4.60 to 2.86, but latency was not needed to claim PASS.

The support-shift cells produced an observation impossible under the development likelihood support. Every policy used the same frozen fail-closed rule and returned `YIELD`; these cells are not counted as hidden correct L/R decisions.

## Construction chronology

Construction-01, before freeze, exposed a 5% weighted error because an empty posterior could fall through to an arbitrary terminal decision. That result is retained in `CONSTRUCTION.md`. Before formal0 only, a shared support-violation=>YIELD contract repaired the defect; construction-02 passed and source/gates were immediately frozen and remotely read back.

A later attempt to launch formal through a user-visible Python surface failed while opening the output path with `PermissionError`. The experiment subprocess was never started, so that wrapper failure consumed zero formal invocation. The actual frozen experiment then ran once in the execution container.

## Independent audit

`audit.py` reconstructs row identity, weights, truth/YIELD requirements, weighted cost, correctness and deadline gates without importing `experiment.py`. It returns `PASS_BOUNDED_VOI_SCHEDULER_SCOPED`, errors=[].

Eight copied-evidence corruptions were tested: wrong decision, row removal, weight mutation, shift laundering, cost laundering, deadline mutation, truth mutation and policy removal. **8/8 were rejected**.

## Scope

This is an exact finite synthetic sequential-selection result. It shows that on the frozen table, choosing the next evidence action by preregistered one-step expected risk reduction per cost can avoid unnecessary evidence work. It does **not** establish real provider token savings, real semantic-model cost calibration, parallel scheduling optimality, distribution-shift robustness beyond the explicit support/YIELD rule, GUI/task benefit, authority changes, or production policy quality.

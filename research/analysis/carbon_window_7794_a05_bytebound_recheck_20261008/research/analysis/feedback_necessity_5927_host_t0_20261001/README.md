# Issue #5927 — finite feedback-necessity host construction

## H / T / D / C / U

- **H:** For a frozen finite task/channel family, transcript-equivalent worlds with disjoint safe-progress actions require a fresh distinguishing exchange; if a common safe-progress action exists, the checker must report no positive lower bound.
- **T:** A host-only standard-library exhaustive construction on two authored cases: a save/modal positive control, a common-safe-action null control, and adversarial mutations for undeclared oracle leakage, stale receipts, falsified candidate lower bound, and relabeling a forbidden effect as safe. Candidate output is raw JSON; an independent enumeration audits it. No GUI, model, game, network, GPU, container, or task effect is involved.
- **D:** `PASS_HOST_CONSTRUCTION_ONLY` requires the positive case's minimum to be one exchange, the null case's minimum to be zero, and every mutation to be rejected by tests/auditor. This does **not** satisfy Issue #5927's preregistered disposable-container T0.
- **C:** The hand-authored state/action oracle and channel semantics may omit relevant states, actions, or hidden channels. Both implementations are finite and share the frozen input. A receipt's truthfulness is stipulated, not demonstrated.
- **U:** No universal feedback bound, GUI behavior, model-call lower bound, latency/bit cost, live task safety, or production result is established.

## Protocol and deviation

Issue #5927 proposes the minimum experiment in a disposable container. `docker --context desktop-linux info` was attempted read-only twice and did not respond within 30 seconds; no container inventory or owner state could be established. Computer Use exposed no open Windows app window for Docker Desktop. Another task's OrbStack interval is not used. To keep the hypothesis moving without claiming the requested container experiment, this allocation is explicitly a host-only construction deviation; formal container T0 remains outstanding.

No model/game/GUI/input/provider/network action, shared GPU use, Docker/OrbStack call that creates or changes containers, or user task effect occurred. The raw CPU enumeration is single-process and uses Python's standard library only.

## Frozen task-relative model

`cases.json` declares two worlds with identical no-feedback transcript (pixel view and dispatch receipt). In the positive control, `claim_complete` is safe only in `persisted`; `continue_recovery` is safe only in `blocked`; therefore their common-safe-action intersection is empty. A fresh `persistence_receipt` distinguishes them, yielding an authored minimum of one exchange. In the null control, `inspect_again` is safe in both, so zero exchanges suffice despite the hidden-state difference.

The unit is one fresh channel observation, not bits, bytes, latency, cost, or model calls. Stale channels are excluded. The separate auditor re-enumerates transcript partitions and checks safe-action labels against the frozen independent oracle fields.

## Execution boundary

The candidate and auditor each run once after the test suite; no retry, seed search, parameter tuning, threshold change, or result overwrite. Construction artifacts and outcomes are additive and do not amend any prior Issue #5927 evidence.

## Construction outcome (2026-10-01)

Allocation 01's candidate returned one exchange for the positive case and zero for the null case. Its auditor stopped with `FAIL_RAW_AUDIT` because equivalent partition rows had different serialization order. That failure is preserved verbatim. Successor allocation 02 pinned the same candidate/input bytes, added a row-order invariance control, passed eight construction tests, and the independent v2 auditor returned `PASS_RAW_AUDIT` with no errors. Both allocations are host-only construction evidence; neither is the container T0 requested by Issue #5927.

Allocation 02 raw results are in `successor_02/candidate.raw.json` and `successor_02/audit.raw.json`. Exact per-allocation commands and hashes are in each `RUN.json`.

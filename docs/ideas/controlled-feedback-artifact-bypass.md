# Controlled feedback and raw-artifact bypass

This finite-method family asks whether a development-feedback restriction still changes a candidate's behavior when the candidate author can read raw evaluation artifacts through a separate tool path. It is an evaluation-boundary proposal, not a claim that historical repository results were contaminated, a reason to restrict public research records, or authorization to access private/real answer keys. All three allocations use synthetic data only.

## A01 — auditor failure

- **Evidence:** open Draft [PR #8760](https://github.com/Unjuno/agent-interface/pull/8760).
- **Result:** Candidate ran once and emitted four cells / 88 events. The independent auditor ran once but failed in its mutation loop before writing an audit. Disposition: `HOLD_AUDITOR_FAILURE`; no scientific contrast is assigned. Preserve the first output and traceback; no retry.

## A02 — candidate/oracle stream mismatch and audit exit failure

- **Evidence:** open Draft [PR #8762](https://github.com/Unjuno/agent-interface/pull/8762); dependent index-only Draft [PR #8767](https://github.com/Unjuno/agent-interface/pull/8767).
- **Result:** Fresh-seed candidate ran once and emitted four cells / 92 events. The auditor wrote eight candidate/reconstruction mismatches and rejected 5/5 mutations, then exited 1 because its final summary referenced a removed variable. Candidate labels used `Random.randrange(2)` while the oracle used `Random.getrandbits(1)`, yielding different random-bit consumption. Disposition: `HOLD_ACCESS_OR_AUDIT`; no scientific contrast is assigned. PR #8767 only supplies the generated analysis-index entry and does not repair the mismatch or change the result.

## A03 — audited synthetic contrast

- **Evidence:** open Draft [PR #8765](https://github.com/Unjuno/agent-interface/pull/8765).
- **Result:** A fresh-seed candidate and independent raw-only auditor each ran once and exited 0. The auditor reconstructed four cells / 92 events with zero errors and rejected all five frozen mutations. The frozen classifier returns `BYPASS_DEFEATS_FEEDBACK_SCOPED` because controlled/raw-bypass optimism equals the full/sealed baseline at the equality-inclusive threshold. Every cell has candidate score 5, development accuracy 17/24, fresh accuracy 119/256, and optimism 0.2435. Thus the fixture does not show an incremental effect caused by bypass availability, and controlled feedback itself showed no advantage over full feedback in this fixture.

## Scope and current integration state

Keep A01's auditor failure, A02's access/audit hold, and A03's negative incremental-effect finding separate; they were not pooled or rerun. All four evidence/index PRs remain open and unmerged at this review. The results do not establish actual researcher behavior, real artifact leakage, contamination of prior results, private-data access, differential privacy, model/GUI behavior, or product impact. The neighboring #8072/#8319 controlled-feedback work and #6173 run-scoped answer-surface access have distinct estimands and are not substitutes for this study.

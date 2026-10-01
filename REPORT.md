# Issue #6129 T0 — pending-outcome route learning

## H / T / D / C / U

- **H:** A pending-aware evidence card can avoid unsupported route rankings caused by fast receipts/complete-case selection, preserve an equal-evidence null, select only when exact conservative bounds separate, and abstain when attribution or censoring assumptions fail.
- **T:** One frozen, authored finite fixture with five cases at update time 5. Candidate input was restricted to `visible.json`; `truth.json` was only mounted into the separate auditor.
- **D:** `PASS_METHOD_SCOPED`: the candidate matched all five predeclared classifications; all identified bounds reconstructed exactly; all-pending routes retained `[0,1]`; nonidentified cases exposed no route bounds; both classification and bound mutation controls were rejected.
- **C:** OrbStack Docker Engine 29.4.0, pinned `python:3.12-slim` digest, linux/arm64, network disabled, read-only root and source mounts, 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges. Candidate and independent auditor each invoked once; zero retries. Local package tests: 5/5.
- **U:** Synthetic finite-method evidence only. No empirical route efficacy, production routing, task safety, causal effect, model/GUI/human behavior, or bandit-regret claim. Repository-wide CI was not run because the attached directory is a source snapshot without `.git`, and full repository acquisition exceeded the bounded transfer window. Obstac was not exposed as a tool/CLI in this session; OrbStack Docker was used instead.

## Result

| Frozen case | Candidate result | Interpretation |
|---|---|---|
| Receipt/effect inversion with possible outcome-dependent censoring | `NONIDENTIFIABLE` | Fast receipt and complete cases do not identify route value. |
| Equal-delay null | `NO_PREFERENCE` | Both routes have exact observed bounds `[1/2, 1/2]`. |
| Known-window noninformative censoring | `SELECT:ROUTE_F` | Exact conservative bounds separate: E `[1/4, 1/2]`, F `[3/4, 1]`. |
| Ambiguous attribution / informative censoring | `NONIDENTIFIABLE` | No actionable route bounds emitted. |
| All-pending initial period | `NO_RANKING` | Both route bounds remain `[0,1]`; pending is neither success nor failure. |

The receipt-inversion case's correct disposition is `NONIDENTIFIABLE`, not a forced no-ranking estimate: the fixture deliberately leaves outcome-dependent censoring unresolved. The authored truth rates are audit-only and were never visible to the candidate.

## Reproduction and retained evidence

`FREEZE.json` identifies all frozen source/input hashes. `results/RUN.json` records runtime conditions, invocation counts, scope and stop reason. `results/candidate.json`, `results/audit.json`, stdout/stderr, local test output and `results/SHA256SUMS` retain raw evidence. The audit reports `PASS_METHOD_SCOPED`, 5/5 reconstructed cases, and an empty error list.

## Stop / next rung

T0 is complete. Stop before T1: a separately frozen estimand, authorized empirical workload, complete attempt/censoring ledger, independently attributable effect oracle, stable task mix and explicit authority are prerequisites. Until those exist, no online route updates or live collection are justified.

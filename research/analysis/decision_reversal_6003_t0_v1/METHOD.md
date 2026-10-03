# Issue #6003 T0-host-01 — decision-reversal selector construction

## H / T / D / C / U

- **H:** Given the frozen four-state illustrative decision table, cheapest-first and nominal entropy select a test with no downstream action changes, while the prior-range robust selector chooses a feasible test with positive worst-case action-reversal mass. When all tests are null, it reports `UNRANKABLE`.
- **T:** Freeze three explanations plus an escape state, four illustrative prior scenarios, three candidate tests, budget 4, and mandatory sentinel cost 1. Compare cheapest-first, nominal entropy, and minimum scenario action-reversal mass. Include a prior-sensitive B/C entropy-order reversal and an infrastructure `STOP` outcome. One candidate run, followed by one separate auditor run.
- **D:** Host construction passes only if the candidate selects A by cost and entropy, B by robust reversal; confirms nominal C>B entropy but capture-lean B>C; reports null `UNRANKABLE`; preserves feasibility and the sentinel; and treats `STOP` as neither a scientific result nor a decision-changing outcome. The independent auditor recomputes all checks from the frozen table without importing selector code.
- **C:** CPU-only, Python standard library. Docker inventory was unresponsive, so this allocation does not claim the Issue's requested disposable-container T0. No model, GPU, network, WSL, package install, or shared container is touched.
- **U:** All states, priors, outcome tables and next-action consequences are authored fixtures. Scores are not calibrated probabilities or expected real-world utility; this tests only a finite selector implementation, not improved research productivity or any route's merits.

Frozen current-main base: `5759a6e65b8b5e7487fb2ad61f53bb531aeaf512`. The earlier preregistration comment naming `72647971d2b96568fa2db3fc47e01d07dd72000a` was superseded before any candidate/audit run after main advanced; see the appended issue-comment amendment.

## Frozen expectations and decisions

The machine-readable input is `FREEZE.json`; its digest is captured in the candidate output. A and B/C all fit the fixed budget after the sentinel. A has four equiprobable nominal outcomes but none changes the next action. B has a 0.60 reversal mass in each illustrative scenario and a 0.10 infrastructure STOP. C is prior-sensitive: nominal entropy exceeds B, while capture-lean entropy is below B. The minimax score excludes STOP mass. The null control changes all non-STOP consequences to the baseline action and must produce `UNRANKABLE`.

## One-shot procedure

From this directory, run exactly once:

```powershell
python .\select.py
python .\audit.py
```

`select.py` writes `candidate_result.json`; `audit.py` independently writes `independent_audit.json`. The second command is an audit, not a rerun of the candidate. Preserve all outputs; do not tune or retry if either fails. These host commands do not fulfill the separate container environment condition.

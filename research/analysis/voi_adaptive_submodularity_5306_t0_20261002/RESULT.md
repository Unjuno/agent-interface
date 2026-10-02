# Result — adaptive-submodularity boundary for VOI stopping (T0)

**Disposition: `COUNTEREXAMPLE_GREEDY_VOI_SCOPED`.** The exact-rational fixture contains complementary evidence for which a greedy one-step net-VOI rule stops at the root, although an exact feasible sequential policy has strictly higher net value. This is a counterexample to assuming universal adaptive diminishing returns for this declared objective, not evidence that a production verifier currently uses the rejected policy.

## Exact result

In the primary case, `P(GOOD)=7/10`; both independent checks have `P(-|GOOD)=2/5`, `P(-|BAD)=2/3`; each costs `1/100` and the total budget is `1/50`.

- B's expected decision-accuracy marginal before evidence is **0**.
- After observing A=`-`, B's conditional marginal is **2/45**. This is an increasing marginal (`0 < 2/45`), violating the tested adaptive-submodularity condition.
- Myopic net-VOI stops immediately: expected accuracy/net value **7/10**, cost **0**.
- Exact finite Bellman enumeration selects A, then selects B only after A=`-`: expected accuracy **541/750**, expected cost **37/2500**, net value **5299/7500**. Its net gain over stopping is **49/7500**.
- The fixed A-then-B checklist reaches the same expected accuracy but pays the full `1/50`, for net `263/375`; adaptive continuation is better in this model.

The perfect-duplicate control has marginal **1/2** before the observation and **0** after A=`GOOD`. Stale-source and deadline-infeasible controls both yield with zero optional calls. The independent auditor reports zero errors and verifies the exact policy continuation, values, duplicate control, gate controls, and the candidate's STOP claim. Contract/mutation tests pass **5/5**.

## H / T / D / C / U

- **H:** Complementary checks may have zero immediate decision value yet positive value after a particular result; universal greedy/ adaptive-submodular assumptions are unsafe without a family-specific check.
- **T:** Exact-rational finite model, myopic net-VOI vs fixed checklist vs exhaustive Bellman continuation, perfect-duplicate control, stale-generation and deadline controls; source and stop rules frozen before the one candidate/auditor run.
- **D:** `COUNTEREXAMPLE_GREEDY_VOI_SCOPED`; candidate, auditor and all five contract tests exit 0; no retries.
- **C:** Fixed mandatory checks or richer multi-step VOI may be preferable; real likelihoods may be unavailable, correlated or nonstationary.
- **U:** Constructed model only. No calibrated verifier, adapter, real interface, GUI, user data, task effect, latency, safety or general optimality is measured.

## Execution and artifacts

Host CPython 3.12.10, standard library only. Docker Desktop was not usable: the service could not be opened by this user process, and a shared OrbStack workload had been reported active without an exclusive slot. No container or other task's workload was touched. Exact commands, exit codes, retry count and resource STOP are in [RUN.json](RUN.json); source identities and byte hashes are in [FREEZE.json](FREEZE.json) and [SHA256SUMS.txt](SHA256SUMS.txt). Raw candidate output and independent audit are retained under `results/`.

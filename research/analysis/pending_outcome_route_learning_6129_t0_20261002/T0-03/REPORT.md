# Issue #6129 T0-03 — delayed ranking inversion under typed outcomes

## H / T / D / C / U

- **H:** At a frozen checkpoint, complete-case selection can select the fast-feedback route even while pending-aware bounds correctly abstain; the same frozen all-attempt endpoint later ranks the other route higher. Typed terminals, recovery, censoring, cross-task coupling, and switch work must remain separately accounted.
- **T:** Seven finite authored cases; 32 assigned attempts; checkpoint 1, deadline 3. Candidate received only visible checkpoint data; auditor separately received the frozen terminal table. Candidate and auditor each ran once; retries 0.
- **D:** `PASS_METHOD_SCOPED`. Independent audit reconstructed 7/7 cases, checkpoint A=0 vs B=1/2 complete-case rates, deadline A=3/4 vs B=1/2 all-assigned success rates, exact conservative bounds, typed event counts, route-switch totals, and no-lookahead boundary. Errors=[]; local tests 9/9.
- **C:** OrbStack Docker Engine 29.4.0; pinned `python:3.12-slim` image, linux/arm64, network none, read-only root/input/source, 0.5 CPU, 256 MiB, 32 PIDs, all caps dropped, no-new-privileges.
- **U:** Exact finite method evidence only. Known-independent administrative loss is stipulated by the fixture, not inferred from samples. The cross-task case only rejects the independent-arm comparison when attribution is state-coupled. No empirical route efficacy, causal/product/safety claim, live routing, or imported regret guarantee.

## Findings

At checkpoint 1, complete cases are A=0/1=0 and B=2/4=1/2, so a completed-only selector picks B. The pending-aware all-assigned bounds are A=[0,3/4] and B=[1/2,1/2]; they overlap, so the candidate returns `NO_RANKING`. At deadline 3, the independent audit sees all eight terminal outcomes and reconstructs A=3/4 vs B=1/2. This is the planted inversion, not evidence about real routes.

Equal-delay routes return `NO_PREFERENCE`; the stipulated independent-loss case yields separated conservative bounds and `SELECT:F`; safe stop and wrong effect stay distinct; YIELD remains pending at checkpoint and its later outcome is auditor-only; unknown/outcome-dependent loss returns `NONIDENTIFIABLE`; cross-task state coupling returns `MODEL_MISMATCH_UNKNOWN`. Switching cost is 2+3+1+4=10 units/change: fixed path total 12 vs A-B-A total 32.

## T0 disposition and limits

Together with the separately retained T0-01/T0-02 records, this allocation covers the Issue's finite method controls. `PASS_METHOD_SCOPED` does not qualify T1, empirical identification, a real-world treatment effect, guard/safety performance, or any production route. T1 still requires the Issue's separately authorized workload, source-bound attempt/effect ledger, censoring reasons, stable task mix, and independent oracle. No live route or user data was used.

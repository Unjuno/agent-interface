# Issue #5771 — finite disturbance/response feasibility T1

## H / T / D / C / U

- **H:** Within this authored finite task/fault family, an extra verifier over unchanged observations cannot resolve an observation alias or supply a missing response. Added discriminating observation removes the alias; an added authorized recovery response covers worker exit; the combined intervention covers both. An authority-forbidden backend restart and an over-deadline response remain gaps.
- **T:** One deterministic finite-state construction with five disturbances and seven arms: baseline, extra verifier (same observations/actions), observation refinement, added recovery, forbidden response, deadline gap, and combined observation+recovery. Candidate emits every disturbance in every arm; independent auditor rebuilds row decisions from the frozen fixture.
- **D:** Require the exact five disturbance IDs retained in each arm, expected classification for each arm, alias pair preserved in baseline and verifier-only arms, no unauthorized edge classified covered, deadline miss preserved, exact candidate/auditor outputs, and corruption test rejecting a dropped row. Candidate and auditor each run once in separate network-disabled pinned-image containers. Preserve operational failures; never retry or relabel.
- **C:** All states, observations, policies, authority labels, and latencies are authored; response coverage is exact only inside this toy envelope. No stochasticity, real GUI, model, human handoff, or measured intervention cost is represented.
- **U:** No production safety guarantee, real disturbance coverage, theorem from Ashby, reliability estimate, or claim that a specific runtime capability is missing. Taxonomy/oracle omissions, correlated faults, partial observability, and time variation remain untested.

## Disturbance and intervention design

`focus-loss` and `target-mutation` emit the same observation but require incompatible responses. `worker-exit` has no baseline recovery response. `forbidden-reset` requires an authority-prohibited response. A modal takeover is a separate covered case. Interventions distinguish verifier-only, added observation, added response, forbidden capability, deadline failure, and combined observation+response. The response mapping is explicitly a constructed oracle, not an empirical controller policy.

## Execution

The formal T1 receipt uses GitHub-hosted Docker as an isolated fallback because local Docker Desktop is unavailable; no local daemon is started. The official image, platform, source and workflow hashes will be frozen before branch creation. Candidate and independent auditor are separate invocations with no network, read-only root, dropped capabilities, no-new-privileges, and bounded CPU/memory/PIDs. One run only.

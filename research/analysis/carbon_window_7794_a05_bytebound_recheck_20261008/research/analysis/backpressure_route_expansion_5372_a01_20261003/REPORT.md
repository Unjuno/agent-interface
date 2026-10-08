# Issue #5372 route-set expansion A01 — result

**Disposition: PASS_METHOD_SCOPED.** The preregistered finite queue fixture produced the predicted local-cost/verified-completion inversion, and the independent auditor reconstructed the complete records with no errors.

| Arm | Local ticks | Verification jobs | Verified by inclusive tick 7 | Pending at horizon | Safety events served |
|---|---:|---:|---:|---:|---:|
| BASE_ONLY | 12 | 6 | 5/6 | 1 | 3/3 |
| EXPANDED_GREEDY | 6 | 12 | 3/6 | 6 | 3/3 |
| EXPANDED_PRESSURE | 11 | 7 | 5/6 | 1 | 3/3 |

The locally faster optional route halves local work (12→6 ticks) but doubles verification jobs (6→12) and lowers horizon-verified tasks (5→3). The fixed reservation-pressure arm returns to 5/6 at 11 local ticks. This is an authored deterministic counterexample, not a measured runtime or product effect.

## H / T / D / C / U

- **H:** Under identical fixed arrivals and safety service, a locally faster optional route that creates more downstream verification work can lower verified completions at a fixed horizon under local-cost-only selection; a narrow reservation gate may recover the base result without delaying mandatory safety.
- **T:** Six tasks arrive at tick 0. Arms are BASE_ONLY (2 local ticks and one verifier job/task), EXPANDED_GREEDY (1 local tick and two verifier jobs/task), and EXPANDED_PRESSURE (same choices with optional-route reservation budget 2 and task-ID ordering). A single FIFO verifier serves one job/tick; horizon is inclusive tick 7. Three safety events at ticks 0/2/4 use a dedicated one-tick lane with deadline 1. Candidate and raw-only independent auditor each ran once in separate native WSLc containers, pinned cached image, no pull/network, one CPU, requested 256 MiB, UID/GID 65532:65532. Retry count 0.
- **D:** PASS_METHOD_SCOPED required exact independent reconstruction, the predicted inversion, pressure recovery to at least baseline completions, no safety misses, and rejection of all five frozen corruptions. All passed; auditor errors were empty.
- **C:** The reservation policy is deliberately narrow and may rely on the fully visible burst and hand-set budget. Different arrivals, spare capacity, central coordination, or no extra verifier work can remove the inversion.
- **U:** This establishes only the behavior of the exact finite authored queue fixture. It is not evidence about prevalence, stability, optimal admission/backpressure, GUI correctness, real agent benefit, end-to-end latency, or an implemented safety lane.

## Execution and retained evidence

- Engine: Microsoft WSLc 3.0.1.0, Linux/amd64.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`.
- Flags: `--pull never --network none --cpus 1 --memory 256m --user 65532:65532`; read-only bind mount. No GPU, model, GUI, install, network, or runtime changes.
- Both container stderr streams recorded: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The memory request was made, but effective memory/swap enforcement is unverified.
- Construction suite: 3/3 passed before freeze; these were not formal candidate/auditor invocations.
- Candidate raw SHA-256: `6142DB37F19AB56E65A8DFE87F802EB13B73950CEDD3C205ACEDC536EFA311DF`.
- Auditor JSON SHA-256: `D3A4435A7B891CA775FBF81A069A2554C1E970081EF6ECFE4F67884A60ED999D`.
- Candidate and auditor stderr SHA-256: `2562006E62622BCF41C809D627CDC2C6250516B8CF1C9CCD28072C331FCC4096`.
- Auditor rejected: `drop_offer`, `route_label`, `suppress_verifier_work`, `safety_miss`, `forge_completion`.

See [PREREGISTRATION.md](PREREGISTRATION.md), [FREEZE.json](FREEZE.json), [RUN_RECORD.md](RUN_RECORD.md), source, fixture, and raw output files alongside this report. This result does not close broader #5372: live scheduler/runtime applicability remains untested.

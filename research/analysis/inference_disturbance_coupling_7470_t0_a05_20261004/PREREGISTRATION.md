# Preregistration — INFERENCE-DISTURBANCE-COUPLING-7470-T0-20261004-A05

- **H:** Four intact circular phase shifts over two repeated periods yield correct centered Pearson correlations `[1.0,-0.2,-0.6,-0.2]`, invariant null outcomes, and phase-sensitive planted outcomes, including explicit seam transitions.
- **T:** Repeat each intact latency and disturbance period twice. Enumerate all four latency rotations. Compute Pearson r as `sum((L-mean(L))*(S-mean(S))) / sqrt(sum((L-mean(L))^2)*sum((S-mean(S))^2))`; independently recompute it from source periods and audit all event rows.
- **D:** `PASS_METHOD_SCOPED` only if the exact expected correlation fixture, fixed marginals/horizon, one seam event per arm/trajectory, invariant null, phase-varying planted outcome, raw reconstruction and 3/3 mutation rejection all pass.
- **C/U:** Tiny constructed periodic input and planted interaction only; no live coupling, causal runtime, prevalence, safety, GUI/game, human or deployment claim.

Candidate/auditor each at most once, no retries, auditor only after candidate exit 0. Fresh output absent; source hashes frozen in PRELAUNCH_FREEZE.json.

# Fixed nonzero startup-overhead T3 — Issue #7327

## H / T / D / C / U

- **H:** In the frozen exact-rational observation model, doubling all declared times preserves normalized observations and first unsafe-observation timing. If a nonzero startup delay is incorrectly left fixed while the rest is doubled, the normalized observation stream changes and a reachable hazard can be observed at a different normalized time/state.
- **T:** Add three fixtures: zero-startup negative control, nonzero-startup reachable hazard, and nonzero-startup quiet control. Compare baseline, fully homogeneous factor-2 scaling, and factor-2 scaling with startup delay held absolute. One candidate and one independent formula-based raw auditor, each at most once; four raw mutation controls. Do not rerun T0/T1/T2 or alter their evidence.
- **D:** `PASS_FIXED_OVERHEAD_DISTINGUISHED` only if homogeneous traces are identical for all fixtures, zero startup remains unchanged under the fixed-delay transform, and the nonzero reachable-hazard fixed-delay trace diverges at its first unsafe observation; all four raw mutations must be rejected. Otherwise preserve FAIL/STOP without retry.
- **C:** Pure synthetic exact-rational schedule; only observation/event ordering is modeled. It has no physical-time, host-latency, GUI, game, safety, or controller claim.
- **U:** Whether this finite model correctly distinguishes a nonzero absolute startup delay from homogeneous time scaling at a reachable observation boundary.

## Runtime and ownership

Allocation: `LOGICAL-TIME-SYMMETRY-7327-FIXED-OVERHEAD-T3-20261004-01`.
Frozen base is recorded in `FREEZE.json`; T0–T2 remain immutable. The sole matching GitHub branch search returned only the prior merged T0/T1/T2 branch; no T3 branch or path existed at freeze. Existing PR #7349 is merged.

OrbStack answered `docker info` but `docker ps` failed while opening a containerd content blob (`operation not supported`). No image listing, pull, launch, or retry was attempted. Per #7327's CPU-only method protocol, this optional container rung falls back to host Python standard library; no container resource-limit or speed claim is made.

After prospective registration, run exactly once each:

```sh
python3 candidate.py spec.json output/raw.json
python3 audit.py spec.json output/raw.json output/audit.json
```

No GUI, model, game, GPU, physical input, or network access is used by the experiment.

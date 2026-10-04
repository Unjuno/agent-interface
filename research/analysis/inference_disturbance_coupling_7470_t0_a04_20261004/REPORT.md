# Issue #7470 A04 — correlation-gate defect (not an Issue-level PASS)

## Formal result

The frozen candidate ran once (exit 0), enumerating all four unique circular latency shifts and both plants over two complete periods: eight trajectories, each with eight event steps. The auditor ran once after candidate success (exit 0), reconstructed all rows, and rejected all three preregistered mutations. Candidate JSON SHA-256: `5bf0b6319ba130dd25e8d83d76e16686aab7be2c7582363c7e1127d5216713ac`.

Each trajectory contains the explicit period seam at event index 4 (period 1, index 0); the seam receives the same transition update as other events. Both input periods remain intact under all shifts. Every trajectory has total latency/release tick 20. The null trace is phase invariant (`null_states=1`).

| Shift | Latency period | Pearson r | Planted peak | Outside-envelope steps | Stale severity exposure | Seam state after event 4 |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 1,2,3,4 | 0.25 | 15.0 | 5 | 40 | 7.0 |
| 1 | 2,3,4,1 | -0.05 | 12.0 | 4 | 28 | 5.5 |
| 2 | 3,4,1,2 | -0.15 | 11.0 | 2 | 24 | 5.0 |
| 3 | 4,1,2,3 | -0.05 | 12.0 | 3 | 28 | 5.5 |

**Correlation gate defect:** the frozen source labels its centered cross-product as Pearson r but divides by period length before normalizing by the unaveraged sums of squares. The resulting values are one quarter of the standard Pearson correlations. Correct post-hoc Pearson values from the raw periods are `[1.0, -0.2, -0.6, -0.2]`. Since reporting the preregistered statistic is part of the gate, A04 is not declared a PASS; the trajectories remain valid as a seam-inclusive harness diagnostic. Do not rerun A04. A separate successor is needed to correct and independently test the correlation calculation.

## Interpretation and limits

The artifact demonstrates phase-sensitive outcomes in the planted toy law with an explicit seam. Because the preregistered Pearson statistic was miscomputed, the complete A04 method gate failed. No real-world, causal, prevalence, safety, GUI/game, human benefit, or deployment claim follows. A02's arbitrary-assignment diagnostic and A03's one-period seam omission remain separately preserved.

## Environment

Host CPython standard library on macOS arm64. No container was required by this bounded CPU-only Issue T0; no model, GUI, network, GPU, user data, or external actuation was used. No isolation claim.

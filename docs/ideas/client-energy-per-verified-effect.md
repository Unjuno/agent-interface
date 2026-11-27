# Client energy per verified effect — #7728

- **Status:** Matched-route energy hypothesis untested; sensor qualification is platform-specific.
- **Source:** [Issue #7728](https://github.com/Unjuno/agent-interface/issues/7728). The macOS eligibility packet is retained in main under `research/analysis/client_energy_per_effect_7728_t0_20261005/`; Windows counter cross-checks remain in open Draft [PR #7758](https://github.com/Unjuno/agent-interface/pull/7758).
- **Idea:** Compare direct and guarded routes on the same fixed desktop tasks using a supported cumulative energy counter and an independent oracle for safe application effects. Count failed attempts, retries, recovery, and guard overhead; keep success, safety, latency, and tokens separate from energy.
- **Outcome:** The unprivileged macOS preflight is `HOLD_ENERGY_SENSOR_UNAVAILABLE`: `powermetrics` required superuser access and exposed no qualifying cumulative counter. No escalation or route/task comparison ran. Windows A01/A02 cross-checks in Draft PR #7758 qualify only counter identity/sampling on that Windows host; A01 retains a runner-source custody HOLD and A02 a stale-base HOLD. Neither measured application effects or energy per verified effect. No T0/T1 route-comparison result exists.

## Measurement boundary

Do not convert estimated power, CPU time, TDP, WSL characteristics, or host load into measured joules. CPU-package energy is not whole-device, GPU, network, or remote-provider energy. Resume only with an eligible, documented sensor and a separately frozen matched-task protocol; sensor unavailability is a valid stop, not a reason to substitute a proxy.

See the main-tree [macOS eligibility report](../../research/analysis/client_energy_per_effect_7728_t0_20261005/REPORT.md) and the unmerged [Windows sensor cross-check PR](https://github.com/Unjuno/agent-interface/pull/7758).

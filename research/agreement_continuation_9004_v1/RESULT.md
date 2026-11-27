# Issue #9004 T0 result

**Disposition:** `NO_INCREMENTAL_AGREEMENT_VALUE` on this finite synthetic trace family. The frozen method gate is `PASS_METHOD_SCOPED`; `formal_pass=false`.

The allocation `9004-agreement-continuation-t0-a01-20261017` ran once from frozen commit `a04941c5213b060c095ff1994b4dd2ce61481ccc`, based on current main `1ece47014d05db898bf73afcd722a14524462e15`. The candidate generated all 40 rows (10 fixed cases × 4 arms). The separate raw-only auditor reconstructed all rows with zero errors. Five tests passed in normal and optimized Python, including wrong common-mode action, missing release obligation, omitted case-arm, and duplicate-row mutations.

| Arm | Actions | Cases with actions | Median synthetic inter-action gap |
|---|---:|---:|---:|
| Always-wait | 4 | 2 | 1 tick (2 paired cases) |
| System-1-only | 4 | 2 | 1 tick (2 paired cases) |
| Agreement-only | 2 | 2 | not applicable (one action per case) |
| Agreement lease | 4 | 2 | 1 tick (2 paired cases) |

Agreement lease matched System-1-only in the cases where they acted. It did not lower the synthetic inter-action gap relative to always-wait, so the prospective 20% gate was not met. The two successful paired cases cannot support latency inference because their ticks are synthetic. The common-mode wrong-agreement and irreversible/unknown-effect cases were blocked by the independent truth/effect gate; target substitution, staleness, contradiction, emergency, authority loss and release failure also did not authorize continuation.

Retained evidence: [`RAW.json`](RAW.json), [`AUDIT.json`](AUDIT.json), [`RUN_SUMMARY.json`](RUN_SUMMARY.json), [`RUN_RECORD.md`](RUN_RECORD.md), preregistration and frozen source in this directory. This establishes only finite method behavior for these authored traces. It does not establish model agreement rates, real latency, physical release behavior, GUI/game safety, task success, or product readiness. No live application, model, GPU, network, GUI, or input actuation was used. This allocation is consumed and must not be retried.

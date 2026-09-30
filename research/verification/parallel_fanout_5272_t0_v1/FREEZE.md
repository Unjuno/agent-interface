# T0 pre-registration freeze — Issue #5272

Status at freeze: construction complete; formal invocation not yet started.

- Repository: `Unjuno/agent-interface`
- Frozen main commit: `c4735cfd27bfca057d9c1fca9a7ea19866f77259`
- Frozen main tree: `02354a33ac4938dbc5149130c52cd66e46485663`
- Additive path: `research/verification/parallel_fanout_5272_t0_v1/`
- Allocation: `parallel-fanout-5272-t0-20260930-01`
- Environment: host Python 3.12.10; standard library only; synthetic integer-time event simulator; no network, models, GUI, external verifiers, or input.
- Container decision: Docker/OrbStack was not started because the shared execution-lane record requires a fresh exact allocation; this T0 has no container-specific dependency. No container result is claimed.
- Formal execution limit: one simulator invocation, collision-free raw path, followed only after exit 0 by one separate raw-only audit invocation. No retry or replacement of this allocation.
- Frozen commands (PowerShell, from this directory):
  1. `python -m unittest -v test_model.py` — construction only.
  2. `$env:RAW_OUT = "<fresh evidence path>/raw.json"; python simulator.py` — formal runner, exactly once.
  3. `$env:RAW_PATH = "<the same exact raw path>"; python audit.py` — separate auditor, only after runner exit 0.

## Hypothesis / test / decision / risks / unknowns

- **H:** Parallel fan-out lowers decision-ready latency for independent selected
  checks without changing typed outcomes, dropping mandatory evidence, or
  violating deadline/budget constraints.
- **T:** Run the nine workloads in `workloads.json` under both serial and
  three-worker fan-out policies. The suite covers independence, a dependency
  chain, timeout, UNKNOWN, optional deadline, mandatory deadline, budget
  saturation, decisive FAIL cancellation, and contention. Outcomes and
  verifier identities/versions are frozen in the input. The primary endpoint
  is logical decision-ready time for the independent workload. The fan-out
  gate is `parallel_ms * 4 <= serial_ms * 3` (at least 25% lower). Check
  statuses, trace, service intervals, cost budgets, worker cap, result digests,
  cancellation and typed decisions for all rows.
- **D:** PASS only when the primary endpoint passes; every policy/case matches
  its frozen typed oracle; every PASS has all mandatory checks completed PASS;
  no budget or worker cap is exceeded; dependency, deadline, timeout,
  cancellation, digest, and independent audit invariants all pass. Missing
  mandatory evidence remains UNCERTAIN. Otherwise retain FAIL/HOLD/STOP as
  appropriate. A PASS is only a synthetic finite-model result.
- **C:** Logical time is not host wall time. Fixed costs do not estimate real
  verifier distributions. This excludes CPU/GPU/RAM contention, runtime
  scheduling, rate limits, remote cancellation/cleanup, correlated verifier
  failures, and end-to-end task outcomes. Fan-out may waste work before a
  decisive failure or amplify shared-resource contention.
- **U:** Real cost distributions and shared dependencies; actual cancellation
  and cleanup latency; heterogeneous CPU/GPU contention; deadline utility of
  optional evidence; and whether adaptive fan-out improves real decision
  latency without weakening evidence remain unresolved.

## Exact frozen input and code identities

SHA-256 is over file bytes as frozen in the working tree. Git blob SHA is the
SHA-1 identity of the exact Git blob content.

| File | SHA-256 | Git blob SHA |
|---|---|---|
| `README.md` | `39ca03066b3f84c1a4802cc8e42f6b2e807d2c171bf703de71ae715b7c045daa` | `f61fd786078c4820f33b6d784882ef7c68cf0c40` |
| `simulator.py` | `777959cd6ad02ee4b99485a6c4319484d3d84436adc42460075809dbdea8cc17` | `6e33645842ce464017eb3729322aa9d28a13b9e5` |
| `audit.py` | `80b8a191e955780ecad701633a0a8293a8ad8d087e86f017e0576b5908b061dc` | `68e1218f4257ad30d028361fa56444b75e5209da` |
| `test_model.py` | `af5224a62fd8cf177a201c17c9efef0b46000f564260e9b985e05a81702c105f` | `12046a71a1295618ea386bba8742638999e20120` |
| `workloads.json` | `18b3c9353660dbecd9a5544cd6c8769bb27e2cea3cf4579d64ff6d6d110d7f5d` | `ee39e3f6f479e79a5f33fa523c950e76a3baf65f` |

`FREEZE.md` is the human-readable pre-registration and is excluded from the
input/code hash table to avoid self-reference. The GitHub commit containing
this freeze is recorded in the result report; its parent must equal the frozen
main commit above. Any main advancement before the formal runner starts
invalidates this freeze and requires stopping before execution, not silently
rebasing a consumed run.

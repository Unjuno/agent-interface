# Issue #5694 T0 — exogenous opportunity ledger

Allocation: `EXOGENOUS-OPPORTUNITY-5694-T0-20261001-01`

Prerecorded in Issue #5694 comments #5923917257 and #5924041213. The source question is whether closed-loop sampling hides missed externally scheduled opportunities when only completed-cycle latency percentiles are reported. This is distinct from #5715: no admission-to-hazard margin, forbidden-effect count, safety probability, or policy authority is evaluated.

## H / T / D / C / U

- **H:** On a fixed exogenous opportunity set, a sparse arm with a long declared busy period can show a lower completed-cycle p95 than a denser arm while yielding fewer useful effects before expiry. The opportunity ledger exposes this ranking inversion; the no-stall control does not show a coverage inversion.
- **T:** Deterministic standard-library-only event simulation with integer milliseconds, no sleep, no model, no live clock, no GUI, no input, no network. Eight ordered scenarios are frozen in `runner.build_raw()`:
  1. `inversion`: O1/O2/O3 windows [0,80], [100,180], [200,280], horizon 320. Dense cycles end at 30/130/230 and useful effects occur at 35/135/235. Sparse cycles end at 5/215; effects at 10 (O1) and 220 (O3); busy interval [5,210) fully contains O2's window.
  2. `no_stall`: fast and dense arms both produce timely effects for all three same opportunities; completed p95s are 5 and 30 ms.
  3. `safe_stop`: a declared stop occurs inside one opportunity; it remains counted as `SAFE_STOP`, not as a useful effect.
  4. `expiry`: an opportunity expires with no cycle/effect and a complete observation horizon, so `MISS`.
  5. `censored`: the horizon ends before expiry, so `UNKNOWN`.
  6. `overlap`: A and B windows overlap; a region event may meet both, while a B-only region event cannot meet A. Matching uses raw region/time fields, never controller-labelled opportunity IDs.
  7. `unsynced`: local cycle latency remains computable, but opportunity outcomes and uncovered-gap summary are `UNKNOWN`/null when event clocks are not aligned.
  8. `no_exogenous`: no scheduled opportunities yields `NOT_APPLICABLE` and a zero denominator, never invented opportunities.

  `audit.py` independently derives nearest-rank completed-cycle p95, region/time matches, `MET`/`SAFE_STOP`/`LATE`/`MISS`/`UNKNOWN`, first in-window useful-effect latency, per-opportunity-window uncovered gap, and busy-expired IDs. It does not import `runner`. The canonical JSON fixture identity is frozen as SHA-256 `9a1f4068afbc95244dbd5e9331a136e3e441df23d3f19b4c9bd23374e90a9cee`.
- **D:** `PASS_METHOD_SCOPED` only if the raw fixture identity and all eight ordered cases pass the independent auditor; the inversion case reconstructs dense p95=30 ms and 3/3 useful versus sparse p95=5 ms and 2/3, with O2=`MISS` during the declared busy interval; first-effect latencies are {35,35,35} vs {10,null,20} ms; longest uncovered opportunity-window gaps are 35 vs 80 ms. The no-stall pair both achieves 3/3; safe-stop, expiry, censoring, overlap, clock misalignment, and zero-opportunity controls match their literal expectations. Any runner/audit/schema failure is terminal STOP; no retries or source changes after freeze. A synthetic PASS does not validate a live controller.
- **C:** Authored event/effect fixtures only; the region event records are part of the synthetic ground truth. One CPython 3.12 WSL process for candidate and a separate process for audit. Docker Desktop's Windows read-only `ps` timed out after 5 s; WSL's Docker Desktop context reported protocol-not-available; the shared OrbStack queue in #5085 still has four nonterminal `Created` containers without complete owner/lifecycle release. No container is used or modified.
- **U:** This establishes only finite accounting behavior under the authored clock, opportunity, region and effect rules. It does not prove coordinated omission in any existing benchmark, live opportunity exogeneity, event/effect oracle quality, actual task progress/safety, user benefit, runtime integration, or a general latency-correction rule. Opportunities caused or shifted by controller actions are out of scope; no posthoc regrading of MAP01 traces.

## Frozen execution

Construction before freeze: 12/12 standard-library contract and mutation tests; `python3 -B -m py_compile runner.py audit.py test_contract.py` passes. Formal commands, one-shot only:

```sh
python3 -B runner.py raw.json
python3 -B audit.py raw.json --out audit.json
```

The auditor runs once in a separate process only if the candidate exits 0. No external service, model, application, privileged data, or shared container is involved. Source files, plan, README and tests are hash-frozen before candidate execution; exact raw/audit bytes and exit receipts will be retained alongside that freeze.

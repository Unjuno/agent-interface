# Prelaunch freeze — Issue #7383 T0 A01

- Allocation: `GUI-OBSERVATION-HEDGING-7383-T0-20261004-A01`
- Frozen repository main: `13bab54ea6d91978247ecc1b70e5060db752367a`
- Repository main independently read immediately before this freeze: the same SHA.
- Package path: `research/analysis/observation_hedging_7383_t0_20261004/`
- Runtime: macOS 27.0.1 arm64, CPython 3.14.5, standard library only.
- Container disposition: OrbStack `docker info` returned server 29.4.0, but `docker ps` failed before inventory with `containerd ... blob ... operation not supported`. The identical failure was observed on a prior task. No retry, pull, build, or container candidate was attempted. This A01 is explicitly host-CPU, not container evidence.
- No model, GPU, GUI, external network, mutable application, or user input is used.
- Prelaunch output path `results/` is empty; formal invocation budget is candidate 1, auditor 1, retry 0.

## Frozen inputs

| File | SHA-256 |
|---|---|
| `spec.json` | `601fad3f6f5a3e9c3a3ccfe703999af2415417fd34a2f596eae84d44616fe0b6` |
| `candidate.py` | `2077d65f063a306ac33141a4010682a87a584ffeab928eb84891fccb56e35214` |
| `auditor.py` | `f3ea4ee630cbcde59f14d0746e8979a55f6b96c87065584b9385c90107e53099` |
| `test_package.py` | `bdde057c9f95062dbd595594ab82db8dfbf93177860ea781779dd6f8d8ec9e82` |

The construction suite passed 6/6 before this freeze. This is not the formal candidate/auditor result. After posting this freeze to Issue #7383, the only formal commands are:

```sh
python3 -I research/analysis/observation_hedging_7383_t0_20261004/candidate.py
python3 -I research/analysis/observation_hedging_7383_t0_20261004/auditor.py
```

The first command writes only `results/candidate.json`; the second reads that exact output, writes `results/audit_result.json`, and runs the four frozen corruption controls. Preserve stdout, stderr, process exit codes and UTC start/end times. Do not rerun either command after it has been invoked.

## Frozen method and decision

- Disjoint deterministic calibration deck: 200 traces; delay threshold is the nearest-rank empirical p90 of primary service time and is not recomputed from test rows.
- Test deck: 200 rows in each of five conditions: independent heavy-tail service, perfectly correlated tail service, a one-server shared queue, long cancellation lag, and a GUI-generation transition between the two captures. All arms use the same primary service-time row.
- Arms: one request, one delayed duplicate at the calibration threshold, and immediate duplication as a diagnostic upper-cost arm.
- Percentiles use nearest-rank p50/p95/p99. Duplicate work is completed/consumed secondary service divided by baseline primary service across the same test rows; ceiling 1.20. The primary target is the independent heavy-tail condition only: delayed-hedge p95 at least 10% below single-request p95, duplicate-work ratio at or below 1.20, and no increase in missed fixture deadlines. The fixture's independent score is timely complete current-generation observation; it is not an application effect or task-success score.
- Every complete response retains request ID, launch/start/capture/completion times, source generation, service work, cancellation request/ack and consumer decision. Stale/incomplete/wrong-generation responses may never be admitted, and at most one response may win.
- The independent auditor does not import the candidate. It reconstructs the full input deck and event ledgers, recalculates p50/p95/p99 and work/deadline outcomes, and rejects partial-response, old-generation-first, double-admission and omitted-loser-work mutations.
- `PASS_METHOD_SCOPED` requires the independent reconstruction plus all four mutation rejections and the target heavy-tail criteria. Failure or disagreement is retained as-is. No deployment, real capture-tail, end-to-end latency, or adoption inference follows.

The repository main commit is provenance only; all stimulus, simulation, scoring and audit code are hash-bound above. An unrelated main advance does not alter this finite synthetic input or retroactively change the allocation.

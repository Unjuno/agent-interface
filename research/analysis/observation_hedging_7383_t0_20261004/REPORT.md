# Issue #7383 T0 — freshness-gated observation hedging

**Disposition: `PASS_METHOD_SCOPED` for the finite declared simulator; real capture adoption remains HOLD.**

Allocation `GUI-OBSERVATION-HEDGING-7383-T0-20261004-A01` ran once on 2026-10-04 against frozen main `13bab54ea6d91978247ecc1b70e5060db752367a`. The standard-library candidate and independent auditor each exited 0; no retries. OrbStack was not used because `docker ps` failed with the previously observed containerd missing-blob error. This is host-CPU method evidence, not container evidence.

## Result

The disjoint 200-row calibration deck selected a 6 ms hedge threshold. The candidate generated 1,000 matched test rows across five conditions and three arms per row (3,000 arm results). The independent auditor reconstructed all rows, summaries, current-generation admission and loser work; it rejected all four preregistered mutations.

| Condition | Single p95 | Delayed hedge p95 | Delayed hedge timely current observations | Delayed hedge / baseline primary work |
|---|---:|---:|---:|---:|
| Independent heavy tail | 89 ms | 12 ms | 200/200 (single: 180/200) | 4.46% |
| Perfectly correlated tail | 89 ms | 89 ms | 180/200 | 63.58% |
| One shared server | 89 ms | 89 ms | 180/200 | 1.49% |
| 20 ms cancellation lag | 89 ms | 12 ms | 200/200 | 4.46% |
| Generation transition at 7 ms | 6 ms among 180 current single replies | 12 ms | 200/200 (single: 180/200) | 4.46% |

In the preregistered independent heavy-tail condition, p95 fell 86.52% (89→12 ms), delayed-secondary service was 4.46% of baseline primary service (below the 1.20 ceiling), and deadline misses fell from 20 to 0. The serialized shared-queue and perfectly correlated controls showed no p95 gain. In the generation-transition condition, stale responses were refused; the delayed arm's second capture occurred in the new generation, while immediate duplication still yielded on seven rows whose responses were both old by completion.

The result supports only the simulator's conditional statement: if a measured observation route has independent heavy-tailed service, concurrency, cancellation, and generation semantics like these declared inputs, a delayed single hedge can satisfy the frozen latency/work/deadline criteria. It does not show that any Agent Interface capture route has this service distribution or lies on a task's critical path.

## Parallel allocation boundary

During the post-run collision recheck, the Issue thread showed a separate WSLc allocation, `OBSERVATION-HEDGE-7383-T0-WSLC-20261004-01`, on branch `research/observation-hedge-7383-t0-wslc-20261004` and path `research/analysis/observation_hedge_7383_t0_wslc_a01/`. Its preregistration described 40 rows per stratum, an 11 ms threshold, and a different mean-service-work criterion; at that preregistration its candidate/auditor counts were 0/0. The branch/path and allocation are distinct. This A01 did not touch that branch or path, and the two output sets are not pooled or treated as one replication. Any later comparison must audit both frozen definitions independently.

## H / T / D / C / U

- **H:** Passed for the declared finite independent heavy-tail fixture; not generalized to real captures.
- **T:** 200 calibration rows; five conditions × 200 matched test rows; single, delayed and immediate-duplicate arms; exact service, capture, completion, epoch and cancellation traces; one candidate and one independent auditor.
- **D:** `PASS_METHOD_SCOPED`; full reconstruction 1,000/1,000 rows, four mutations rejected, p95 gain 86.52%, delayed duplicate-work ratio 0.0446, target deadline misses 20→0.
- **C:** Perfectly correlated service removed the gain; a serialized queue likewise left p95 unchanged. Immediate duplication cost more work and did not always rescue a generation change. The independent-tail benefit is therefore not robust to plausible shared-resource behavior.
- **U:** All delays and state transitions are synthetic and deterministic. The fixture score is a timing/current-generation score computed from its declared oracle, not application effect, task success, or user utility. No current critical-path measurement, Xvfb, GUI, model, real-world latency, safety, or deployment evidence exists.

## Next gate

Do not adopt hedging or start T1 just because this T0 passes. First establish on an eligible real route that complete-current observation acquisition is a straggler on the useful-feedback critical path. Then, only under a separately frozen/authorized allocation, test two read-only workers on a private disposable Xvfb application with an application-owned effect oracle, exogenous clock, source epochs, cancellation accounting and non-interference scoring. If no such critical-path route is evidenced, stop this branch of the idea.

## Reproduction

From repository root:

```sh
python3 -B -m unittest research.analysis.observation_hedging_7383_t0_20261004.test_package -v
python3 -I research/analysis/observation_hedging_7383_t0_20261004/candidate.py
python3 -I research/analysis/observation_hedging_7383_t0_20261004/auditor.py
```

The last two commands are the consumed A01 candidate/auditor commands. Do not rerun them under A01. Exact exits, timestamps, raw hashes and the first outputs are in `RUN_RECORD.json`, `results/`, and `SHA256SUMS.txt`.

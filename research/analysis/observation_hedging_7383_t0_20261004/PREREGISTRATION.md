## Issue #7383 — T0 preregistration A01

Allocation `GUI-OBSERVATION-HEDGING-7383-T0-20261004-A01`, frozen main `13bab54ea6d91978247ecc1b70e5060db752367a`, additive path `research/analysis/observation_hedging_7383_t0_20261004/`.

**H:** On the declared independent heavy-tail fixture, one delayed duplicate can lower p95 complete-current-observation latency by at least 10%, with delayed secondary work no more than 1.20× baseline primary service work and no increase in fixture deadline misses. Strong correlation/shared queue may erase the gain. This is not a claim about actual GUI capture tails.

**T:** 200 disjoint calibration rows set a nearest-rank p90 hedge threshold. Then five deterministic conditions each receive 200 matched rows: independent heavy tails, perfectly correlated tails, a single shared queue, long cancellation lag, and generation change between captures. Arms are single request, delayed single hedge, and immediate duplication diagnostic. Candidate and independent raw auditor are separate standard-library programs. The auditor reconstructs all requests, source epochs, completion/cancellation/work, unique winner, p50/p95/p99 and fixture deadline scores. Four predeclared corruptions must be rejected: partial response admitted, old-generation response accepted, double admission, and omitted loser work.

**D:** `PASS_METHOD_SCOPED` requires exact reconstruction of all 1,000 rows × 3 arms, rejection of all four mutations, no stale/incomplete/double winner, fully counted loser work, target p95 gain ≥10%, work ratio ≤1.20 and no worse deadline score. Any disagreement or failed criterion is retained; no threshold tuning or retry.

**C/U:** The independent-secondary heavy-tail case may be favorable by construction. Queue correlation, source-generation changes and cancellation work can remove benefit. This deterministic simulation is not measured critical-path evidence, real capture or application-effect evidence, a task benefit, nor authorization/adoption evidence.

Frozen input hashes: `spec.json` `601fad3f6f5a3e9c3a3ccfe703999af2415417fd34a2f596eae84d44616fe0b6`; `candidate.py` `2077d65f063a306ac33141a4010682a87a584ffeab928eb84891fccb56e35214`; `auditor.py` `f3ea4ee630cbcde59f14d0746e8979a55f6b96c87065584b9385c90107e53099`; `test_package.py` `bdde057c9f95062dbd595594ab82db8dfbf93177860ea781779dd6f8d8ec9e82`. Construction tests passed 6/6 before formal invocation.

OrbStack `docker info` succeeded, but `docker ps` returned a containerd missing-blob / `operation not supported` error. This same failure had already been observed; no retry/pull/build was made. Accordingly A01 is host CPU only: macOS 27.0.1 arm64, CPython 3.14.5 standard library, no model/GPU/GUI/network. Output directory was empty at freeze. Formal budget: candidate once, auditor once, retry zero.

Commands, each exactly once after this preregistration:

```sh
python3 -I research/analysis/observation_hedging_7383_t0_20261004/candidate.py
python3 -I research/analysis/observation_hedging_7383_t0_20261004/auditor.py
```

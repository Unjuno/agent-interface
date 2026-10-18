# Issue #8434 T0 A01 — equal-marginal disturbance-order method test

## H / T / D / C / U

**H.** Fixed synthetic route laws can rank differently when only the temporal ordering of the same 16 A / 16 B disturbances changes. If the held-out clustered/block schedules favor one route while the held-out alternating schedule favors the other, an IID-only average can conceal this authored path dependence.

**T.** Use the exact frozen `SOURCE.json`: 32 equal-duration, equal-intensity opportunities per sequence; four structures (`iid`, `clustered`, `alternating`, `heldout_block`); 12 calibration and 12 disjoint held-out seeds per structure. Compare two fixed stateful route laws plus two order-invariant controls. Candidate emits every opportunity and route outcome. A separately implemented auditor reads only source bytes and raw output, regenerates schedules, checks exact counts/intensity/duration, recomputes route outcomes and summary contrasts, and rejects five hostile mutations. No model/GUI/OS input is involved.

**D.** `PASS_METHOD_SCOPED` only if the raw-only audit reconciles all source-bound cases, all held-out exposure marginals are exact, both signs of the preregistered >=4-safe-effect paired median contrast occur on held-out correlated structures, the null pair is equal for every schedule, and all hard-gate fields pass. Otherwise retain the exact failure/HOLD. This is a method-fixture outcome, not evidence that any real interface exhibits the effect.

**C.** A memoryless route may depend only on marginal counts; a timescale profile may suffice; apparent order sensitivity may actually be a run-length or reset-position effect; or the authored route law may create its own crossover by construction. Equal marginals alone cannot rule out these explanations.

**U.** The simulator is deliberately finite and authored; it does not instantiate an Agent Interface runtime, model, GUI, human, or empirical disturbance process. Seeds provide reproducible schedule variants, not statistical sampling from a real workload. No population, causal UI, performance, safety, or route-selection claim follows.

## Frozen execution boundary

- Allocation: `DISTURBANCE-ORDER-8434-T0-A01-20261008`.
- Candidate and auditor each get one formal invocation after freeze; no retry or source edit after formal start.
- Container was preferred. OrbStack reports server 29.4.0 / overlayfs / cgroup v2, but image listing fails on the known containerd content-store `operation not supported`; no container invocation is made. This A01 is explicitly host-only, standard-library-only, offline, and does not claim container isolation.
- Formal output is immutable once written. Candidate failure, auditor failure, or infrastructure STOP is recorded without relabeling.

## Reproduction

From this directory, with Python 3.14.5:

```sh
python3 -B candidate.py SOURCE.json formal_01/RAW.json
python3 -B audit.py SOURCE.json formal_01/RAW.json formal_01/AUDIT.json
```

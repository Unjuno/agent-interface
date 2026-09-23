# Issue #2966 natural UNO contention — bounded container result

Task: `LO-NATURAL-CONTENTION-2966-20260920-01`  
Issue: [#2966](https://github.com/Unjuno/agent-interface/issues/2966)  
Image: `agent-interface-lo2966:20260920@sha256:551f399a59ec7bd238d22c11c5d53ee14a12be6ede6d5184e4320e6cf62a7944`  
Network: `none`  
Runner SHA-256: `e4dbbe55c46d1ff155f3a45961518456400ef57fc0680b8e1cf113326eb42349`

## H / T / D / C / U

- H: a cooperative expected-state boundary must refuse a stale A mutation or require re-observation; it must never report the stale intended effect as success.
- T: run stable, natural A/A contention, unrelated B mutation, and recovery-after-re-observation rows against the fixed Draw A/B fixture. No parent barrier and no macro sleep are used by the runner.
- D: `PASS_NATURAL_CONFLICT_BOUNDARY_SCOPED` requires stable application, typed natural conflict, exactly-once recovery, unrelated-B independence, and typed audit rows.
- C: one LibreOffice build, one local UNO topology, one Draw fixture, three repetitions per arm; no crash atomicity, distributed transaction, production authorization, general GUI, or race-probability claim.
- U: runner source is additive local evidence pending GitHub publication; #438 forced-interleave rows remain separate.

## Result

`PASS_NATURAL_CONFLICT_BOUNDARY_SCOPED`.

The block completed 12 rows (3 per arm) in fresh container invocations:

| arm | rows | typed outcome pattern | final A/B |
|---|---:|---|---|
| stable | 3/3 | `APPLIED` | 1200 / 5000 |
| natural A/A | 3/3 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1700 / 5000 |
| unrelated B | 3/3 | writer B `APPLIED`; controller A `APPLIED` | 1200 / 5500 |
| recovery | 3/3 | writer `APPLIED`; stale controller `CONFLICT_REJECTED`; fresh recovery `APPLIED` | 1200 / 5000 |

Every row emitted a typed outcome from `{APPLIED, CONFLICT_REJECTED, REOBSERVE_REQUIRED, BACKEND_FAILURE, UNKNOWN}`. No stale intended A mutation was classified as successful. Recovery used a new observation of A=1700 and applied A=1200 once; it did not replay the obsolete expected value.

## Boundary and non-claims

The runner uses ordinary independent Python/UNO threads with bounded joins. It does not reproduce #438's parent-controlled validation barrier or fixed 500 ms macro sleep. This result is evidence for this cooperative local boundary only; it does not estimate natural race frequency and does not generalize beyond the pinned environment and fixture.

The exact raw per-row JSON was generated under `/tmp/lo2966-block-BC7TkX` during the container run; the compact table above is the retained publication summary. The source runner is retained locally at `work/lo2966_natural.py` and must be committed together with a machine-readable `RESULT.json` before integration.


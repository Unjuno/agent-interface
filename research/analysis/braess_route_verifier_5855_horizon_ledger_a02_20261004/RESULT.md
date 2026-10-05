# #5855 finite-horizon ledger transfer — A02

**Scoped result: `PASS_HORIZON_LEDGER_TRANSFER_SCOPED`.** An independently implemented auditor reconstructed all 416 task rows across 26 policy arms from the immutable #5855 T0 result and verified event-prefix task conservation with a common finite horizon. The predecessor source and its original disposition were not modified or rerun.

## H / T / D / C / U

- **H:** Task-ID accounting with an explicit observation horizon can be transferred to the original six-cell route-addition T0 without dropping offers or counting post-horizon work as observed completion.
- **T:** Read the predecessor result frozen at main `bb3138d019118bf050fe1136a9ba3619146bb46e`; 6 cells × 4 principal policies, plus 2 held-out disjoint controls. The horizon in each cell was last offer time + 32 ticks. Candidate once, raw-only independent auditor once; no retry.
- **D:** Candidate emitted 26 arms, 416 per-task rows and 832 OFFER/disposition events. Auditor exited 0 with `PASS_HORIZON_LEDGER_TRANSFER_SCOPED`. At every event prefix, offers equal verified terminals + right-censored tasks + active tasks. All 416 offers had exactly one disposition; duplicate receipt IDs, duplicate terminal transitions and missing task dispositions are rejected by five pre-freeze mutation tests. Across arms, 83/416 tasks were right-censored at the chosen horizon. In the held-out `(interval=8, fast verifier=12)` cell, baseline had 16/16 verified terminals by horizon; greedy route-added had 12/16 and 4/16 right-censored. The predecessor's complete-schedule latency metrics remain unchanged; a mean over only the 12 observed greedy terminals is not treated as a denominator-complete system mean.
- **C:** This is an accounting projection of already retained deterministic synthetic task schedules. It does not independently validate the predecessor simulator, change any routes, or prove a real queue effect. The new common horizon is an A02 observation boundary, separate from the predecessor's per-task deadline metric.
- **U:** No online runtime, model, GUI, input, real arrivals, or service distribution was exercised. Since the retained raw includes eventual completion times, this tests deterministic horizon classification, not online censor detection. No stationarity or production throughput inference follows.

## Reproduction

From this directory, with CPython 3.14.5:

```text
python3 -B candidate.py  # one invocation; exit 0
python3 -B audit.py      # one invocation after candidate; exit 0
```

The source candidate hash is `ba5ee3c03bcf1105fd6bbbd0278b710fffb014cdd865f988f2d5649cb0bb4361`; predecessor freeze hash is `c2435408c1e7117a909fb95d9151bfaadfa231db30d9a3d83d6d6f5ba3b73828`. See `FREEZE.json`, retained stdout receipts, and `SHA256SUMS`.

OrbStack Docker server version was 29.4.0, but image metadata enumeration failed on a missing containerd content blob (`operation not supported`); no container started. This bounded deterministic transformation ran on host CPU. This is not container validation.

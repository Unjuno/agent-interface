# Issue #3965 — preformal source freeze

Allocation `native-paced-capture-batched-20260922-02`; parent #3949 is terminal STOP and is never resumed, pooled, rerun or overwritten. Base main remains `b2457b746a6df06f6536585dfe2ab937aff639f4`. Owned additive branch: `research/x11-native-paced-capture-20260922-v1`.

Local `FREEZE.json` SHA-256: `3429ae65f74c687a530f178c4691132485ae4a11ff0393826af078959fae7c11`.
Local `PLAN.md` SHA-256: `e6c5f88e8981458814e06483f90a09dc90d24543b2204f9cde25e3f15edd43bd`.
Formal cases/invocations at this freeze: **0**.

The six inherited experimental source/binary files are byte-identical to the v1 source freeze: native.c, native.so, fixture, study.py, audit.py, test_audit.py. The old monolithic entry point is not invoked; only its case entry point is used. The parent source archive SHA-256 remains `85eb6fe450ddfac4f9971134cbd69d3a687a7ea7d5b8865660ad1a8643da68b4`.

New frozen files:

| File | SHA-256 |
|---|---|
| src/batched.py | cb3e4a9e916c3480576398ecc233a692ba4a0dab982fffd27d87cbe13b6d2b91 |
| src/audit_batched.py | 4c9458fdf9fbbad7afa8805db9ca69f9f0ba27cf97d66d006618b0600862d575 |
| src/test_batches.py | f6822fab49d0a568cfcbc9131340781fa2e6612b53fabaa5f7926746a34c995a |

The exact sources and construction artifacts are locally retained at this freeze; lossless publication follows separately. This is a source-hash timestamp, not a claim that raw formal data already exists on GitHub.

## Fixed execution

Five exclusive-create batches: [0,8), [8,16), [16,24), [24,32), [32,40). Each requires preceding successful external exit receipts and unchanged allocation/source/CPU/raw hashes. Each case has a six-second deadline; on timeout its owned process group is terminated and the allocation stops. Each batch is issued in its own 60-second tool invocation. Missing external batch exit is HOLD/STOP, never inferred as zero. Failed batches are not retried and later batches are not run.

Exactly once, in order:

```sh
python src/batched.py 0
python src/batched.py 1
python src/batched.py 2
python src/batched.py 3
python src/batched.py 4
```

For each command, retain stdout/stderr and its actual shell exit in batch-00.exit.json through batch-04.exit.json. Independent final audit: `python src/audit_batched.py . > AUDIT.json`.

## Unchanged scientific gates

Twenty matched pairs; balanced Python/native order; nominal 5 ms cue at offsets 120/122/124/126/128 ms repeated four times; 300 ms sampling; 2 ms non-catch-up cadence; 1 ms Python switch interval; identical CPU-bound Python thread; observer/load/Xvfb+fixture CPUs 0/1/2. Native/Python arms share the exact acquisition/count helper.

All 40 fresh rows and five zero external exits must reconcile. Every cue exposure is 4–8 ms. PASS_NATIVE_PACED_CAPTURE_SCOPED additionally requires >=18/20 native detections, median paired native/Python max-start-gap ratio <=0.70, and >=2 native-hit/Python-miss pairs. Integrity-complete gate miss is HOLD_NATIVE_PACING_BENEFIT_NOT_ESTABLISHED. Otherwise typed STOP/HOLD/FAIL; no subset verdict, pooling, threshold tuning or replacement.

## Construction and scope

One new excluded two-case batch completed; original raw pixel/time/load/affinity/cleanup audit has zero errors. Eight final wrapper test methods pass, with sixteen corruption variants rejected using an explicitly synthetic padded reconciliation envelope. No formal measurement is fabricated from that envelope. Earlier construction sources and test outputs are preserved. The six inherited experimental hashes are verified exact.

Only the supplied Linux x86_64 execution container / CPython 3.13.5 is claimed, not Docker/OrbStack. No model/provider/network-in-experiment, XTEST, keyboard/mouse, or shared-runtime change. Batch boundaries stay between pairs but add idle/host-scheduling variation. Captures are returned after the window, not online to a model. No fresh action authority, release safety, task/cost benefit, production readiness, or hard-real-time claim. #2117 and the global roadmap remain open.

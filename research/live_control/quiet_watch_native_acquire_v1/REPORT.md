# Native XGetImage at fixed 2 ms cadence: HOLD

**Decision: `HOLD_COST_GATE`. Do not promote this acquisition path into shared runtime.**

Task `QUIET-WATCH-NATIVE-ACQUIRE-20260916-001`, Issue #236; successor to #225 / PR #231. Publication BASE `821d214b13500db52e6b34ff57b6ece59a76142f`; source/preregistration freeze `b618fcb3d4c5fd74be6a6e92989884fd55298327`. Only this new research directory is changed. The exact upstream #231 runner is imported with its SHA-256 checked, not modified. There were zero model/game calls and no production InputOwner integration.

## Frozen question and allocation

Replace Python-Xlib's protocol implementation of full-ROI XGetImage with a small native libX11 adapter. Keep the same server operation, 32x32 ROI at (48,48), exact BGR equality/count predicate, threshold 512 pixels, nominal 2 ms polling, nominal 5 ms target cue, XTEST Right input, 600 ms authority deadline and cancellation behavior. Both arms use the same timing wrapper, bytes copy, classifier and original fixture/scheduler. Neither shared memory, subsampling nor a cooperative cue latch is introduced. The acquisition-path intervention includes ctypes/GIL behavior; it is not a pure protocol-overhead intervention.

One fixed serial block contained 15 target pairs (offsets 150/152/154/156/158 ms, three repetitions) and four nuisance pairs. Pair order was shuffled once with seed 23620260916; within-kind arm order alternated (target 8/7, nuisance 2/2). All 38 first outcomes were retained. No retry, replacement, extension or threshold tuning followed measurement. Nuisance controls, rather than early-cancelled targets, provide matched full-window cost comparisons.

The frozen cost gates require BOTH median paired total-acquisition-wall ratio and median paired per-sample ratio to be no more than 0.8. Native must detect all 15 targets; no false nuisance cancellation or release/integrity failure is allowed; all nuisance acquisition counts must remain in 270..330. Cue-width reduction was descriptive, not an acceptance gate.

## First outcome

| Endpoint | Python protocol | Native libX11 |
|---|---:|---:|
| Targets detected | 15/15 | 15/15 |
| Nuisance false cancellation | 0/4 | 0/4 |
| Nuisance acquisition wall, median [range], ms | 80.032 [65.147,94.617] | 65.964 [47.609,91.650] |
| Nuisance getter thread CPU, median [range], ms | 47.296 [41.983,53.771] | 20.464 [20.108,25.057] |
| Getter plus predicate wall, median [range], ms | 113.286 [89.234,152.306] | 105.720 [81.229,152.880] |
| Nuisance acquisition count, median [range] | 292 [286,299] | 297.5 [282,302] |
| Largest observed nuisance end-to-next-start gap, ms | 20.864 | 7.137 |
| Target draw-completion cue width, median [range], ms | 5.534 [5.255,6.749] | 5.478 [5.225,9.728] |

Paired native/Python total-wall ratios were 0.773498, 0.968644, 0.887655 and 0.730784. Their median was **0.8305765658061821**, which fails the predeclared 0.8 gate. The paired per-sample median was **0.8073599682802832**, also above 0.8. Do not substitute a ratio of group medians for the median of paired ratios, or round either outcome into PASS.

All 38 cases verified empty Right-key state, exactly one application-observed press and release, and a clear final ROI. The unchanged frozen audit independently reclassified **4,616 ROI captures**, including final captures, from their retained pixel bytes. Sampling-count integrity passed. Evidence integrity passed; the mechanism's cost gate did not.

## Interpretation: facts versus inference

**Observed:** both configurations detected the finite target set. Native getter thread CPU was lower, while the required wall-time reduction was not reached. Nominal 2 ms scheduling still produced much longer acquisition gaps. The native maximum measured cue duration was larger than the baseline maximum.

**Inference:** reducing client-side CPU does not necessarily reduce synchronous acquisition wall cost sufficiently on this host. Server work, scheduling, transport wait and GIL behavior remain possible contributors. The experiment does not identify their separate magnitudes. Moving acquisition alone is not enough evidence for the proposed promotion.

**Not established:** population detection reliability, lower total system CPU, a robust reduction in cue-duration distortion, arbitrary-GUI semantics, gameplay benefit, hard-real-time behavior, or a production rollout. Fifteen detections out of fifteen are not a guarantee. This is not a replication with the same host as #231; use only the within-block comparison for the present inference.

## H / T / D / C / U

**H:** at fixed 2 ms cadence, native full-ROI acquisition can lower the two declared paired wall-cost measures by at least 20%, while preserving detection and release correctness.

**T:** the source-frozen, balanced-order 38-case allocation above; first outcomes only. No sequential extension. Seven excluded static byte/threshold checks at 0/1/511/512/513/1023/1024 target pixels, two C invalid-argument guards and four excluded live preflight cases preceded the freeze.

**D:** `HOLD_COST_GATE`; retain negative evidence, no production promotion. Raw/source/release audit passes are distinct from the cost decision.

**C:** native/FFI/GIL scheduling could influence both getter wall time and producer cue duration. Python predicate work remains in both arms. Four nuisance pairs cannot resolve tail behavior or cross-host effects. Neither a CPU reduction nor a smaller median cue width proves less observer perturbation.

**U:** one synthetic declared-colour fixture, one shared virtual host, unpinned CPU frequency/affinity, software draw-completion timestamps rather than physical scanout. Thread CPU sums exclude X server and the rest of the process and include clock-instrumentation overhead. These data do not support a calibrated combined standard uncertainty or coverage factor; none is fabricated. Raw nanosecond clock differences are reported as milliseconds; both cost ratios are dimensionless. Advertised 1 ns clock resolution is not timing accuracy.

## Measured implementation conditions

Private Xvfb :97, 640x400x24, Xauthority enabled, TCP disabled. Linux 6.18.44 x86_64, glibc 2.41, Python 3.13.5, **python3-xlib 0.15**, libX11 1.8.12, Tk 8.6.16, Xvfb 21.1.16, GCC 14.2.0. CPU reports Xeon Platinum 8370C nominal 2.8 GHz; affinity 0..4 and frequency unpinned. Measurements are one serial block, no batching or parallel live cases. Full environment receipt is in raw JSON.

Build: `gcc -O2 -fPIC -shared -Wall -Wextra -Werror native.c -lX11 -o native.so`. Measured binary SHA-256: `e0fa1d64111776414f4106761533ba981ced5024d2f58f2047558fb49aa9837f`. The C ABI checks depth 24, 32 bits per pixel, 128-byte stride, little-endian byte order and RGB masks before copying all 4096 bytes. Other layouts are unsupported, not silently reinterpreted. Fresh live runs on different toolchains require a new preregistration, not modification of this frozen binary hash.

## Complete formal raw retention and replay

The formal canonical JSON is **1,315,566 bytes**, SHA-256 `94cd656928acca74375ab824f13ef8d5476f79dad50d0d4fd5541ecab63f7bc7`. Every pixel payload and acquisition bracket is retained, not only derived case summaries.

`codec.py` is an offline transport codec added after measurement; it never participated in observation or scoring. Column-delta/variable-integer encoding and XZ compression reduce the exact raw file to 64,496 bytes. Eleven binary parts under `raw/` were uploaded through GitHub MCP; each returned Git blob SHA matched the local source bytes. `manifest.json` records the part SHA-256/Git blob identities, archive hash and original raw hash. Local decode plus byte comparison reproduced the formal JSON exactly. The frozen scientific source and audit were not changed for publication.

From a checkout, replay with Python standard library only; no display or compiler is required:

```sh
python research/live_control/quiet_watch_native_acquire_v1/replay.py --out /tmp/qnative-replay-new
```

Use a new output directory and do not use `python -O`. Replay verifies every retained part, archive and raw hash, recomputes the frozen audit, compares the full summary with `result.json`, and tests eight evidence mutations. Pixel corruption, count changes, missing release, swapped schedule, source mismatch, negative CPU duration, deadline changes and final held-key state were each rejected. These are evidence-integrity controls, not additional live cases.

The old #231 missing raw remains missing; this complete retention applies only to #236. Excluded preflight raw/logs are in the conversation evidence bundle, not these formal raw parts.

## Retained setup/audit limitations

The first setup command failed a lookup for distribution name `python-xlib` before GUI construction. It was repaired to report the actually installed `python3-xlib` package; no timing gate was tuned. One offline audit invocation with a relative preregistration path failed upstream-file resolution; the same frozen audit passed with an absolute preregistration path. `replay.py` supplies that absolute path. Neither failure consumed another live allocation. An accidental duplicate coordination Issue #239 was immediately closed; #236 is the only experiment identity.

## Exactly one successor question

Before a more complex backend or shorter period, hold one acquisition path fixed and test whether moving only the unchanged full-ROI predicate into native code reduces getter-plus-predicate wall cost without any byte-classification disagreement. First establish bit-exact equivalence on threshold/boundary inputs. This is a proposed successor, not another started allocation and not an inferred solution to server/scheduling delays.

Relevant transfer disciplines: real-time systems (sampling gaps), measurement science (observer perturbation and separate clock endpoints), and HCI/input safety (release ownership independent of sensing cost).

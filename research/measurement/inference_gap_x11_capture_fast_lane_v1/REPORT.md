# #1523 10 Hz capture × bounded fast-lane composition — retained result

Decision: **PASS_CAPTURE_FAST_LANE_COMPOSITION_SCOPED**.

Formal first outcome: one logical allocation, four immutable batches, 24 matched pairs / 48 fresh private-X11 sessions, reruns 0. The capture arm adds a separate 10 Hz 320×240 raw-XGetImage observation plane while preserving the identical 5 ms edge-triggered F8 controller.

Safety/correctness gates all pass: expected useful-effect counts match in every pair; WATCH/HARD effects 0; post-handoff sends/effects 0; terminal release failures 0; exceptions 0.

Measured candidate values:
- ACTIVATE p95: **5.513790 ms** (<12 ms gate)
- YIELD p95: **4.476611 ms** (<12 ms gate)
- 10 Hz capture p95: **1.892923 ms** (<10 ms gate)
- paired median candidate-minus-control ACTIVATE-p95 increase: **0.064482 ms** (<=2 ms gate)
- maximum matched candidate ACTIVATE excess: **1.150092 ms** (<=10 ms gate)
- capture count minimum: **4** per capture session; max ring frames **4**; control host-noise sessions **0**.

The formal batches, aggregate and independent audit completed before an outer wrapper timeout occurred during the subsequent corruption command. The formal allocation was **not rerun**. Corruption controls were then executed separately as postformal verification only and rejected 5/5 mutations. Postformal scientific-source rehash matches every frozen member exactly.

RESULT SHA-256: `f0a338e4e55d4bd370090cc6549e82856da81ad33ec62e314ad686cc293dda02`. AUDIT SHA-256: `1f97a4b8a1abd7125737ced3957eadd62b870c596249fa536ba4d6b258a86415`. Raw first outcome is retained losslessly as base64 xz/tar with xz SHA-256 `fb904347b880b905ab85870d51326a1e1c70dca5e77230fd3d24ae8184b82463`.

Scope is narrow: one private-X11 320×240 fixture, separate Xlib capture connection, nominal10 Hz capture, one-key edge-triggered bounded lane and a 300 ms simulated frontier gap. This establishes scoped concurrency compatibility only; it does not establish a real-frontier/model, full-screen/high-DPI, encoding, token, task-level speed, human-tempo or production result.

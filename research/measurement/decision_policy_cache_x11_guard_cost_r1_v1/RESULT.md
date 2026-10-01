# Result

Decision: **PASS_X11_ACTION_GUARD_ROI_COST_SCOPED**

- Formal: 24 matched pairs / 48 private-X11 cases, 408 guards per arm.
- Classification mismatch: full 0, ROI 0.
- Stale hard-invalid effects: full 0, ROI 0.
- Ambiguous effects: full 0, ROI 0.
- Guard p95: full 1.454179 ms; ROI 0.221238 ms; ratio 0.152139.
- Guard p99: full 1.832951 ms; ROI 0.318803 ms.
- ROI hard-invalidation-to-stop p95: 2.475851 ms.
- ROI action-start lag p95/max: 0.015730/0.077779 ms.
- Bytes/guard: full 307,200; ROI 4,096.
- Transition-overlap captures: full 0; ROI 0.
- Host-noise cases: full 0; ROI 0.
- Authority actions 0; formal1/reruns0; cleanup and independent audit pass.

Interpretation: on this private Xvfb/XGetImage sentinel fixture, the 32x32 action-time visual guard preserves the same exact no-effect/yield/invalidate semantics as 320x240 capture while materially reducing acquisition cost and transferred bytes. This does not establish production compositor, arbitrary semantic ROI extraction, model-token, or end-to-end speed claims.

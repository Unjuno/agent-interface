# A02 positive-frame visual check

This is author visual inspection, separate from the programmatic replay auditor. I opened the two frames the frozen OCR recipe marked exact and confirmed that the layout-B Value field visibly contains the exact scorer token.

| Arm/task | Frame | SHA-256 | Expected and visible value |
|---|---|---|---|
| plain / task-4 | `research/live_control/results/integrated-efficiency-live-orchestration-probe-02/arms/plain/runtime/065.png` | `531036021e694ebaf5dd54ff58dfce082c13cf1aebb050249bf7062609a6d4cf` | `t991028-4` |
| persistent / task-4 | `research/live_control/results/integrated-efficiency-live-orchestration-probe-02/arms/persistent/runtime/083.png` | `d4deab9d6b3330fb92fafc9dcef4c64e85f7734514465e10292a7a26caaa14ca` | `t991028-4` |

No task-5 or task-6 frame was called a visual positive because the exact OCR output is absent. This check does not change A02's frozen failure for four of the six task-arm cases.

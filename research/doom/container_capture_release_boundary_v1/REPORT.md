# Capture/release boundary ordering micro-test v1

Status: **BOUNDARY_CAPTURE_COST_CANDIDATE** in the rendered Xvfb/Tk/XTEST fixture.

This is the next one-variable discovery step after the capture-during-hold test rejected capture presence alone as the primary explanation. The hold target, key, rendered fixture, XTEST path and capture operation stay fixed. Only ordering at the 250 ms release boundary changes.

## Frozen conditions

- `release_first`: at the 250 ms deadline send `KeyRelease` + X sync, then perform one full-frame Pillow `ImageGrab`.
- `capture_first`: at the same deadline perform the same full-frame `ImageGrab`, then send `KeyRelease` + X sync.
- 12 balanced matched pairs; no retry.
- primary metric: paired `capture_first - release_first` application-observed press-to-release duration.
- candidate threshold: median >= 5 ms OR p95 >= 10 ms.

## Environment

- CPython 3.13.5
- Linux 6.18.44 x86_64
- Xvfb 1024x768x24 + Openbox
- rendered 900x600 Tk checkerboard
- XTEST `w` KeyPress/KeyRelease
- no model, ViZDoom, gameplay state, planner, renewal or shared runtime

## Result

| Metric | Release first | Capture first |
|---|---:|---:|
| n | 12 | 12 |
| application-observed hold median | 250.111106 ms | 255.963309 ms |
| application-observed hold p95 | 250.240213 ms | 259.834836 ms |
| send-hold median | 250.117006 ms | 255.731369 ms |
| deadline -> KeyRelease median | 0.117006 ms | 5.731369 ms |
| capture median | 3.618421 ms | 5.286453 ms |
| KeyRelease send -> app release median | 0.553999 ms | 0.456029 ms |

Paired `capture_first - release_first` application hold:

- median: **+5.791928 ms**
- p95: **+9.711145 ms**
- range: **+2.832981 to +10.963741 ms**

The preregistered median threshold is crossed. The extra delay is close to the capture duration, supporting a narrow causal interpretation: observation work placed before physical release holds the key longer by roughly the duration of that work in this fixture.

## Interpretation

This identifies an ordering mechanism, not a complete explanation for previously observed tens-of-ms retention. Raw capture alone contributes about 6 ms median here. The next one-variable step should retain the same boundary ordering and add one artifact-processing layer (PNG encode/write/reopen) before release, to test whether retained-observation processing can scale the delay into the larger regime.

## Provenance

- base commit: `8d7bd88197cd4553251d1c47bff5b94bad8c499c`
- source SHA-256: `bda5f20934ddf5f03fda7a37de3d6bccf8b318292f14f3d3b4b94b99beadbf7f`
- preregistration SHA-256: `45a32d89b980a64b178358889db6cdc6fa2b949aab410526fd898470f0f16b95`
- result SHA-256: `24f8b666934b7ea93e839bd9689676648e31cfead76a781dfacc28f932dc48cb`
- raw formal case count: 24
- construction smoke: 2 pairs, excluded from formal aggregation

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, hard-real-time, human timing, model, planner, or production-runtime claim.

# Issue #6581 T0b preregistration — disposable constrained-path fixture

Allocation ID: `PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01`  
Branch: `research/path-width-continuous-gui-6581-t0b-20261002`  
Additive result path: `research/analysis/path_width_continuous_gui_6581_t0b_v1/`  
Base: main `60e2e7bb8a69cb7270fc2082e0affc5bf2789876`  
Predecessor: Issue #6581 T0 read-only feasibility `STOP_DATA` (preserved; not retried).

## H / T / D / C / U

**H.** In a software-defined GUI fixture with explicit continuous corridor semantics, identical start/end coordinates can conceal path-validity and saved-effect differences. Holding centerline, endpoints, input trace, task, and timing constant while changing only width should change whether a near-boundary trace is accepted. A path that exits then returns to the correct endpoint must remain a failure.

**T.** T0b constructs a disposable local SVG/canvas-like GUI with an explicit pointer-event boundary and save rule. A browser emits discrete pointer events; the fixture defines each consecutive pair as a straight swept segment and checks that the entire segment is covered by the declared corridor polygons. A separate Python auditor consumes only frozen fixture definitions and raw browser events, independently reconstructs continuous segment coverage and endpoint/effect outcomes, and compares those with the app receipts. The fixture includes:

1. Same straight centerline, same start/end/contact rule and same input trace at `y=37`: wide half-width 10 vs narrow half-width 4 (primary width contrast).
2. One piecewise-linear variable-width corridor with the same centerline and trace.
3. An orthogonal-corner corridor with a trace following both arms.
4. A narrow-corridor adversary that exits and later reaches the exact endpoint.
5. An ordinary no-corridor drag control whose path validity must remain `NOT_APPLICABLE`, not inferred from imagined bounds.

All task/layout/trace coordinates, polygon definitions, endpoint tolerance, browser viewport scale and scoring rule are fixed in `spec.json` before candidate execution. No live human/model, real app, real OS input, GPU, network access from the container, or product runtime is used. Wall-clock/efficiency is not an estimand.

**D.** `PASS_METHOD_SCOPED` only if: (a) the independent auditor reproduces all raw browser pointer events and app receipts without errors; (b) the primary shared-centerline contrast is accepted only in the wide arm and rejected in the narrow arm while endpoints and input points are identical; (c) the variable-width and corner controls match their frozen oracle; (d) the endpoint-after-exit adversary has an endpoint hit but no saved effect; (e) the ordinary drag control has a saved endpoint effect but path validity `NOT_APPLICABLE`; and (f) corruption controls for raw event deletion/reordering, geometry mutation, false endpoint receipt, and false saved effect are all rejected. Otherwise preserve `FAIL` or `STOP`; no retries of the formal candidate or auditor.

**C.** This test codes the path rule into a custom fixture, so it establishes neither that ordinary GUI applications enforce such paths nor that agents/humans move continuously through them. Event-to-event straight interpolation is the declared app semantics, not an assertion about unobserved physical motion. A width-dependent acceptance result may be tautological to the fixture's geometry rule.

**U.** No Steering-Law fit, human/agent performance, path-choice behavior, phase-time bottleneck, GUI product, real input, task benefit, or safety claim. The external HCI transfer, T1, and DOOM are out of scope. This T0b can only establish fixture/oracle feasibility and the preregistered endpoint-vs-path divergence.

## Frozen run contract

- Build/run in a fresh dedicated OrbStack Ubuntu 24.04 ARM64 machine with its own Docker Engine; do not use another worker's machine or shared Docker daemon.
- Pin the official Playwright browser container by resolved image digest and platform in `FREEZE.json`; require its package version to match the image release and a clean npm audit before freezing. Run with container network disabled, read-only root filesystem, source/dependencies read-only, a separate output bind, and bounded CPU/memory/PIDs. Record requested vs observable resource limits without claiming enforcement not verified.
- Construction suite may be iterated and recorded before freeze. Once `FREEZE.json` and this preregistration's source digest are posted to Issue #6581, formal candidate and independent auditor each run once. No retries or edits to the frozen sources/results.
- Candidate raw JSON, stdout/stderr, exact command/exit receipts, independent audit, and SHA-256 manifest are retained under `formal_01/`.

## Prior-art boundary

The retained #6581 read-only STOP_DATA and #4388/#4424 endpoint/effect evidence remain unchanged. This new allocation implements a controlled synthetic path-constrained GUI fixture; it does not reinterpret those predecessors as path evidence. The Steering index is not a safety certificate.

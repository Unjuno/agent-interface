# Issue #8185 A02 pre-candidate protocol

**Status:** infrastructure STOP before candidate construction or formal allocation.

## H / T / D / C / U

**H.** A typed epoch-bound affine transform chain with bounded uncertainty agrees with an independent exact transform oracle, rejects stale/unmodeled controls, and reduces false `UNKNOWN_REFUSE` by at least 20% versus a frozen single-origin, last-known-scale/offset comparator on the declared valid composed-affine stratum.

**T.** A future eligible allocation must start from a clean current-main commit and freeze protocol, candidate, fixture, hidden edge matrices, target geometry, comparator calibration/update schedule, truth, output schema, and hashes before invocation. The oracle independently composes exact matrices and maps point/region corners through the total transform. The candidate must not receive hidden matrices or truth. The comparator must use one capture-origin plus its last-known uniform scale/offset per declared calibration state, with a predeclared public update schedule; it may not refuse merely because the graph uses multiple edges. Include an inverse-shear pair whose composite is identity; crop/presentation, client/window, monitor-origin, uniform/mixed-DPI transforms; a real 7→8→9 epoch chain; shared versus independent uncertainty; and stale, missing, reversed, duplicate, unit, DPI-context, identity, non-affine, boundary, and forbidden-region controls. Run construction, one candidate, then one independent auditor, without retries.

**Runtime gate.** Use the project-directed OrbStack container on this macOS host. Do not substitute host execution, another container runtime, or repair/pull the shared store. If read-only runtime/image preflight fails, record STOP before candidate invocation.

**D.** PASS requires every decision and mapped value to match the independent exact oracle, zero false admissions, every invalid control refused, and at least 20% false-UNKNOWN reduction. Wrong-target admission or stale-chain acceptance is FAIL_UNSOUND; no incremental value is FAIL_NO_INCREMENTAL_VALUE. Missing oracle/provenance coverage or a failed runtime gate is HOLD/STOP, never PASS.

**C.** A capture-bound mapping plus invalidation, or an OS-provided current mapping, may suffice; a conservative calibrated scalar comparator may match the graph.

**U.** Even a future finite-model PASS would not establish native DPI/backend behavior, calibration distributions, GUI hit-testing, latency, safety, semantic effects, or product readiness.

## This allocation

This allocation stopped at the runtime gate. No construction suite, candidate, or auditor was invoked. No scientific outcome is available. The STOP evidence is in `ORBSTACK_PREFLIGHT.*` and `RUN.json`.

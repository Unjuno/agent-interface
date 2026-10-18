# A01/A02 results

## A01 baseline

`FAIL_RECEIPT_NOT_EMITTED_BEFORE_EXPIRY_TERMINAL`. One admitted F8 down had a matching owner-confirmed per-key physical-up record after the blocked cleanup sync resumed, but the bridge emitted zero `input_release_measurement` events before the single `expired` terminal. Fake physical and bridge-held state were empty. This is a telemetry-custody gap, not a physical release failure. Raw output and audit are retained under `results/formal_01/`.

## A02 minimal repair probe

`PASS_RELEASE_ALL_DRAINED_PENDING_EXPIRY_RECEIPT_SCOPED`. Under the same synthetic schedule, adding a `release_all()` finally-drain caused exactly one matching per-key release measurement to reach the bridge event stream before the single `expired` terminal. The owner record independently confirms physical up; aggregate release events remain absent; fake physical and bridge-held state are empty. Raw output and audit are retained under `results/formal_02/`.

## Scope and limits

Both runs use fake Xlib and current pinned ExecutorV12. A02 validates only this one cleanup-pending interleaving and the minimal drain probe. It does not establish production readiness, live X11 ordering, game/application effect, useful feedback, recovery efficacy, threat response, latency, MAP01 progress, or Issue #59 completion. Container was not launched because OrbStack failed before startup on the prior identical image-blob attempt; this explicitly labeled native run is not container-equivalent. See `CONTAINER_DISPOSITION.txt`.

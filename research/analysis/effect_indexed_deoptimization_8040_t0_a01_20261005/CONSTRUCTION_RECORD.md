# Construction record — Issue #8040 T0 A01

## Scope
The construction qualifies a finite three-operation semantic-cursor reconstruction method. It covers 12 authored rows across before/after safepoints, a one-to-many instruction midpoint, VERIFIED/NO_EFFECT/UNKNOWN effect receipts, stale generations, invalid/missing map locations, malformed receipt bindings, and specialized-program end without task-success inference. UNKNOWN after a VERIFIED prefix preserves that known prefix in the ledger but withholds the generic cursor. It is not an empirical GUI/runtime test.

## Construction commands and outcome
- `nice -n 10 python3 -B build_fixture.py` — deterministic 12-case fixture; mapping SHA-256 `febe115614f020bac5e3d75d95ab4c26fc0b13bd81062b4ee1d35c8dc4137a5d`.
- `python3 -B -m unittest -v test_construction.py` — repaired suite 7/7 PASS; full stdout/stderr in `construction.normal.log`.
- `python3 -B -O -m unittest -v test_construction.py` — repaired suite 7/7 PASS; full stdout/stderr in `construction.optimized.log`.
- `python3 -B -m py_compile build_fixture.py candidate.py audit.py test_construction.py run_formal.py prepare_freeze.py` — exit 0; `construction.pycompile.log` retained.

The initial construction run was 5/7: the auditor's `change_cursor` mutation selected the valid cursor-0 row and changed nothing, so that mutation was not rejected and the overall construction gate failed. The independent row reconstruction had zero disagreements. The mutation now selects a valid positive-cursor row; subsequent normal and optimized suites both pass. This initial failure is a construction-only event; formal candidate/auditor CLI invocations remained 0/0.

## Runtime preflight
Docker Engine read-only info responded on OrbStack (Linux/aarch64, 29.4.0). Read-only `docker image inspect python:3.12-slim` failed on a containerd content blob with `operation not supported`. No image pull, container creation/start, prune, service restart, or cleanup was attempted. The preflight is preserved in `preflight.json`.

The formal code is standard-library-only, deterministic, CPU-light, and makes no network, GUI, model, or external-input calls. Because the requested image was unreadable, the proposed A01 uses one low-priority native-host process as a disclosed environment substitution. It carries no container/isolation claim; this environment substitution does not repair the OrbStack STOP or establish runtime transfer.

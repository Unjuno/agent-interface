# #2558 real Docker persistent batch

Date: 2026-09-20 Asia/Tokyo

## H/T/D/C/U

- H: the persistent app-server image-grounding route remains stable across fresh container allocations, with native target guards preserving fail-closed behavior.
- T: run fresh OrbStack allocations task-5, task-6, task-7 using the same image `sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398`; for each, use one persistent app-server process/thread with two image turns, then feed the returned plan into the container-native handle bridge.
- D: 3/3 task success; 3/3 independent effects; 3/3 visual revalidation; 3/3 release; 3/3 focus-change `SCOPE_MISMATCH` refusals with emissions delta 0; 3/3 continuation input false. Action-to-scored-effect: 166.804158ms, 149.354124ms, 150.202487ms (mean 155.453590ms). All model turns completed and returned the expected plan.
- C: `PASS_THREE_FRESH_DOCKER_PERSISTENT_BATCH_SCOPED`.
- U: finish the preregistered six-task cold/reuse/reuse/repair/reuse/reuse route. Current real persistent Docker evidence is 4 fresh allocations including task-1 from the preceding merged report; it is not yet the formal six-task route.

## Retained launch failure

An earlier orchestrator attempt for nominal tasks 2-4 pre-created the output directories, while the container harness correctly requires a fresh non-existing root. All three stopped `STOP_NO_READY` with return code 1 before fixture readiness. They are not counted as successful allocations and were not overwritten.

Provenance: Docker context `orbstack`, Docker Server 29.4.0, aarch64. Model boundary is host-local app-server; GUI and native effects are container-side.

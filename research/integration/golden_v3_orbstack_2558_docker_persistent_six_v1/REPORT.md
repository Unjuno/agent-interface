# #2558 six real Docker persistent allocations

Date: 2026-09-20 Asia/Tokyo

## H/T/D/C/U

- H: repeated fresh OrbStack allocations preserve the model-to-native-effect path when one persistent app-server process/thread performs two image turns per allocation.
- T: execute fresh container allocations task-1, task-5, task-6, task-7, task-8, task-9 with the pinned image; for each, run two `localImage` turns in one app-server process/thread, feed the returned JSON plan into the container-native handle bridge, and independently score effect, visual revalidation, release, focus invalidation, and continuation.
- D: 6/6 task success; 6/6 independent effect; 6/6 visual revalidation; 6/6 release; 6/6 focus-change `SCOPE_MISMATCH` refusal with emissions delta 0; 6/6 continuation input false. Action-to-scored-effect (ms): 146.738860, 166.804158, 149.354124, 150.202487, 156.122191, 145.919423. Mean 152.556874ms. All 12 model turns completed.
- C: `PASS_SIX_FRESH_DOCKER_PERSISTENT_MODEL_TO_EFFECT_SCOPED`.
- U: run the exact preregistered six-task semantic route `cold/reuse/reuse/repair/reuse/reuse` with its original task identities and repair admission, then compare only within that preregistration. This batch is six fresh allocations and must not be relabeled as that formal route.

## Provenance

- Docker context: `orbstack`
- Docker Server: 29.4.0
- Architecture: aarch64
- image digest: `sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398`
- GUI fixture and native effects ran inside the container; model boundary was host-local `codex app-server --stdio`.
- Previous task-2/3/4 launch failures remain immutable and are not counted.

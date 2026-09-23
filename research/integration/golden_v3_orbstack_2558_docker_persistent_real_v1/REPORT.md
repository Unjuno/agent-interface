# #2558 Docker/OrbStack persistent model-to-effect experiment

Date: 2026-09-20 Asia/Tokyo
Allocation: one fresh container allocation, task-1
Image: agent-interface-2558-orbstack:20260920
Image digest: sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398
Docker context: orbstack
Docker Server: 29.4.0
Architecture: aarch64

## H/T/D/C/U

- H: a persistent app-server thread can ground the fresh Docker/X11 observation and produce a plan that survives native handle admission and effect gates.
- T: launch a fresh Xvfb fixture inside OrbStack; capture `before.png`; use one host-local `codex app-server --stdio` process and one thread for two sequential image turns; use the second returned plan `[200,145]` and `docker2558-persistent` for the native handle bridge; independently verify effect, visual revalidation, release, focus-change refusal, and continuation.
- D: the container fixture completed. Independent effect was `{"saved":true,"text":"docker2558-persistent"}`; evaluation `task_success=true`; visual target revalidation=true; action-to-scored-effect=146.73886ms; native result completed; focus-change guard refused with `SCOPE_MISMATCH`, `input_dispatched=false`, emissions delta 0; continuation returned with no input dispatch. The two persistent model turns both completed and returned the same valid plan.
- C: `PASS_DOCKER_PERSISTENT_MODEL_TO_EFFECT_SCOPED`.
- U: repeat this exact container-integrated route across the preregistered six-task cold/reuse/reuse/repair/reuse/reuse allocation, retaining all raw artifacts and diagnosing the models-cache warning before formal comparison.

## Boundaries and failures retained

The first attempted model input used the invalid app-server variant `local_image`; the server rejected it before a model turn with expected variants including `localImage`. The corrected run used `localImage` and is the experiment reported above. This protocol failure is retained as a diagnostic, not silently discarded.

This is one fresh allocation, not yet the six-task formal golden result. The model process is host-local by design; GUI fixture and native effects ran inside the OrbStack container. No population/generalization claim is made.

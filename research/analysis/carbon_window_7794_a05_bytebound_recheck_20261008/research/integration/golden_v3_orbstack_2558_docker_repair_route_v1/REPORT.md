# #2558 Docker repair-route experiment

Date: 2026-09-20 Asia/Tokyo
Allocation: fresh OrbStack task-11
Image digest: sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398
Docker Server: 29.4.0, aarch64

## H/T/D/C/U

- H: a stale native plan is refused without input emission, after which a fresh model plan from the same persistent thread can be admitted and complete the effect.
- T: start a fresh container/Xvfb fixture; run two `localImage` turns in one persistent app-server process/thread; submit the second plan; retain the harness-generated stale-observation attempt; then verify repaired dispatch, independent effect, visual revalidation, release, focus invalidation and read-only continuation.
- D: stale attempt: status `refused`, diagnostic `STALE_OBSERVATION`, native backend emissions 0. Repaired attempt: native `completed`, independent effect `saved=true` with exact text `docker2558-repair-11`, task_success=true, visual revalidation=true, release verified, action-to-scored-effect 144.956939ms. Focus invalidation separately refused with `SCOPE_MISMATCH`, emissions delta 0; continuation input false.
- C: `PASS_DOCKER_STALE_REFUSAL_THEN_REPAIR_SCOPED`.
- U: execute the complete preregistered route with the official task identities and its cold/reuse/reuse/repair/reuse/reuse model-call accounting; this allocation proves the repair gate but is not itself the full formal six-task result.

## Retained failure

task-10 was a fresh allocation but the model returned `{"x":200,"y":145,...}` instead of the required `point:[200,145]` schema. The container stopped before result publication; it is retained as a schema-boundary failure and not counted as success. task-11 used an explicit schema instruction and completed.

# Typed semantic-grounding admission

`semantic_repair_model_v2` converts one controlled Luna-low process into one of
four explicit no-authority outcomes:

- `COMPLETED`: exactly one validated message, turn, thread and complete usage;
- `DEFERRED_UPSTREAM`: the exact capacity-unavailable refusal and no completed
  output;
- `FAILED_UPSTREAM`: another nonzero model-process result;
- `FAILED_OUTPUT`: exit0 without a valid grounding result.

It never retries. `semantic_grounding_admission_v1` then permits task mutation
only for `COMPLETED`. Capacity becomes `TASK_DEFERRED`; process and output faults
become `TASK_BLOCKED`. All receipts explicitly grant neither semantic nor input
authority. Even the eligible receipt requires ordinary Executor admission before
any side effect.

Seven focused tests pass on Windows and WSL. They replay a retained valid
Luna-low grounding and the frozen v1 capacity failure, add a malformed-success
control and reject attempted authority escalation. No new model or GUI call is
part of this construction evidence.

The next live comparison should obtain the initial grounding receipt before
entering the task token. A deferred receipt must close the session without task
mutation. A completed receipt may supply the validated target reference, after
which current pixel revalidation and ordinary input admission remain mandatory.
Availability can still disappear later; any such reacquisition refusal remains a
typed deferred outcome and cannot be counted as a comparison sample.

The frozen v2 live allocation confirmed the initial boundary under available
service, then exposed a separate freshness rule. A post-resize model call took
8,262.886ms against a3,000ms source freshness limit. Although Luna returned the
correct Save point, the handle correctly refused `STALE` before target input.
The next caller must refresh and revalidate after completed model inference; a
successful model result does not refresh its source observation.

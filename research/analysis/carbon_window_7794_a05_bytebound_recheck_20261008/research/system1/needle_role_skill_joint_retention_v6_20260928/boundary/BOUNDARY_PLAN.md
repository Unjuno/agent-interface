# Host thread-overlap boundary probe — H/T/D/C/U

## H — hypothesis

On this Windows host, two real Python threads can emit monotonic event receipts
that independently establish overlap between one feedback arrival/trainer
critical section and an individual in-flight placeholder call. This checks the
event-instrumentation boundary only; it is not evidence about inference or
optimizer performance.

## T — allocation and execution

- Allocation: `needle-host-thread-overlap-boundary-20260928-v1`.
- Additive path: `research/system1/needle_role_skill_joint_retention_v6_20260928/boundary/`.
- Main checkpoint: `6e032b99d1fd85b4a87375f3262eef5e74e96617`.
- No random seed, model, optimizer, GPU, Docker, or shared resource is used.
- One OS process starts exactly two named threads. Events order the query call,
  feedback arrival, trainer interval, and inference-call release. The raw record
  stores `perf_counter_ns` intervals, process/thread identities, environment,
  source scope, and explicit placeholder/no-optimizer labels.
- Run exactly once with:

  ```text
  python -B host_thread_overlap_probe.py thread_boundary_raw.json
  python -B audit_thread_overlap.py thread_boundary_raw.json thread_boundary_audit.json
  ```

- The independent stdlib auditor imports neither the candidate protocol nor any
  model/optimizer implementation. It checks exact cardinality, process scope,
  worker distinctness, arrival/consumption ordering, each-call interval, and
  strict interval intersection; it binds the raw file digest.

## D — decision

`PASS_HOST_THREAD_OVERLAP_INSTRUMENTATION_SCOPED` requires one valid query and
one feedback event, fresh arrival/consumption within the query, distinct worker
IDs, strict overlap with the retained individual call, zero model/optimizer/
Docker/seed use, and an independent zero-error audit. Malformed or nonoverlap
raw is `FAIL_BOUNDARY_AUDIT`; timeout or incomplete event capture is `STOP`.

## C — controls

Barriers, not sleeps or guessed timestamps, guarantee causal overlap. The
auditor reconstructs conditions from serialized monotonic timestamps; it does
not trust the probe's claimed decision. The probe refuses to overwrite output.

## U — limits

The “inference” is an event-blocked placeholder with no model call; the trainer
interval is an empty critical section with no parameter update. This proves
only that this host's two-thread event logger records a real temporal overlap.
It says nothing about PyTorch/GIL behavior, actual LoRA updates, query quality,
CUDA, Docker, deadline latency, or any formal #5081 threshold.

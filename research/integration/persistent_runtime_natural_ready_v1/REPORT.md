# Persistent runtime natural-ready gate v1 — retained result

Decision: **PASS_EXISTING_RUNTIME_READY_GATE_SCOPED**

Formal invocation: 1. Formal reruns: 0.

## Result

- `endpoint_only`: 3/3 later `clock` reads timed out; 0/3 clock boundaries.
- `runtime_ready_gate`: 3/3 reached the later `clock` boundary; 0/3 timeouts.
- Candidate ordering passed in every case: existing `ready` record with `authority=none` precedes endpoint publication; endpoint publication precedes the requested `clock`.
- Excluded readiness negatives fail closed 3/3: suppressed ready, wrong-authority ready, unrelated early record.
- Postformal corruption controls are rejected 3/3: forged ready authority, candidate status corruption, frozen source corruption.

Endpoint availability median is 464.943 ms baseline vs 1249.210 ms candidate. This is **not a speedup**: the candidate intentionally delays endpoint publication until initialization evidence exists. Candidate ready-emission→publication median is 0.561 ms; publication→clock-event median is 1.159 ms.

## Interpretation

The existing persistent entrypoint already provides a plausible natural initialization milestone. In the scoped harness, using that milestone prevents a short later read budget from being consumed by startup without introducing a new readiness event vocabulary. This is the specific successor question from #807/#812.

## Limits

The executable child/socket harness is source-derived and not byte-identical to the complete current runtime. Exact current-main inspection separately establishes the real source order `suite.prepare + Backend -> ready -> initial snapshot -> stdin loop`. Therefore this result does not prove real GUI startup behavior, general liveness, lower latency, task correctness, token reduction, or production readiness.

Next: do **not** add another readiness vocabulary. If #57 integration still needs the mechanism, test the existing `ready` boundary on one actual persistent GUI caller path with byte-pinned runtime and separately accounted startup/read timing; otherwise stop here.

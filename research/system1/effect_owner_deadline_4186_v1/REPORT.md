# Issue #4195 result

## Final disposition

**ID001:** `STOP_EXTERNAL_EXECUTION_TIMEOUT / HOLD_FORMAL_INCOMPLETE` — 20 complete rows, one started partial directory without a row, 15 unstarted. No retry/resume/pooling. Frozen prefix audit reported only `row_count:20!=36` and no complete-row semantic errors.

**ID002:** `PASS_EFFECT_OWNER_DEADLINE_SCOPED` — three prospectively frozen 12-row batches, 36/36 fresh app+sink pairs, external exits 0/0/0, raw-only audit errors=[], 12/12 corruption controls rejected, source hashes unchanged.

## Scientific result

The application-side deadline check was on time in every case. The separate sink was the only process allowed to create the O_EXCL/fsynced effect file.

- APP_CHECK_ONLY: six short effects on time; all six long effects committed late (~140.5–150.7 ms).
- SINK_POSTHOC_CHECK: six short effects on time; all six long effects committed late and were labelled LATE only after commit.
- SINK_PRECOMMIT_DEADLINE: six short effects on time; all six long writes refused before effect, with no effect file.

Effect-file `case_id`, `sink_pid` and `effect_ns` matched the sink receipt in every committed row. Authority remained false.

## H/T/D/C/U

- **H:** an application check before IPC does not establish an effect-by-deadline contract when a separate effect owner can delay commit.
- **T:** CPython3.13.5 stdlib, three policies x four schedules x three reps, CLOCK_MONOTONIC, deadline120ms/freshness400ms, one app + one sink process per case.
- **D:** ID002 rows36/errors[]; late candidate effect files0; valid candidate short effects6/6; 12/12 corruption controls reject.
- **C:** cooperative sink receives the deadline; fsync return is a fixture commit point, not power-loss durability; directed IPC/sleep timings.
- **U:** no distributed/network transaction, arbitrary GUI semantics, hard-real-time, authentication, model/task/token/latency benefit, natural rate or production promotion.

## Integration handoff

For deadlines whose semantic requirement is the **effect commit**, validating upstream app/dispatch state is insufficient across an asynchronous owner boundary. The effect owner (or a transaction that controls it) must enforce the predicate before commit. Posthoc detection is evidence of an already-occurred late effect, not prevention.

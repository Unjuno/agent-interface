# R3 repeated mixed-app guarded recovery — formal stop

Issue #1769.

## Disposition

**STOP_FORMAL_WRAPPER_NO_DURABLE_ROWS**

The exact-frozen monolithic formal invocation was started once and was terminated by the external container command timeout before `RESULT.json` was durably published. The allocation is consumed and will not be rerun.

Formal discipline: formal1 / reruns0 / replacements0 / tuning0.

## What is known

- source bundle and construction evidence were frozen and remote-read back before formal;
- the first complete excluded construction passed all R3 gates across three cycles;
- construction also descriptively exposed raw X11 window-ID reuse across non-consecutive process generations;
- during formal, temp roots for session IDs 1, 2 and 3 were created;
- `formal.stdout` and `formal.stderr` retained zero bytes and `RESULT.json` is absent;
- because the runner accumulates rows in memory and writes only after all four sessions, retained scientific rows = **0**.

The temp directories are setup/runtime residue, not a substitute result. They do not prove that any formal session completed, and no formal PASS/FAIL is inferred from their file counts.

## Failure mechanism

The scientific schedule was made longer by the preregistered 3x repetition, but result durability was still monolithic. A wrapper-level stop can therefore erase already-computed in-memory rows. This is a retention/execution-packaging defect, not evidence for or against the guarded-recovery hypothesis.

## Successor rule

Do not rerun this allocation. A successor may change exactly one factor: write each formal session as an immutable durable batch result before starting the next session, then aggregate only the four retained batches. Preserve the R3 science, cycle count, applications, task effects, gates and thresholds.

FORMAL_STOP SHA-256: `5fcb6dee792abe9473e467fa3760eac5cee9fcf99c4d5827ca7239c70617df0e`.

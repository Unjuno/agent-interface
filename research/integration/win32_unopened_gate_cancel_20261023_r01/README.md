# Cancel while the Win32 producer gate is closed — R01

The public caller can wait on a final target-generation query after registering
its child process but before opening the child's input gate. At baseline
`572b86b6b1119d537d3fac20d2e6610e7e161a4f`, cancellation during that wait
retired the child, sent a fake recovery UP, and reported recovered even though
the input gate had never opened. Frozen-baseline trace evidence records the
exit, recovery request, UP, and observer request in that order, with no producer
authorization or DOWN event.

The caller now declares `start_gate_required=True` at admission. The owner
retains `producer_gate_state=closed` until it attempts the parent-owned gate
callback. After retiring a child whose gate is still known closed, it refuses
to claim recovery, keeps UNKNOWN with
`producer_retired_without_start_authorization`, denies replay, and sends no
compensating input or readback request. The fixed trace contains only the
producer-exit confirmation. This conservative result does not claim release
or task success, and leaves same-owner admission fenced.

The gate state is set to `authorization_attempted` before invoking its callback:
a callback that opens the gate and then raises cannot be classified as never
authorized. Direct operation-owner clients that do not declare a parent gate
retain `untracked` state and the previous recovery behavior; registration alone
never proves their inputs stayed closed. Every public Win32 caller admission
requires the gate. The public API cannot override this internal requirement.

## Evidence

- `raw-red.txt` retains the initial reproduced failure.
- `reproduce_baseline.py` substitutes the frozen pre-fix owner and caller
  classes in memory, runs the final composed test, and produces the expected
  failure in `raw-baseline.txt`. `traces-baseline/` retains the unwanted UP.
- `raw-first-green.txt` records 22 focused passes on the first repair before
  the final trace recording and gate-callback-exception test were added.
- `raw-normal.txt` and `raw-optimized.txt` record the final focused plus
  MCP-owned-process/guarded-X11 compatibility runs. Commands and counts are
  in `conditions.json`; `traces-normal/` and `traces-optimized/` retain all
  composed scenarios, including the closed-gate cancellation.
- `SOURCES.json` binds canonical Git blob bytes at the final source commit.
  `SHA256SUMS` covers packet files other than itself. Earlier packets are
  unchanged; captured raw whitespace is preserved.

The reproduction uses actual spawned processes, real custody/caller code and
the real Win32 session/backend when the gate opens, but only an inert Win32
API. The new refusal case never enters that backend. Target/process identity
readers are synthetic. It does not qualify physical Windows input, native
generation fencing, recovery authority after authorized input, queued late
DOWN exclusion, a live task/MAP01 oracle, hard bounds, matched efficiency or
reliability. No WSLc allocation, Docker, or native desktop input was used.

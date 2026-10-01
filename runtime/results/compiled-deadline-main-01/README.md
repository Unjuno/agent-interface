# Compiled continuation integration and deadline boundary

The primary six-task batch composition remained efficiency HOLD: guarded input
required74 public calls versus29 for a fully batched direct route. This does not
establish a speedup. Issue57 specifically requires intermediate evidence to
select a later action. The previously live-tested compiled graph supplies that
mechanism, but was available only under research and could continue after a
blocking adapter consumed the method budget.

Move that existing graph into `runtime/core_v1/compiled_gui.py`, retain its
research entry point as an exact compatibility import, and include the shared
implementation in the committed portable archive. This is an explicit Python
API with caller-provided adapters, not a new MCP tool or an automatic controller.

Recheck the original deadline after external observation, branch journaling,
admission, effect verification and returned execution. At the exact deadline,
yield rather than dispatch another input or claim graph completion. Clamp each
executor deadline to the earlier of admission expiry and the method deadline.
Retain neutral completed transitions and pending effects when execution returns
late. Release failure and uncertain delivery keep their original failure reason.
There is no preemption of blocked I/O, physical release deadline or replay.

Validation:14 initial tests produced11 RED failures on the prior implementation,
then14 GREEN. Expanded22 focused tests passed normally and with Python -O.
They include the late initial/intermediate/final observation, late admission,
late verifier, late completed input, journal delay, deadline clamping, unchanged
normal branches, missing/stale/ambiguous/unknown input dependencies, failed or
unavailable effects, release failure, uncertain delivery and compatibility.
An isolated working-source archive test imports no research checkout and stops
before late admission. Source286cfc988's committed native checks passed366
protocol and157 harness tests. Detailed logs and result hashes are retained.

The initial full check failed because the build intentionally reads committed
HEAD, which did not contain the new runtime file yet: protocol had1 error and
harness8 errors. All were committed-source lookup failures, retained under
full-ci. After committing the implementation, committed-ci passed both suites;
no GUI allocation, scenario retry or frozen historical result was involved.

`TASK_SUCCEEDED` remains an adapter/predicate graph verdict, not an independent
application certificate. Adapters must share the clock domain and enforce the
supplied deadlines, target guards, raw persistence and effect verification.
Future live source manifests must pin both the compatibility entry and the new
shared implementation. Historical frozen source/results are not rebound.
No actual speed, model-token reduction, semantic latency or human performance
was measured here. Live adapter integration remains required before accepting
this path as a product efficiency improvement. The broader goal remains active.

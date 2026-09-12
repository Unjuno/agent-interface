# Adapter inventory against the shared runtime

Inspected reference: `interactive_v10.py` and its manifest at `7427bdd`.
Legacy transfer entrypoints inspected: `visual_tracking/async_events.py` and
`doom/session_v4.py`. This is a source inventory, not a validated port.

| Concern | Shared candidate | Legacy tracking / DOOM |
|---|---|---|
| Executor | executor_v3, absolute validity | Both import executor_v2; submit has no validity argument |
| Input ownership | dedicated input_owner_v2 connection | Both inherit session_v2 worker-owned input |
| Focus | capture samples and bound intent | Observation sequence only; no corresponding focus binding |
| Recovery | read-only observation without authority renewal | Different older execution semantics |
| Presentation | full default; explicit optional compact | First-per-step plus latest polling; tracking has pending signal map |
| Shutdown | close executor, input owner, app/session | Close executor and environment; no dedicated owner lifecycle |
| Domain operation | finite keys/text/hold and observations | Tracking adds track_red up to 30 seconds; DOOM uses ordinary key holds |

DOOM's existing real-time environment validation and asset hashes can be retained:
ASYNC_SPECTATOR, OS key input, cached-telemetry refresh outside the clock wait,
and outcome scoring after control. The adapter must update submit/deadline
handling and explicit owner lifetime, and pin the exact shared backend. Do not
silently keep the old backend while claiming common semantics. A basic-room
outcome still does not demonstrate general game skill.

Tracking requires more than changing imports. Its custom loop directly calls raw
input, has a thirty-second operation budget, and detects known visual signals in
an overridden snapshot method. It must bind authority before its custom branch,
respect lease cancellation and release, and define how the domain-specific
operation budget fits the shared contract. Its pending-signal/acknowledgement
logic cannot be discarded merely to simplify integration. This is a potential
subsystem-semantic change requiring separate evidence and a churn entry.

Priority: DOOM adapter first because its existing operations fit the shared input
vocabulary; track_red integration follows an explicit authority/event contract.
This prioritization reduces architecture uncertainty and cross-domain gaps.
No port is implemented or promoted by this note. Frozen legacy sources remain.

## Transfer update

[DOOM revision 6](../doom/SHARED_RUNTIME.md) now uses the pinned shared backend
and executor. Three scripted readiness cases and ten exact frames passed; two
failed development cohorts are retained. The table above describes the legacy
entrypoints only. Shared assistant gameplay and broader qualification remain
open; tracking still requires the explicit authority/event contract described
above. No new core semantics or performance gain is claimed.


## Pointer owner candidate — 2026-09-13

[Primitive implementation and probes](../live_control/POINTER_OWNER.md) introduce
`input_owner_v3.py` separately from the shared v10 backend. This is proposed new
core input semantics (churn), not an adapter-only change or qualified domain.
No pointer operation is admitted by the existing shared program validator yet.
Geometry binding, destruction/disconnect lifecycle and shared-app regressions
remain prerequisites to integrating it with the saved OpenTTD task.


The follow-up [v5 owner candidate](../live_control/POINTER_LIFECYCLE.md) adds
observed geometry and failure-lifecycle handling. Sixteen primitive checks and
two private-server fault injections are evidence for that component only. Shared
backend integration, snapshot binding and real-app regression remain unqualified.

The subsequent [session_v9 candidate](../live_control/POINTER_BACKEND.md) integrates
snapshot-bound pointer programs with the existing executor. One managed-window
cohort passed; three setup failures remain. [One OpenTTD self-use episode](../openttd_task/SELF_USE.md)
passed independent scoring with this shared candidate. The OpenTTD adapter uses
no custom input semantics. This is new core semantics/churn, not runtime promotion
or a qualifying freeze revision; broad/fresh regressions remain open.

[Guarded OpenTTD placement](../openttd_task/GUARDED_PLACEMENT.md) subsequently adds
a query-only surrounding-state observer and stricter independent task score.
The shared backend/executor are unchanged. A real overlong-drag replay fails the
new score and a corrected visual development episode passes; this is a task/oracle
revision, not another core-semantics change or qualifying freeze revision.

[Desktop pointer transfer](../live_control/DESKTOP_POINTER.md) adds an entrypoint
using unchanged session_v9 for existing desktop fixtures. The legacy SVG task
passes but exact-displacement checks fail in four real-app trials, including dense
paths. This is transfer/failure evidence, not core promotion or a freeze pass.

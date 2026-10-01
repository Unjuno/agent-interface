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

[Intermediate drag feedback](../live_control/DRAG_FEEDBACK.md) adds candidate core
semantics in session_v10/v11: checkpoint observations and a bounded optional delay.
This is churn. The five integration cohorts include three partial focus failures;
freshness, held-state ordering and bounded continuation remain unresolved.

[Pointer focus equivalence](../live_control/POINTER_FOCUS.md) introduces candidate
owner_v6/session_v12 after capturing a same-client child-to-parent focus stop.
Eight controlled boundary checks and three real Inkscape integration runs pass;
keyboard exact focus remains unchanged. This is another explicit core-semantic
change/churn, not qualification, precision improvement or runtime promotion.

[Historical input-state bracketing](../live_control/INPUT_STATE.md) adds candidate
owner_v7/session_v13 state samples around capture/preparation. Four race/stall
cases and eight focus regressions passed, including a held-state record delivered
after release. This is state-contract churn; bounded continuation is not implemented.

[Owner continuation admission](../live_control/CONTINUATION_ADMISSION.md) introduces
owner_v8 instance/revision matching for movement within one live hold and original
lease. Two component cohorts pass 11/12 checks. This is core churn; executor yield,
path replacement, observation freshness and actual assistant continuation remain
unimplemented and unqualified.

[Guided pointer replies](../live_control/GUIDED_POINTER.md) subsequently add
session_v14/v15, owner_v9, a one-reply mailbox and candidate interactive_v12.
This is core semantic churn: executor yield, count/age bounds and timer lifetime
through owner admission. Three known-fixture local visual-controller runs meet
±1 px displacement tolerance, with blocked-output and consumed-reply stall release
evidence. The stall retains a `failed` terminal classification. No remote-model
performance, fresh-case generality, promotion or freeze qualification is claimed.

[Planner-facing patch servo](../live_control/SERVO_INTERFACE.md) adds session_v16
and interactive_v13 with source-bound single-step local correction and needs_decision
mapping for non-goal tracking outcomes. This is explicit core operation/feedback
churn. Actual assistant use and selected-source failure mapping have narrow evidence;
cross-domain and fresh distractor gates remain open. No freeze credit.

[Live modal guard](../live_control/LIVE_MODAL_GUARD.md) adds an unpromoted private
proposal attachment and pre-input pixel/context check around an ordinary Return
step. This changes candidate control semantics, not a domain adapter alone. Known
X11 negative cases stop without owner revision change; check/input race and runtime
incarnation binding remain unresolved. No freeze credit or public ABI promotion.

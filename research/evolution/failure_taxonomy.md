# Failure taxonomy — initial register

Stable IDs below distinguish categories from individual occurrences. This is an
initial, incomplete retrospective index. Discovery counts are not yet audited.
The scoped [occurrence register](occurrences.csv) currently indexes nine observed
examples in F03/F04/F10/F14. This is not full recurrence or discovery coverage.
Do not count a proposed risk or a unit-test assertion race as a newly discovered
product failure without an explicit classification decision.

| ID | Class | Current evidence/status |
|---|---|---|
| F01 | Input delivery | Earlier DOOM binding failure; see ../doom/README.md |
| F02 | Input ownership / cleanup | Ownership checks exist; broad failure coverage incomplete |
| F03 | Lease / expiry | Worker stalls delayed key release; ../live_control/INPUT_OWNER.md |
| F04 | Wrong-target / focus | Controlled wrong-window delivery; ../live_control/FOCUS.md |
| F05 | Stale action / binding lifetime | Late cancel and old intent; ../live_control/DECISION_BOUNDARY.md |
| F06 | Observation freshness / paint | Unpainted modal observed; ../live_control/RECOVERY.md |
| F07 | Critical-event loss | Compact visual-only transient omission is an explicit open risk; ../live_control/PRESENTATION.md |
| F08 | Transport / reconstruction | Keep codec failures separate from task correctness; historical audit pending |
| F09 | Route invalidation | Historical audit pending |
| F10 | Modal transition / recovery | Focus guard prevented observe-only recovery; ../live_control/RECOVERY.md |
| F11 | Capture/context skew | Different image/window states; ../live_control/OWNER_SELF_USE.md |
| F12 | Motor control | Historical drag/tracking failures; audit pending |
| F13 | Planner-boundary delay | Multi-second planner gaps despite short local operations; handoff |
| F14 | Task specification / interpretation | Calc B1 instead of A2; ../live_control/OWNER_SELF_USE.md |

For each future occurrence record revision, trial, evidence, taxonomy ID,
observed-vs-risk status, regression relation and resolution. A new category is
counted once at its earliest verified discovery; subsequent occurrences count
as recurrences. Retrospective earliest-discovery dates remain unknown until
backfill. Category merges/splits must version the taxonomy and recompute curves.

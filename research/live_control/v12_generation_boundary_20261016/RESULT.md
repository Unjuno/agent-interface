# Current V4→V12 target-generation boundary

Disposition: **REPRODUCED_METADATA_IGNORED_AT_CURRENT_V4_V12_OWNER**.
Generation-preservation contract satisfied: **false**. This is an unmet capability
against the overall goal, not a newly advertised guarantee of the legacy API.

## Executed construction

On base `2aa662b833dd1cda7d44c02a79f9d4433bdf0867`, freeze commit
`3b6fd9dcb31e811130ac08d37336ff35597c94ae` precedes the first four-cell run.
Ten dependency hashes include actual V4/V3/V12 owner code, current cooperative
lease classes, fixture and probe. Normal Python 3.13.14 on Windows uses the
existing FakeDisplay and patched XTEST/display functions; no X connection is
opened. There is no model, WSL, container, GUI, physical input or formal allocation.

| Cell | Fixture identity vs supplied source | Fake focus | Actual result |
|---|---|---:|---|
| stable | same XID/PID/start identity | 41 | One KeyPress admitted |
| same_xid_new_pid | PID/start identity differ | 41 | One KeyPress admitted: generation contract fails |
| same_xid_pid_new_start | same PID, start identity differs | 41 | One KeyPress admitted: generation contract fails |
| changed_focus | same generation | 71 | DecisionRequired, zero KeyPress |

Each admitted cell has one KeyRelease, verified empty fake key/button state and
no remaining fake key. All four owner threads stop after explicit close.
The probe calls the actual `input_transition_owner_v4.InputOwner`, its V3 wrapper
and V12 native owner, using an actual `lease_cause_v2.Lease`. It supplies a
`target_generation` field itself. The fixture's current identity is an independent
reference value; it is not a working XRes adapter or a real process/window restart.
This confirms that the present owner ignores that metadata. It does not show
that the standard caller currently populates it or that a future platform reader
is correct. Source pipeline inspection, not this raw, establishes the caller gap.

`first-outcome.json` retains admissions, emissions, held-state snapshots, release
records and thread-exit state. The reference predicate compares the exact supplied
generation tuple plus focus. `audit.py` reads saved bytes only and never imports
an owner. Normal and optimized checks reproduce the same failure disposition;
three test methods pass in each mode and reject ten inconsistent saved claims.
Audit success validates the recorded gap, not input safety. The owner probe ran
once; optimized verification re-reads raw instead of repeating it.

## Actual caller and remaining implementation

The current MAP01 controller's measurement session selects
[`session_map01_v15.py`](../../doom/session_map01_v15.py), which replaces the base
Backend with [`doom_owner_thread_release_batch_backend_v1.py`](../../doom/doom_owner_thread_release_batch_backend_v1.py).
That backend selects V4, which wraps V12. This graph differs from the historical
V10 generation-fence candidate retained at local preservation commit
`50a863b314a3454d6b8e293d9d6523ff943c0808` (A07 failure/A08 scoped effect/A09
construction). Do not overwrite V12 with the V10 copy and lose newer release
telemetry/custody fixes.

Public guarded Python/MCP already has a different, explicitly selected
[process-identity path](../../../runtime/guarded_x11_v1/PROCESS_IDENTITY.md).
Its success cannot qualify this MAP01 owner path. Neither proves window/client
incarnation within one process or atomic X-server acceptance.

The next implementation must connect a supported trusted platform identity
reader through capture association, immutable admitted lease evidence and the
actual selected owner. Reuse XRes + process-start identity where its local-server/
PID-namespace assumptions hold. Check before each new press and define held-input
revocation; preserve original expiry, release tracking and cancellation-wake
semantics. A stalled identity reader must not newly trap the only cleanup writer.
Test this complete caller/owner path with stale/fresh/unavailable/late evidence and
held-prefix cleanup before a separately authorized live run. Sampling still leaves
an explicit server-acceptance race. Task effect, finite recovery and matched
efficiency remain separate unproved gates; #59/#17/#57 stay open.

## Read-only verification

```powershell
python research/live_control/v12_generation_boundary_20261016/audit.py
python -O research/live_control/v12_generation_boundary_20261016/audit.py
python -m unittest discover -s research/live_control/v12_generation_boundary_20261016 -p test_audit.py
python -O -m unittest discover -s research/live_control/v12_generation_boundary_20261016 -p test_audit.py
```

The probe requires an exclusive new `--output` path and verifies frozen source
hashes before fake input; ordinary later regression runs are distinct from the
retained first outcome. Raw is not silently refreshed to new main source.

Review found that the first auditor checked aggregate stale-admission count
without validating each named cell's reference axes. A corrected-axis regression
first reproduced three false accepts (`v12-generation-axis-red-first.log` in
local outputs). The auditor now checks typed identity/PID/start association,
common source, same-XID PID change, same-XID/PID start change and changed-focus
control separately. Raw and probe are unchanged; only saved-data auditing was
repaired. Initial six corruption controls and four axis controls are all retained.

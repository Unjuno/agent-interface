# Issue #4136 — active pointer grabs versus hit-target checks

Allocation: `pointer-grab-hit-target-20260922-01`

Decision: **PASS_POINTER_GRAB_BOUNDARY_SCOPED** for the declared boundary hypothesis only.

## H/T/D/C/U

- **H:** current XQueryPointer leaf can remain Entry A while another X client owns an active pointer grab; XTEST button input may be delivered to that grab owner. A temporary pre-click grab probe can detect a grab that already exists, but cannot close a later check/use interval.
- **T:** HIT_ONLY vs HIT_GRAB_PROBE; CLEAR / GRAB_BEFORE_CHECK / GRAB_AFTER_CHECK; three repetitions per policy/state, plus two NO_TASK_INPUT controls = 20 fresh cases. One source-frozen formal orchestration, no retry/replacement/tuning.
- **D:** all 20 exact rows matched the preregistered table. Raw-only auditor: 159 checks, errors=[]; 9/9 copied-evidence corruptions rejected. Supervisor/runner/app/grabber/Xvfb terminal evidence completed; all terminal X-server keys/buttons neutral.
- **C:** cooperative private-Xvfb/Tk fixture, separate owner_events=False X grabber, X server logical input. The diagnostic probe itself briefly grabs/ungrabs the pointer in eligible cases.
- **U:** passive/owner_events=True/keyboard grabs, arbitrary applications/toolkits, grab ownership identity, production target discovery, model/task utility, latency/token benefit and natural incidence remain untested.

## Formal result

| Policy / state | n | click disposition | application text | foreign grabber |
|---|---:|---|---|---|
| HIT_ONLY / CLEAR | 3 | clicked | A=`7` | 0 |
| HIT_ONLY / GRAB_BEFORE_CHECK | 3 | clicked | no text | 1 press + 1 release each |
| HIT_ONLY / GRAB_AFTER_CHECK | 3 | clicked | no text | 1 press + 1 release each |
| HIT_GRAB_PROBE / CLEAR | 3 | clicked | A=`7` | 0 |
| HIT_GRAB_PROBE / GRAB_BEFORE_CHECK | 3 | refused before click | no text | 0 |
| HIT_GRAB_PROBE / GRAB_AFTER_CHECK | 3 | clicked | no text | 1 press + 1 release each |
| NO_TASK_INPUT controls | 2 | no click | no text | 0 |

The native pointer leaf equals Entry A in all 18 scientific policy cases, including active-grab cases. In the preexisting-grab candidate cells the probe returns non-GrabSuccess and blocks the click. When the grab begins after the probe, the candidate is still vulnerable: the foreign client receives the button pair.

Post-click focus validation prevents text after the diverted click in this fixture. It does not undo the already-delivered click.

## Provenance

The first public FREEZE accidentally quoted pre-public local source hashes. Remote readback detected that mismatch while formal remained 0/20; the incorrect comment is retained. FREEZE was then corrected to bind the actual Git blobs and local SHA-256 of the published bytes before the sole formal invocation. No scientific schedule, arm, state, gate or expected outcome changed.

Full raw evidence is losslessly retained in `FORMAL_EVIDENCE.zlib.b64`. `restore_formal.py` reconstructs the 20 per-case JSON records plus rows, execution, audit and controls. See `FORMAL_MANIFEST.json` for all identities.

This is research evidence only. It does not modify shared runtime/defaults or close #4084, #2789, or the global ROADMAP.

# R36–R39 public-relay blocked-stdout recovery series

These one-shot Windows synthetic-fixture attempts test the standard `interface_cancel` route through the public stdio relay. Raw output remains local-only under each packet's ignored `run/` directory. No existing GZDoom window was targeted. No WSLc or Docker operation occurred.

| Attempt | Classification | Result |
| --- | --- | --- |
| R36 | `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` | Input-free stop: fixture did not become foreground; same-generation key-state witness unavailable. Its post-hoc pretrial hash check notes that the audit script was changed after execution. |
| R37 | `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` | Input-free stop: selecting the exact HWND with CUA did not raise it; foreground remained elsewhere. Preregistered and raw hashes passed 8/8 and 5/5. |
| R38 | `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` | CUA Raise worked. Recovery and same-generation SHIFT-up were observed while output remained blocked, but coarse monotonic timestamps tied recovery to output resume. The relay call-count audit was off by one, and the second fixture was not foregrounded, so task effect was not attempted. Integrity passed 8/8 frozen and 17/17 raw hashes. |
| R39 | `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` | Scoped recovery and task gates passed. High-resolution timestamps place recovery and independent same-generation SHIFT-up before stdout resumed; `interface_cancel` overtook queued request 17; stale generation was refused; one fresh-generation compiled action produced the exact fixture effect and independent task oracle success, with neutral input and clean fixture exit. Full attempt remains FAIL because original foreground restoration was not observed (`foreground_before_restore=0`, `foreground_after_restore=0`). R39 integrity passed 8/8 frozen and 38/38 raw hashes. |

R39's independent follow-up audit is [`audit_followup.json`](audit_followup.json). The successful scoped gates demonstrate this one relay composition only; stdout was an in-process blocked writer, not a saturated OS pipe. This is not a live production-app, MAP01, WSLc, efficiency, or reliability result. The exact R39 runner and conditions are frozen in its preregistration and source hashes; R36–R39 raw packets remain on the local host.

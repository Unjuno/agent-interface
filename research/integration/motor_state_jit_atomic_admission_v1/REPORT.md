# MotorState JIT atomic-admission boundary v1 — #4266

Disposition: **PASS_MOTOR_STATE_JIT_ADMISSION_RACE_SCOPED**.

## Result

One prospectively frozen 16-case allocation ran as four immutable four-case batches. Formal reruns/replacements/post-result tuning: 0/0/0.

| schedule | JIT_THEN_SEND | ORDERED_ADMISSION |
|---|---|---|
| STABLE | Calc A1=7, helper empty (2/2) | Calc A1=7, helper empty (2/2) |
| TRANSFER_BEFORE_CHECK | refuse before input (2/2) | refuse before input (2/2) |
| TRANSFER_AFTER_CHECK_BEFORE_INPUT | wrong-surface helper=7, Calc blank (2/2) | Calc A1=7, helper empty (2/2) |
| OBSERVER_UNAVAILABLE | refuse before input (2/2) | refuse before input (2/2) |

All 16 cases independently observed the held Shift state and its release, ended with Shift/7/Return neutral, retained four child-process exit receipts and authority=none. Candidate wrong-surface effects: 0.

The candidate uses a deliberately narrow X11 ordering section: `XGrabServer -> current-focus validation -> first XTEST task-key publication -> XUngrabServer`. In the directed race, the foreign helper's separate-client focus request remains pending until ungrab. The weak comparator allows that focus transfer before sending the key.

Candidate critical-section duration, diagnostic only: 6 observations, min 224,307 ns, median 310,707 ns, max 375,163 ns.

Frozen independent audit reconstructs 16/16 with errors=[]; 12/12 copied-evidence corruption controls reject.

## Scope

This is a directed X11/Calc boundary, not a production recommendation. XGrabServer blocks unrelated clients and its liveness cost is unqualified. The result does not establish OS-global atomicity, physical HID routing, toolkit-general behavior, natural race incidence, model/planner usefulness, token/screenshot savings, cross-platform reliability or product readiness.

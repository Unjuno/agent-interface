# Issue #2918 transfer study roadmap

This roadmap is specific to the posted live-certificate transfer idea; it does
not replace the repository's higher-level integration/release roadmap.

| Stage | Evidence question | Status |
|---|---|---|
| R0 | Does the unchanged #1904 state-conditioned compiler behave correctly at the public observation boundary in its isolated X11 fixture, with fail-open controls? | Scoped PASS, allocation 05 is already retained on main. |
| R1 | Does the same bounded transfer survive a second, real X11 application surface (XCalc), with visible-value extraction, independent semantic scoring, stale/partial/identity controls, and XID reuse? | Formal-01 is preregistered; execution/audit disposition is to be recorded in `FORMAL_RESULT.json`. |
| R2 | Does it hold on a held-out application/workflow with independently observed post-action effects? | Open; R1 cannot close this. |
| R3 | Do safe suppressions improve end-to-end agent time/cost after extraction and fallback cost? | Open; R1 reports local capture/decode timing only. |
| R4 | Does the evidence justify integration beyond a bounded research adapter? | Open; no runtime/product promotion is authorized by R1. |

Each formal allocation is additive and immutable. A failure or stop becomes
part of the record; it is not repaired in place or recast as a pass.

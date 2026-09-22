# #4148 click-focus edit-context boundary — frozen plan

Allocation: `click-focus-edit-context-20260922-01`.

H: ordinary click-to-focus can alter insertion/selection before task text. Exact post-click edit-context validation should prevent text under changed context but does not erase click-induced edit-state effects. A fresh app-provided insertion-index coordinate should preserve no-selection insertion points in this fixture.

T: private Xvfb/Tk/XTEST; 3 policies x 4 edit states x 2 repetitions =24 plus 2 no-task-input controls. Three immutable batches 9/9/8. Formal cases are fresh processes. Construction-01/02 stopped before input on Xauthority setup; construction-03 exposed unusable unfocused Entry bbox; construction-04/05 validated the corrected prefix-font-measure coordinate and are excluded.

D: see Issue #4148 and EXPECTED.json SHA in FREEZE.json. PASS requires exact 26-row accounting, 12 center-click edit-context mutations, 6 unguarded wrong-text outcomes, 6 center-guard refusals, 6 index-guard typed positives, 2 selection refusals, 2 no-input preserved controls, all neutral terminal input, all exits0, independent raw audit error0, and >=8 evidence mutations rejected.

C: cooperative Tk Entry, exact app receipt/bbox-derived coordinate, fixed ASCII; no atomicity or general toolkit claim.

U: disabled/read-only widgets, IME/layout, grabs/overlays, concurrent writers, model usefulness, performance and production remain open.

No formal retry/replacement/exclusion/tuning after the freeze. Any wrapper/publication incident stays under #4148 and never changes consumed science.

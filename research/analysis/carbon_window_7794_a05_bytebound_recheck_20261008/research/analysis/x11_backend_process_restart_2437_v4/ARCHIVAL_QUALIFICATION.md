# Allocation 04 archival qualification

This directory preserves the original preparation package from source branch
`research/2437-backend-restart-multicontrol-v4-20261001`, tip
`ea192babc76257a03899ac346e5602bfe2b14d35`. The original `FREEZE.md`,
`experiment.py`, `preflight.py`, and `test_audit.py` are retained without
editing. `REPORT.md` and this qualification are separate archival additions.

The freeze labels Allocation 04 as preregistered and explicitly says the formal
candidate was not invoked. There is no formal raw output or audit receipt in
this package. Its simultaneous F8 + Button1 stale-request hypothesis therefore
has no experimental PASS or FAIL. Allocations 01, 02, 03, and 05 remain
separate records; do not pool this preparation with the scoped Allocation 03
failure in PR #5618 or the Allocation 05 pre-invocation STOP in PR #5623.

Local validation for this archive ran only the 11 synthetic
`AuditorConstructionTests` in `test_audit.py` (11/11 passed). These tests
exercise fabricated records and pure classification helpers; they are not the
frozen experiment, X11 preflight, Xvfb, GUI, input, formal candidate, or raw-only
auditor. No Docker/Obstac slot was available or used. No experimental claim is
promoted and no formal allocation is resumed or repeated.

# Current publication status — Issue #4237

This recovery preserves the exact frozen source package and its plan. It does
not reinterpret the Issue-reported result or rerun the consumed allocation.

## Recovered and checked

The original branch contained `FREEZE.json`, `PLAN.md`,
`SOURCE_MANIFEST.json`, and `SOURCE.tar.xz`. The source archive SHA-256 and
all seven member byte counts and SHA-256 values match the manifest. The four
Python members pass syntax compilation in an isolated scratch directory.
These checks establish byte integrity and syntax only; they do not reproduce
the Calc/X11 allocation or audit its formal outcomes.

## Missing formal evidence and disposition

Issue #4237 reports `PASS_MOTOR_STATE_FRESHNESS_TOCTOU_SCOPED` for 18 cases,
but its 720-file postformal archive, raw outcomes, process receipts, and
formal audit/control outputs are absent from the branch, current `main`, and
the checked Actions artifacts. Therefore the PASS remains an Issue-reported
historical result, not independently verified repository evidence.

Publication status is **HOLD_POSTFORMAL_RAW_UNAVAILABLE**. No formal case or
formal audit was rerun, and no missing archive was synthesized. This scoped
X11/Calc study does not establish atomic check/use safety, physical HID
telemetry, production freshness policy, or cross-platform behavior. Issue
#4237 remains open for exact postformal-byte recovery or a separately frozen
successor addressing the residual check/use race.

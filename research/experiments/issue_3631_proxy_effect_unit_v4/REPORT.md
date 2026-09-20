# Issue #3631 formal-04 report

## Status before allocation

Formal allocation has not yet been invoked. Therefore no formal PASS, FAIL, HOLD, or STOP is claimed. The result and auditor records will be appended only after the single frozen run.

## Construction evidence

- Pinned OrbStack image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64.
- Six unit/construction tests passed in the pinned container.
- Disposable GTK/Xvfb smoke passed: XRes LocalClientPID equaled fixture PID 10; screenshot-derived and structured coordinates both resolved to `[236, 88]`; click caused one fixture effect; root-window Button1 was up afterward. This smoke is excluded from the formal 28 rows.
- Earlier unit-test launch omitted the read-only launcher mount and errored while opening `/formal_launch.sh`. No formal runner was invoked; the mount was added and the suite then passed.
- Earlier working-draft metadata contained predecessor allocation IDs and is corrected before freeze.

Construction evidence is not formal evidence and makes no comparative performance claim.

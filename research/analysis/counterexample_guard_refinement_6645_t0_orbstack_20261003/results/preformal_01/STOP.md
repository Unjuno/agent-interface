# A01 construction STOP

Allocation `CGREF-6645-T0-ORB-20261003-01` stopped before any formal candidate
or auditor process. The frozen construction command exited 1: 11/13 tests
passed. The two failures were a canonical ordering mismatch between candidate
minimum-guard enumeration and the test/auditor's expected list; they do not
indicate a semantic false admission. The observed image interpreter was Python
3.12.14, while `FREEZE.json` mistakenly recorded 3.12.11. The full exact command,
failure names, frozen hashes, and disposition are in `STOP.json`.

This is a retained pre-formal construction/environment STOP, not an H_PASS or
H_FAIL. No formal result exists for A01. Its frozen sources remain unchanged.

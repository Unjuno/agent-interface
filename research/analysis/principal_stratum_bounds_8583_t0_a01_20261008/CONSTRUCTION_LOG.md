# Construction log — Issue #8583 T0 A01

- Implemented test-first; observed the expected RED condition before candidate and oracle existed.
- Fixed a construction defect where a generator was consumed while building the candidate's legal unit types; materialized the tiny outcome-pair domains.
- Corrected a test assertion to match the auditor's result field name.
- Extended pre-freeze hostile-input coverage to sealed truth, fixture digest, and success-count-versus-zero-demand inconsistencies. An initial test edit changed a valid positive-demand success count; the fixture target was corrected to the zero-demand case before formal freeze.
- Normal WSLc/Python 3.12.14 test suite: 2 tests passed.
- Optimized (`python -O`) WSLc/Python 3.12.14 test suite: 2 tests passed.
- Both suites include exact fixture assertions and five negative audit mutations. These are construction checks, not formal allocation outcomes.
- WSLc `xvfb-run` issue from an unrelated prior GUI experiment is not applicable here; this allocation is headless CPU-only.

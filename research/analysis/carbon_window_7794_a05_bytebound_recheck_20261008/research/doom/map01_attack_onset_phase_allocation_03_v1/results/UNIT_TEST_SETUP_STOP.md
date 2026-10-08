# Preformal test setup STOP (no tests executed)

The first Docker unit-test command stopped in `setUpClass` because the frozen v12 test harness expects the optional `input_owner_v10.py` comparison fixture beside `input_owner_v12.py`. The allocation's `dependencies/v12/` directory correctly contains only the files declared in its source manifest and does not include that separate comparator. The failure occurred before any test method: `Ran 0 tests`, `FAILED (errors=1)`.

A second setup attempt supplied the exact v10 comparator and then stopped on its frozen import dependency `executor_v3`; no test method ran in that attempt either. The comparison-only `executor_v3.py` and `lease.py` are now separately retained in `test-support/`, each from the same base commit and with Git blob/SHA-256/byte identities in `SOURCE_MAP.json`.

No source under `dependencies/v12/` or the frozen experiment runner was edited. The exact comparator was recovered from commit `3c34e3cea2a39e961e097b41444ff4a7563a4170`, verified as Git blob `341b3c01649943ddaad5f28431a792c4889cc36e` and SHA-256 `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b`, then staged separately in `test-support/`. A fresh isolated test invocation uses a temporary test-only overlay; the runtime source remains unchanged.

These are test-fixture setup records only. The corrected test-only overlay then completed the frozen v12 suite 10/10; see `UNIT_TEST_RESULT.json` and `UNIT_TESTS.log`. Formal invocations: 0. Game/session launches: 0. Physical inputs: 0.

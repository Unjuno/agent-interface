# Current-main Calc composition run — first fixture outcome

Source base `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`; cached image ID and all 23 source pins are in `conditions.json` and `source_sha256.json`. Network was disabled, source read-only, 2 CPUs, 4 GiB memory plus 4 GiB total memory+swap, 256 PIDs, init enabled.

The selected 214-test suite was run in normal and optimized Python. Both runs had one failure: `test_parent_custodied_calc_launch_is_opt_in_and_gates_profile` supplied aliases without mint provenance, so the new public MCP guard correctly returned `CALC_BINDING_NOT_MINTED_FOR_REVIEWED_SOURCE` before operation/input. The other 213 tests passed in each mode. Full logs and nonzero exit are retained here. This is a test-fixture contract mismatch, not evidence that the runtime guard is wrong.

The fixture correction and successor runs are retained in the adjacent follow-up packets; this first outcome is unchanged.

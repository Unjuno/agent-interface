# PR #10303 current-main reconciliation candidate (2026-11-15)

Candidate branch: `candidate/pr10303-current-main-reconcile-20261115`; tested code HEAD: `f34c43c18f0d52f18a1a390b319eff3b472c0888`; base `origin/main`: `f0d5fa202de83f39012bf4a914369b21f8e98a41`. The candidate includes the original PR #10303 G10 work merged locally onto current main plus subsequent recovery-query/caller integration and contract tests. Original PR head `321ff571e8e9f43599974f9f6b8dec716262fdfc` is an ancestor of the candidate; updating its branch can be a normal fast-forward.

## Local verification on Windows / CPython 3.11.9

Independent suites were run normally and under `-O`; these counts are not a single combined-suite result:

- `runtime.cli_v1.test_mcp_supervised_win32`: 51/51 each mode. Source/test packet: [Win32 recovery candidate](../win32_delayed_down_readback_candidate_20261115/README.md).
- `runtime.guarded_win32_v1.test_process_cancellation`: 31/31 each mode. Same packet.
- Six G10/compiled-X11 suites (`test_compiled`, `test_calc_g10_action_custody_composition`, `test_calc_g10_artifact_v1`, `test_calc_g10_formula_effect_v1`, `test_calc_launcher_v1`, `test_calc_task_artifact_v1`): 113/113 each mode.
- `runtime.guarded_x11_v1.test_compiled_native_dependencies`: 12/12 each mode.
- `runtime.cli_v1.test_mcp_owned_process` plus `runtime.core_v1.test_compiled_gui`, `test_compiled_gui_journal_exception`, and `test_compiled_gui_effect_verifier_exception`: 112/112 each mode.

The last pair's raw logs are `../calc_g10_pre_dispatch_action_receipt_candidate_20261115/final-candidate-public-owned-core-gui-normal-20261115.log` (SHA-256 `DEF072169ACC9C8CA1DCB41DEB2A351EF5B6E9B89D79EDD6238F43CE14E28B3E`) and `final-candidate-public-owned-core-gui-optimized-20261115.log` (`784CDDB12268BFF26E0D0FCC152106002A2329AD49C0F4D12FB1E1E62FA34457`). G10 and X11 dependency raw logs/hashes are in that packet.

Source hashes: `runtime/cli_v1/test_mcp_owned_process.py` `FB476889341819BB2B71DC3B02B1F15238A9D7CC069DCE8DDEFBDAB7043B9730`; `runtime/core_v1/compiled_gui.py` `8899C20A359F4D1F79B5657C2B50B31715AEB5D865F28B2F33BE87D8107E2E58`; Win32 MCP test `6DF44B738033F3A2C86E51B6D872230D821C976F26AE283B5D697A75730D365E`; cancellation source `6F953B9070F9E07E3FAD4B775059F1CCE91C17E4EC60A78D6B9694EB0577FD45`; X11 compiled adapter `10AB04D437B99F9685C49F6D3FC2BCD1C1ABB412112B18A5DBC73070E4A56FF6`; G10 artifact `B6556DBBDE886E69CE8E00365976AC1B353035A20947589C96B448FFE6FDA893`.

`git diff --check origin/main...HEAD` passes. These are offline/fake/fixture and lifecycle-contract tests. No live Calc result, new MAP01 operation/release, or #57 matched token/latency/economics claim is made. R269 custody remained unresolved at revision 888 at the last read-only refresh; the existing GZDoom screen was occluded by another app, and no input/recovery was attempted.

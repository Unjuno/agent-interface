# GZDoom idle-control preflight attempts R61–R62

**Date:** 2026-10-27  
**Source:** `12930ac63a6030ec42e66372f5224a5e95cca2b1`  
**Classification:** both attempts stopped before public observation; no idle-control measurement.

R61 stopped before opening a capture because `wait_cua_window_receipt()` had already written `computer-use-gate-accepted.json`, and the runner tried to create that exclusive file again. No input or public observation was issued. The exact fresh target exited 0 during exception cleanup; the six preserved GZDoom processes remained. Its post-hoc record is in the task-local R61 packet.

R62 corrected the duplicate receipt write and launched a fresh process (PID 59420, HWND 9637840, creation time `134375381696300063`). Win32 enumeration found exactly one visible MAP01 window, and the process remained responsive. Fresh Computer Use `list_apps()` and `list_windows()` results omitted that owned HWND while returning three older GZDoom windows. The required exact-window visual receipt therefore timed out before any public observation or input. Runner cleanup posted `WM_CLOSE` to only the exact owned HWND; that process exited 0 without forced termination. The six protected PIDs (6696, 21660, 45344, 48228, 60320, 63528) remained.

R62 raw manifest: 14 entries, all hashes verified. The task-local packet is `private-packets/map01_native_windows_20261027_r62_compiled_idle_control/`; its trial reconciliation is `trials/r62_compiled_idle_control_live_map01/posthoc-reconciliation.json`. R61 raw and reconciliation remain in `private-packets/map01_native_windows_20261027_r61_compiled_idle_control/`.

**Next:** diagnose why Computer Use enumeration excludes a newly spawned, visible owned process. Do not bypass the exact-window observation gate, select an older same-title window, or treat either attempt as an idle baseline. Retry only after the CUA-returned unique-window path is demonstrated. No WSLc, Docker, model/provider call, input dispatch, public observation, task effect, MAP01 completion, or efficiency comparison was established.

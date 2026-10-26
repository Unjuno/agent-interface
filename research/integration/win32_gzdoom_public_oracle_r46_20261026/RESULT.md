# GZDoom public task-effect oracle integration and R49–R50 idle control

## Result

R48 completed one fresh GZDoom Freedoom MAP01 action through the supervised Win32 standard caller and the public `interface_verify_task` route. The server-configured oracle accepted a correctly formatted 32-character lowercase hexadecimal oracle ID, verified the exact action identity and release, recaptured the configured target directly through `Win32Backend`, confirmed the target generation and geometry before and after that capture, and returned a receipt bound to the call, operation and generation. The public API returned `status=verified` and `task_success=true`.

The claim is limited to a visible W-forward effect, not MAP01 completion. The oracle compared a public pre-action `screen_physical_px` observation with its own post-action capture. In the fixed upper 80% region, 996,339 of 1,003,200 pixels changed (99.3161%), above the preregistered strict 5% threshold. Dispatch completed once; `input_dispatched=true`; the runtime release receipt was verified; independent same-generation readback reported W up; and the fresh target exited with code 0 after exact-HWND WM_CLOSE.

## Attempt history

- **R46:** stopped before input. The server wrapper was imported by Windows multiprocessing spawn without a `__main__` guard, causing helper startup failure. The exact fresh process exited by WM_CLOSE with code 0. The frozen source hashes matched the executed files. No dispatch occurred.
- **R47:** the spawn-safe wrapper successfully dispatched one action and its independent visual measurement passed (99.2295% changed pixels). The public task oracle rejected the result because its `oracle_id` had a prefix and was not exactly 32 lowercase hexadecimal characters. Public `task_success` remains UNKNOWN for R47. The exact fresh process was generation-checked, W-up confirmed, and WM_CLOSE’d with exit code 0. No replay occurred.
- **R48:** fixed the oracle ID format before launch and removed the pending-cancel branch; a still-pending action after bounded read-only polling now remains UNKNOWN without cancellation or replay. The public task oracle accepted the receipt and verified visible task effect.

R47 and R48 are separate attempts with fresh GZDoom generations. Their results are immutable and not pooled into a reliability estimate. R42 remains one valid no-input control; this is not a matched reliability or efficiency comparison. R48 used no WSLc, Docker, or provider calls. Its local packet contains 65 manifest entries with zero hash mismatches; raw evidence remains local-only.

## Matched-duration no-input control (R49–R50)

R49 stopped before observation because the CUA receipt writer used `window_title`, while the runner contract requires `title`. The screenshot had visually confirmed the exact fresh PID/HWND on MAP01; no keyboard or mouse input was sent. The target exited by WM_CLOSE with code 0. No baseline/post pair exists, so R49 is excluded from pixel analysis. The receipt schema mismatch was corrected and syntax-checked before the distinct R50 launch.

R50 completed the preregistered 13.234-second no-input control in 13.281 seconds between capture starts, using a fresh target generation. It recorded 300/1,003,200 changed pixels (0.0299043%) in the upper 80%, with zero input dispatches, all keys up, and identical generation before and after. The exact fresh process exited by WM_CLOSE with code 0; the three protected UNKNOWN generations were still alive and untouched. R50's packet manifest has 34 entries. The duplicate R49 files copied into R50's working packet are excluded from R50's raw manifest and analysis.

Descriptively, R48's action interval changed 99.3161% of the same region while R50's matched-duration idle interval changed 0.0299%. This single action/control pair supports visible movement as an action-associated effect on this fixture; it is not a reliability estimate, full MAP01 success, general causal guarantee, latency bound, or efficiency comparison. R49 and R50 used no WSLc, Docker, or provider calls.

## Timing and remaining boundary

R48's public baseline capture began 13.234 s before the server oracle's independent post-capture began. The oracle's own capture took 31 ms; the accepted task-effect receipt arrived 453 ms after that capture began. These are descriptive single-run timings, not a latency bound or comparative efficiency result.

No task completion oracle for finishing MAP01 was exercised. No reliability estimate, bounded blocked-I/O recovery result, WSLc result, or matched efficiency advantage follows. The R45 visual result and the R48 success both establish visible movement effect only.

## Evidence locations

Private raw packets: `private-packets/map01_native_windows_20261026_r46_public_oracle/`, `..._r47_spawn_safe_oracle/`, `..._r48_oracle_receipt/`, `..._r49_idle_control/`, and `..._r50_idle_control/`. R46, R47, R48, and R50 manifests contain 84, 62, 65, and 34 entries respectively. R49 contains a pre-input stop and schema diagnosis, not pixel observations. R50 manifest includes only R50-specific records; copied R49 files are excluded.

# WSLc standard-caller R28–R30 deadline boundary

R28 used current-main source `058ab3c` and a 2,900 ms private-Xvfb pause. Supervisor release/readback completed 35.908 ms before its 3,000 ms transaction deadline, and independent readback, late-event horizon, and old/fresh task oracles passed.

R29 held source and caller conditions constant and raised the pause to 2,950 ms. Xvfb resumed 101.597 ms before the 3 s deadline, but the release worker returned `unknown`; its completion receipt arrived 2.765 ms after deadline. The standard-caller test failed its disconnect assertion. Final cleanup observed all keys up, but independent release/task oracles were not reached. The forensic audit passed 24/24 and preserved the failure.

Commit `aaa4fce67440fcd475e71e3134345f5649336f39` increases the internal transaction budget from 3 to 4 s while leaving the public response budget unchanged, and adds a Fake X regression that failed before the change when a release worker completed at 3.2 s. Local Linux CPython 3.12.3 passed that regression and the blocked-worker UNKNOWN test in normal and optimized modes. The full 74-test MCP/owned-process run also retained environment failures: missing `runtime/backends/quartz_v1/__init__.py`, child Python missing the injected `mcp` dependency path, and two slow release-worker tests exceeding their 1.5 s worker supervision budget under the Windows-mounted WSL test environment.

R30 used the same 2,950 ms pause as R29 against the 4 s source. Supervisor release/readback completed 3,004.616 ms after admission, leaving 995.384 ms; independent key-up readback arrived at +3,164.535 ms. The +8,502.357 ms horizon saw no delayed `b`; old and fresh task oracles passed. Audit passed 33/33. Runtime cancellation remains UNKNOWN/no-replay. This is one patched-source synthetic-Xvfb sample and does not establish a generally safe outage duration, Win32/MAP01 transfer, production task success, efficiency, or reliability.

See [R28](wslc_standard_caller_xvfb_20261025_r28/RESULT.md), [R29](wslc_standard_caller_xvfb_20261025_r29/RESULT.md), and [R30](wslc_standard_caller_xvfb_20261025_r30/RESULT.md), each with its audit and retained raw.

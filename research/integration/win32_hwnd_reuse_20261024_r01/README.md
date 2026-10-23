# Native Win32 HWND reuse batch R01 pre-entry failure

The frozen R01 probe did not enter the experiment. Its setup omitted the
`advapi32` module required by `Win32Backend._configure_api()` and stopped before
the first `CreateWindowExW` call. The failure record confirms zero HWNDs were
created, no window was activated, and no input was sent. It is retained as a
setup failure and was not retried under the R01 attempt ID.

The corrected experiment was assigned the separate R02 attempt ID and is
preserved in the sibling [`r02 packet`](../win32_hwnd_reuse_20261024_r02/README.md).

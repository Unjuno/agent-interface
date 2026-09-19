# A1 formal stop

Task `SAFETY-WATCHDOG-RECEIPT-RECOVERY-20260917-001`, Issue #827.

Disposition: **STOPPED_FORMAL_HARNESS_OUTPUT_FRAMING**.

A1 formal block was invoked once. Fresh ID `f01` began and produced an app-observed F8 press/release but no `result.json`; IDs `f02..f08` never started. `f01` is consumed and will not be rerun or pooled.

Read-only diagnosis using a distinct nonformal ID found watchdog rc=0 and a valid cleanup JSON line, preceded on stdout by `Xlib.xauth: warning, no xauthority details available`. Frozen A1 `json.loads(wd_out.strip())` therefore failed on the two-line payload. Scientific arm behavior was not classified.

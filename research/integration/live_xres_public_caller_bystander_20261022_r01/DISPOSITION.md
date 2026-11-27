# R01 disposition

**Status: `NOT_RUN_PREFLIGHT_ERROR`.** The wrapper started private Xvfb :178 and completed basic display connection preflight, then exited 1 while formatting the python-xlib version banner because its version value was a tuple. The standard MCP caller, input owner, bystander, and cancellation worker were never started. No experiment input was emitted. The exact wrapper error, Xvfb log/PID, and cleanup receipt are retained in [`raw/r01/`](raw/r01/); the private server cleanup record says `xvfb_alive_after_cleanup=false`.

This is a preserved harness setup failure and is not a negative or positive caller result. No rerun was made under R01. The independent one-shot candidate is separately frozen as [R02](../live_xres_public_caller_bystander_20261022_r02/README.md), with a corrected tuple-safe version banner and a separate display/raw directory.

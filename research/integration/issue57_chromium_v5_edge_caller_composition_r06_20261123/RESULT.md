# R06 result — STOP_SETUP_PROTOCOL_PATH

The unittest setup failed before running tests because the evidence-root
directory was nested one level deeper than the runner's frozen protocol lookup
expects. It attempted to read `raw/PROTOCOL.md`, which does not exist. The
runner reports `Ran 0 tests`; Edge was not launched and no task or input
allocation was consumed. The completion-predicate change was frozen but not
evaluated. This is a setup failure, not a product pass or product failure.

Raw wrapper output and exit code are retained in [`raw/normal/`](raw/normal/).
R07 will use a separate output root at the expected depth. R06's source and
protocol remain unchanged.

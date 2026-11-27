# Win32 public task-oracle startup R01

**Disposition: `FAIL_OR_UNKNOWN`; no input was issued.** The first harness
invocation stopped at `RUN.mkdir` because the packet already contained an empty
run directory. The preflight record confirms that no fixture or server was
started in that invocation. A second invocation was made under the same frozen
conditions after correcting that harness-only directory check; it created one
fixture, but the server failed during Windows multiprocessing bootstrap before
MCP initialization. The fixture emitted only its `ready` event, then exited
with code 0. The original foreground window was restored. Public observation,
dispatch, and task verification were never reached.

The second invocation's protocol result, fixture event, preflight failure, and
frozen conditions are retained under `run/`. The multiprocessing traceback was
reported by the MCP child to the parent tool output but was not separately
captured to a file. The bootstrap fix is in the separate R02 harness; R01 is not
rewritten or retried.

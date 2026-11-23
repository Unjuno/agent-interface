# R43 pre-live qualification addendum 01

The five-trial R43 conditions and runtime source remain frozen and no trial has started. The first handshake attempt exposed two setup-only defects in the copied smoke input:

1. R01 normal and `-O` could not open the three static preflight files. The MCP child exited before initialization; its tracebacks are retained in `raw/taskserver-handshake-{normal,optimized}/failure.json`.
2. R02 supplied an empty native-ID mapping (`fresh: 0`), which current-main `create_server` correctly rejects before serving. The attempted configuration is retained as `raw/preflight-targets-r02-null.json`; the normal and optimized exception traces are retained in `raw/taskserver-handshake-r02-{normal,optimized}/failure.json`.

Both were setup-only: the smoke script only initializes MCP and lists tools; it sends no observation, dispatch, or task verification. There was no fixture window, computer input, provider call, or custody-fence transition.

R03 replaced the placeholder with positive sentinel ID `2147483647` (no native window was opened or addressed), and supplied empty state/event fixtures. A distinct wrapper writes to new output directories so R01/R02 remain intact. Normal and `-O` both initialized the current-main task-oracle server, listed 12 tools including `interface_verify_task`, and recorded zero observations and zero dispatches; each process exited 0. These results satisfy the frozen startup precondition only. They do not count as any of the five native action trials.

This addendum adds hashes for its input files and wrapper scripts to `FREEZE.json` before any live trial. R43's trial conditions, allocation, order, thresholds, and source runtime tree are unchanged.
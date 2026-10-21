# r03 duplicate-cancel confirmation

The targeted healthy public-MCP supervisor case passed in normal Python (2.030
s) and optimized Python (2.058 s). A duplicate cancel after the first operation
returned reuses the original operation ID and retained cancellation record.
The independent Fake X oracle records exactly one `KeyRelease` and keys-up
state. Runtime release remains `UNKNOWN`, `release_confirmed=false`,
`task_success=null`, and replay denied.

Frozen conditions, source hashes, sanitized trial receipt, raw test logs and
exit codes are retained in this directory. This is a local Fake X construction
check, not live X11 behavior.

# R30 result — recovery verified; follow-up server did not start

**Disposition: `STOP_TASK_SERVER_ARGV_ERROR_AFTER_RECOVERY`.** The frozen
allocation was consumed; it must not be rerun.

On current main `87b5b459a56c636934947a2fc7616f26150e8b9a`, the public source A
dispatch returned `UNKNOWN`, `task_success=null`, `release_confirmed=false`,
and `replay_allowed=false`. The fresh public orphan recovery then returned
`recovered`, confirmed release and neutral state, and verified the 2 s late
input horizon over 77 samples. The old action remained UNKNOWN. The fixture
recorded the scheduled `a` as a factual delayed effect; it is not eligible
success for the old action.

The corrected R30 foreground gate passed twice with exact HWND/PID/title, and
the fixture was at state `a`. The separate follow-up task server failed to
initialize because the runner supplied `python.exe` both as the subprocess
command and as its first script argument. The Python interpreter therefore
parsed its own executable as source and exited with a non-UTF-8 syntax error.
This happened before a fresh task observation, any follow-up dispatch, or task
verification. No B effect is claimed.

The durable fence was clear after the successful recovery. The fixture process
was intentionally left open for diagnosis under the frozen stop rule; do not
send it further input or close it as part of R30. Raw source/recovery receipts,
exception, foreground records, state and fence snapshot are retained. No
provider/model, efficiency, MAP01, preview, or reliability claim is made.

A corrected command invocation requires a separate allocation. R30 cannot be
retried or retroactively scored.

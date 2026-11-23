# R36 result — native foreground mismatch stopped before MCP

**Disposition: `STOP_NATIVE_FOREGROUND_MISMATCH_BEFORE_MCP`.** The single allocation is consumed; no retry was made.

Computer Use AX showed the R36 source title focused after Raise. The independent native probe nevertheless saw the old R35 window as `GetForegroundWindow` (HWND 16585130/PID 47620), while the expected R36 window was HWND 40570978/PID 21192. The strict HWND/PID/title foreground gate stopped the run. No public MCP observation, dispatch, recovery, or task verification occurred; the durable custody fence was clear. The R36 fixture is preserved under the stop rule.

This is evidence that AX focus/raise is insufficient evidence of Win32 foreground ownership in this environment. A future fresh allocation needs a visible target interaction followed by the independent foreground probe before creating the public caller session. No product behavior or task effect is claimed.

# R35 result — title mismatch stopped before MCP

**Disposition: STOP_FIXTURE_TITLE_MISMATCH_BEFORE_MCP.** The allocation is consumed; no retry was made.

The R35 source fixture process/window launched and Computer Use raised the exact R35 window. The independent foreground probe rejected it because the frozen per-trial record still expected the inherited R34 title, although the trial-level title had been changed to R35. HWND and PID matched; the title check failed. No MCP observation, dispatch, recovery, or task verification occurred. The durable fence was clear. The fixture remains open under the frozen stop rule.

This is a harness/configuration failure and gives no product-behavior result. The R34 parent packet remains immutable. A future allocation must freeze matching title values in both the top-level trial and trials array, then repeat from a new fixture.

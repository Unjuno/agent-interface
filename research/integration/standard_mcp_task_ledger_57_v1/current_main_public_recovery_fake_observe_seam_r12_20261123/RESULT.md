# R12 result

**Disposition: PASS for the narrowly scoped fake observation injection seam.** One fresh normal run and one fresh `-O` run both exited 0. Each verified that the supervised Win32 server called the injected fake exactly once, returned its unique observation marker, and the raw observation report had `input_dispatched: false` and no side-effect authority.

This confirms the direct minimal `interface_observe` seam. It does not explain the R10 lifecycle orphan that reported a real backend invalid-HWND error, because R10 followed the longer compiled-caller lifecycle path. Do not attribute R04/R09/R10 lifecycle cohorts to Fake solely from this minimal result. No task effect, input, recovery, MAP01, efficiency, provider accounting, or distributable runtime was tested.

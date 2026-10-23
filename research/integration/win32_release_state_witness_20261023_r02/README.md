# Win32 release-state observability R02

This input-free diagnostic fills the missing thread-desktop and token-integrity observations from R01. The owned fixture was foreground; the input desktop opened with `DESKTOP_HOOKCONTROL`, `UOI_IO` reported that it receives input, and the probe and fixture threads both named the `Default` desktop. The probe and fixture token integrity RIDs were both 8192. `GetAsyncKeyState` returned raw zero for Ctrl, S, and left button with no last-error value, while the fixture had received no input. All process/window cleanup completed.

This is evidence that neutral key state is returned as zero in a context where the documented inactive-desktop, desktop-hook-access, and higher-integrity target blockers were excluded for this owned fixture. It supports a narrowly scoped availability witness for this context; it does not prove release of a prior injected event or generalize across desktops, integrity levels, targets, or blocked calls. The R03 public release receipt remains `release_unverified`.
## Candidate validation

The desktop/query diagnostic is evidence for the branch implementation, not a release result. The final Win32 backend suite passed 85 tests in normal and optimized Python, and the CI-equivalent CLI/API set passed 131 tests in both modes (7 expected platform skips). The earlier 85-test normal run failed one alias-count assertion because the first candidate resampled despite having no availability witness; the implementation now fails closed before the extra query, and the corrected v2/final runs pass. Logs are retained here.

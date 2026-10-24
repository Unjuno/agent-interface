# S23 WSLc current-main private-Xvfb boundary probe

S23 passed the unmodified current-main standard-caller Xvfb test on WSLc 3.0.3 at a 3,920 ms private X-server pause under a 4,000 ms transaction deadline. The release readback completed 3,986.877 ms after cancellation admission, leaving 13.123 ms before the deadline. A separate parent X client independently read all keys up at 4,358.689 ms after cancel start; the delayed-request horizon was 8,502.055 ms with no delayed keypress.

The old and fresh synthetic task oracles passed. Public runtime state remains `UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`. Audit: 25/25. This is synthetic private Xvfb only; it establishes no physical GUI, real application, MAP01, efficiency, or reliability claim. WSLc constraints match S22; see the audit for the Docker pids/tmpfs condition difference.

See [PREREGISTRATION.json](PREREGISTRATION.json), [AUDIT.json](AUDIT.json), [raw result](output/result.json), and [S22 comparison](../wslc-currentmain-xvfb-blocked-release-s22/RESULT.md).

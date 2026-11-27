# Chromium V5 point-mint generation guard R06

R05's baseline reproduced the missing process/window-generation comparison in
both modes. After implementing the guard, the test harness was hardened to
load the exact method under a private module name and restore its temporary
unused-parent stub, avoiding pollution of subsequent unittest imports. R06 is
the frozen post-fix rerun using that final harness.

One normal and one `-O` process run the same three generation cases, followed
by existing semantic-handle, caller/core handoff, and adaptive caller/core
composition regressions in that same process. The new tests must refuse both
changed-generation mint attempts before registry creation and preserve the
same-generation positive. The combined 23-test suite must pass in each mode.
This validates a local Fake-only contract; it is not live GUI, provider,
efficiency, or recovery evidence.

# Current-main WSLc optimized XRes 1 s diagnostic R06

Status: **DIAGNOSTIC FAIL / UNKNOWN PRESERVED**.

The optimized standard-caller unittest exited 1. With only `_XRES_DISCONNECT_TIMEOUT_S=1.0` changed in memory, owner disconnect was confirmed after 448.15 ms. The follow-up release worker still timed out after 1,505.35 ms; its result was UNKNOWN and the independent X keymap still read A down. The final fixture cleanup later read A/B/C up. No source file was modified. The exact test assertion, JSON and logs are retained.

This shows that getting past the XRes disconnect query is insufficient: release-worker supervision and neutral key state remain separate boundaries. The next R07 diagnostic changed only the in-memory release-worker budget to 3 s while holding the XRes diagnostic at 1 s. This one sample does not justify production timeout changes or establish a task pass.
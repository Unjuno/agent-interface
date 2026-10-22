# A07 result

A07 is preserved as `STOP_HARNESS_PROBE_KEYCODE_MISMATCH`. The actual V15 process backend admitted allowlisted `a` (X keycode 38), but the independent observer still checked keycode 25 (`w`). The gate therefore stopped before session SIGKILL; the owner was force-terminated, and recovery was not tested. A07 is not retried. A08 will probe the keycode for `a` and is a new frozen allocation.

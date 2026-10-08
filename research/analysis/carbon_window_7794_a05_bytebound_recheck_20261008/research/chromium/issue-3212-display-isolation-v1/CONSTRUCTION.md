# #3266 display isolation construction evidence

Status: CONSTRUCTION_PASS_ONLY

## H/T/D/C/U

- H: A fresh Xvfb display with TCP disabled can host a fresh Chromium/CDP process, providing the prerequisite for generation-correlated p1/p2 experiments.
- T: Use a fresh Debian bookworm-slim container; start Xvfb on :92; start headless Chromium with a fresh profile and CDP port 9222; poll /json/version; retain startup failures and final process/display identity.
- D: Record container topology, display, Xvfb PID, Chromium PID, CDP endpoint and raw stdout/stderr. Do not claim X11 window correlation or application effect.
- C: Construction PASS only if Xvfb and Chromium/CDP start successfully. Formal PASS requires later p1/p2 identity correlation, stale-XID controls, and independent effect.
- U: No formal allocation was run; no input or application effect was attempted.

## Results

1. Xvfb smoke in Debian bookworm-slim:
   OBSTAC_XVFB_ISOLATION_SMOKE PASS display=:91 pid=6
2. Chromium/CDP smoke in a fresh Debian bookworm-slim container with --shm-size=512m:
   OBSTAC_CHROMIUM_CDP_DISPLAY_SMOKE PASS display=:92 xvfb_pid=7350 chromium_pid=7351

The Chromium probe recorded initial connection-refused polls before /json/version became available. This is startup polling evidence, not a failure.

Related: #3266, #3212.

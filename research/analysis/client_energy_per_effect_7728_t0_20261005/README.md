# Issue #7728 T0 — client energy-counter eligibility

**H.** A documented, supported cumulative energy counter with explicit domain, unit and resolution may be available on this host without privilege escalation.

**T.** At pinned main `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310`, capture macOS/hardware identity without hostname, hash `/usr/bin/powermetrics`, inspect its local manual and help, and make one two-sample, unprivileged `cpu_power` probe. Do not start a GUI task or compare routes. An energy estimate/process score does not qualify.

**D.** Only if a cumulative counter is observable and explicitly gives domain, energy unit and resolution may a later protocol-validation rung be designed. Otherwise stop with `HOLD_ENERGY_SENSOR_UNAVAILABLE`; no T1 pilot.

**C.** Native host execution is required to check the host sensor boundary; containerization would expose a different measurement surface. No `sudo`, `powermetrics` elevation, installation, model, GUI, app task, or route execution.

**U.** Other Apple hardware/OS versions, privileged samplers, and the existence of a future validated energy source are outside this probe.

See `REPORT.md`, frozen inputs in `FREEZE.json`, raw command outputs in `RESULT.json`, independent source/result checks in `AUDIT.json`, and `SHA256SUMS`.

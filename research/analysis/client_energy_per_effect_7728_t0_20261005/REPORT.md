# Issue #7728 T0 — client energy-counter eligibility (2026-10-05)

## Disposition

`HOLD_ENERGY_SENSOR_UNAVAILABLE` for this unprivileged macOS host preflight. The probe did not expose a documented cumulative energy counter with explicit measurement domain, unit, and resolution. **No energy-per-effect comparison was run.** This is a metrology eligibility stop, not evidence that guarded routes use more or less energy.

## H / T / D / C / U

**H.** A supported cumulative energy counter with explicit domain, unit and resolution may be available on the active host without privilege escalation.

**T.** At pinned main `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310`, record privacy-minimized host details, hash `/usr/bin/powermetrics`, read its local manual/help, then issue one two-sample `cpu_power` request with no elevated privileges. Treat only a documented cumulative counter as eligible.

**D.** Proceed to protocol validation only if the counter reports cumulative energy with a defined power domain, unit and resolution; otherwise use the Issue-prescribed HOLD and do not launch a route/task pilot.

**C.** Power estimates and process Energy Impact are not converted to joules. No model, GUI, application task, route, battery-derived estimate, CPU-time proxy, `sudo`, or other privileged probe is used.

**U.** This says nothing about root-authorized sensors, other macOS releases/devices, or whole-system/remote energy. It does not imply that a suitable sensor cannot be made available later with explicit authorization and calibration.

## Evidence and limit

The frozen package retains the exact commands, exit statuses, stdout/stderr, host OS/build/model (no hostname), binary hash, and local manual output. The independent auditor verifies the freeze, executable identity, probe arguments, documentation's stated limits, and the stop classification. The probe requires superuser access; no escalation was attempted. The local manual describes `powermetrics` power values as estimates and per-process Energy Impact as a rough proxy, neither of which meets the Issue's joule-counter gate.

The candidate's raw-man parser failed to recognize the process-proxy phrase because terminal overstrike/line wrapping split the text; that false boolean remains unchanged in `RESULT.json`. Auditor attempts v1 and v2 independently failed on the same presentation formatting and are preserved. Auditor v3 normalizes overstrikes and whitespace, independently confirms the manual's limits, and passes. The primary eligibility stop is supported by the exact unprivileged sample error plus the documented API limitations; no candidate or sensor probe was rerun. Sensor monotonicity, wrap/reset, idle baseline, boundary repeatability, oracle agreement, and route/task outcomes remain untested because eligibility failed before those gates.

Next eligible step: if the user supplies or authorizes access to a supported, calibrated cumulative counter for this host, freeze a separate protocol-validation allocation before any GUI route attempt. Do not treat this report as authorization for that work.

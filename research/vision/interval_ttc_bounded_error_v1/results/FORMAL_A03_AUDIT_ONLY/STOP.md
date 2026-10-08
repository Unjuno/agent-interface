# Issue #8157 A03 STOP

Disposition: `STOP_AUDITOR_RUNTIME_ERROR`. The frozen audit-only program was invoked once in the pinned WSLc container and exited 1 with `NameError: name 'profile_observed_prefixes' is not defined` while assembling the report after reconstruction. No `AUDIT_REPORT.json` was created. The candidate and generator were not invoked. The auditor was not retried; A03 has no raw-audit verdict and makes no scientific inference.

The exact frozen command, runtime, warning, exception, and invocation counts are retained in `RUN_RECORD.json`. The WSLc warning says swap/cgroup limits are unavailable; no hard memory or swap-isolation claim is made. The A03 source, protocol, freeze, A02 raw, A02 `FAIL_METHOD`, and construction tests remain preserved. Any correction uses a separately frozen successor allocation.

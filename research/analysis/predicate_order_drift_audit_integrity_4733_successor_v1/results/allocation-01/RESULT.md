# Formal result — Issue #4994

Disposition: **PASS_AUDIT_HARDENING_SCOPED**.

A fresh one-shot run on the local, pinned linux/amd64 Docker image completed with unit tests, runner, and independent auditor all exiting 0. The unchanged retained baseline was accepted by the hardened auditor (336 rows / 21 distributions). The baseline's historical result remained `PASS_DRIFT_BOUNDARY_MAPPED` with 5/5 predecessor corruption controls rejected.

All frozen controls passed:

- NaN row weight, `development_alpha=0.5`, and `truth_state_count=99`: all rejected.
- JSON `NaN`, `Infinity`, and `-Infinity`: all rejected.
- Boolean, string, NaN, ±Infinity, and 0.1 weight controls: all rejected.
- Exact and frozen-rounded valid weight unit controls: accepted.
- Independent raw-only replay: `PASS_INDEPENDENT_RAW_REPLAY`, 336/336 rows, 21/21 distributions, zero errors; crossover recomputed at alpha 0.70.
- Extracted raw SHA-256 before and after: `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`.

The local audit result retains the STOP for #4959 allocation-01 unchanged. This successor is a fresh allocation and does not reinterpret that STOP or its out-of-protocol diagnostic.

Scope is one synthetic retained corpus on one local container image. This does not alter #4733's scientific result and establishes no real timing, GUI/task effect, production authority, broad JSON interoperability, or general security certification.

Raw probe, unit-test logs, independent audit stdout/stderr, individual exit codes, and SHA-256 manifest are retained beside this report.


# Issue #3595 — audit-only reconstruction of #3587

This successor revisits only the immutable raw evidence from the three formal
#3587 allocations. It does not change their preregistered outcome: frozen audit
v1 returned `HOLD_OR_FAIL`, and Issue #3587 remains HOLD. No runtime, GUI, Xvfb,
or input is launched here.

The directory `prior_issue_3587/` contains the original freeze, runner, v1
auditor, preregistration, and excluded construction evidence. The original
formal bytes are under `evidence/issue-3587/formal/`; the v1 auditor's failed
output is retained verbatim under `evidence/issue-3587/original-audit-v1/`.

The v2 auditor has its own H/T/D/C/U in `AUDIT_PREREGISTRATION.md`. It checks
source/archive binding, every raw request/report/image link, exact independent
effect, received marker, release/cleanup, and controlled corruptions. It can
only produce `PASS_RAW_RECONSTRUCTION_ONLY`; it cannot retroactively pass the
frozen Issue #3587 gate or establish host/model visibility, latency, or benefit.

`PRECHECKS.md` records the excluded construction-only auditor qualification;
`FREEZE_V2.json` pins the final raw-auditor bytes before the one formal
audit-only execution.

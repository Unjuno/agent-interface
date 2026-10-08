# A01 first outcome — `HOLD_AUDIT_INPUT`

The frozen read-only source audit was invoked exactly once on current-main tree `8b04b87394973edee9308dbd62283017479554ee`. It exited 1 before producing any source-identity finding because the audit script incorrectly required `ObservableSignalPolicyMonitor` to be defined in the controller module AST. The implementation imports this monitor rather than defining it there. This is an audit-harness defect; no controller or session bytes were changed, and the source identity hypothesis is untested by A01.

The exact exception and command are retained in `results/a01-first-outcome/` with a SHA-256. No A01 retry is permitted. A02 is a separate allocation that will inspect the monitor's actual current-main import source.

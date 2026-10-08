# Issue #6081 error-carry T0 successor (OrbStack)

This package executes the offline action-compilation idea from [Issue #6081](https://github.com/Unjuno/agent-interface/issues/6081). It preserves the earlier #6087 unsafe-schedule failure, S1/S2/S3 setup STOPs, and #6091 invalid-baseline STOP without editing or rescoring them.

## Outcome

`PASS_METHOD_SCOPED` for the finite, exact-rational, constant-displacement fixture only. See [RESULT.md](RESULT.md) for the H/T/D/C/U and the qualified interpretation.

The formal candidate ran once in OrbStack and produced 80 rows. S4's first formal auditor STOPped on a refusal-schema KeyError; that STOP and raw were preserved. Audit-only S5 independently reconstructed 80/80 rows exactly but its decision code applied an extra rule that any unsafe baseline invalidated the method, so its retained output is `FAIL_METHOD_OR_SAFETY_GATE`. S6, separately preregistered, re-evaluated the original frozen acceptance criteria and passed; S7 separately verified all 21 exact/zero/refusal controls. None of these historical source/output files were overwritten or rerun.

## Evidence map

- [H/T/D/C/U and result](RESULT.md)
- [S4 plan and freeze](PLAN.md), [freeze manifest](FREEZE.json), [candidate raw](results/formal-01/raw.json), [S4 STOP](S4_STOP_REPORT.md), [S4 run receipt](S4_RUN.json)
- [S5 audit-only plan](audit_successor_s5/PLAN.md), [freeze](audit_successor_s5/FREEZE.json), [exact reconstruction plus retained gate output](audit_successor_s5/results/formal-audit-01/audit.json)
- [S6 decision-audit plan](audit_decision_successor_s6/PLAN.md), [freeze](audit_decision_successor_s6/FREEZE.json), [PASS decision receipt](audit_decision_successor_s6/results/formal-gate-01/decision.json), [run receipt](audit_decision_successor_s6/RUN.json)
- [S7 fixed-control plan](fixed_control_audit_s7/PLAN.md), [freeze](fixed_control_audit_s7/FREEZE.json), [21/21 control receipt](fixed_control_audit_s7/results/formal-controls-01/controls.json), [run receipt](fixed_control_audit_s7/RUN.json)
- [checksums](SHA256SUMS.txt)

All candidate/audit executions used `python:3.12-alpine`, image ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`, OrbStack Linux/ARM64, network disabled, read-only source/rootfs and resource caps. Formal raw data is not a GUI/game trace.

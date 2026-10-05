# Issue #7889 T0: equal-cost breadth versus repetition

This package tests the method-level claim that task/app breadth can matter more than repeated observations within a few cells when route contrasts vary across tasks or apps. All observations are deterministic synthetic draws from the frozen finite generator in `PREREGISTRATION.md`; no actual agent, model, interface, application, or user task was measured.

Three designs each spend 96 paired observations: 3 apps × 4 tasks × 8 repeats; 3 × 16 × 2; and 8 × 6 × 2. Four known normal variance profiles cover main-only, task interaction, app interaction, and combined interaction. A separate rare-hard-task generator records distinct task coverage. Missing paired and unknown outcomes must fail closed. `candidate.py` emits raw replicate ledgers and a summary; the separately executed `auditor.py` recomputes gates from those ledgers without importing candidate code.

Run commands, image digest, branch, source main, and preregistered thresholds are in `COMMANDS.json` and `PREREGISTRATION.md`. Container/runtime facts and SHA manifests will be retained alongside the executed outcome. Only the method-specific finite synthetic result can pass; this package cannot authorize or establish a prospective route decision.

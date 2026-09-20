# Needle pilot-06 — isolated near-boundary shift and auditable controls

Issue: https://github.com/Unjuno/agent-interface/issues/3869  
Allocation: `needle-intent-distill-3458-pilot-06-isolated-shift-audit`

This successor corrects two review-discovered design/evidence defects in pilot-05 without changing its retained FAIL. Only the CORRECT covariate shifts; CONTINUE/WATCH are identical balanced generator controls. Raw invalid-control metadata and features are stored so the independent auditor can recompute their outcomes.

Read `PREREGISTRATION.md` for H/T/D/C/U, gates and limits. Formal evidence, audit, environment, freeze, and checksums are preserved beside the sources. Do not rerun an allocated formal invocation.

## Reproduction

Use cached image `needle-pilot05:local`; never pull or prune. Run one construction check before freeze, then one formal invocation and one independent audit, all network-isolated and read-only except for dedicated output mounts. The formal directory must be new and empty. See `PREREGISTRATION.md` and `ENVIRONMENT.json` for exact limits. A PASS is synthetic-only and authority-neutral.

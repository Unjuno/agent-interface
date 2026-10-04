# T4 first outcome — STOP_AUDITOR_MUTATION_CONTROL_BUG

Allocation `LOGICAL-TIME-SYMMETRY-7327-FIXED-OVERHEAD-T4-20261004-01` was preregistered on Issue #7327 comment 5975622054 against frozen main `68e0378362b5ce6775f253064eaad63a2da6cda9`. The fresh pre-candidate main check matched.

- Candidate: exactly one invocation, exit 0; three rows written to `output/raw.json`. SHA-256: `f7e462942ac1ecbc426e0bb48e87b1a8e3c74831613d9493c4e1ab3e2d0f27f3`.
- Auditor: exactly one invocation, exit 1 before raw integrity/scientific checks. The fourth mutation control indexed a trace dictionary as a list (`KeyError: 0`).
- Retries: 0. The candidate and auditor allocation is consumed; neither command may be rerun for T4.

Disposition: `STOP_AUDITOR_MUTATION_CONTROL_BUG`. No scientific result is claimed because the independent auditor did not audit the retained raw. Preserve `output/raw.json` unchanged. A new audit-only successor may independently bind this raw to its frozen spec/source; it must not rerun the T4 candidate or auditor.

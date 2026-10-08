# Verifier label maturity T0 A02

Issue #7993 asks when interim verifier-risk claims remain identifiable while effect labels are pending, delayed, or lost. This package adds an exact, independently audited check of the assumption-conditional IPCW superpopulation estimator subgate.

This is a distinct successor to the finite-cohort method result in [draft PR #8028](https://github.com/Unjuno/agent-interface/pull/8028) and the exploratory repeated-cohort calculation in [draft PR #8034](https://github.com/Unjuno/agent-interface/pull/8034). It prospectively tests the exact expected IPCW value with exhaustive rational enumeration and an independent raw-only auditor. No rows or outputs from either PR are reused. It does not repeat A01's finite-cohort-bound result.

The allocation is based on main `5db548aa351c8ccd351831485d5e5940a4967ff3`. OrbStack image inventory hit the host's existing containerd blob-read error, so the prospective allocation explicitly uses native macOS Python. It claims no container isolation and no OS-enforced network isolation. The exact freeze and one-shot receipt will be recorded after the formal driver; the candidate will read only `public_input.json`, while the independent auditor may also read `auditor_truth.json`.

Reproduction after the freeze: `python3 -B run_formal.py`. Construction-only checks use `python3 -B -m unittest -v test_construction.py` and do not consume the formal invocation.

No live trace, real verifier label, GUI, model, user data, GPU, external effect, conformal guarantee, or production risk claim is in scope.

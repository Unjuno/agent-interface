# Formal T0 outcome — retained audit failure

**Disposition: `METHOD_FAIL_AUDIT`.** This one-shot allocation did not pass its independent-audit gate. Do not rerun it and do not interpret it as evidence about real task cohorts.

- Allocation: `5593-MULTISTATE-STOP-RECOVERY-T0-20261002-01`
- Frozen main: `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`
- Pinned container image: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Candidate: invoked once in a fresh network-disabled bounded container; exit 0; output says 5 launched episodes and 6 ticks.
- Candidate output SHA-256: `83997cc3799812cb71ef44194c961ab3a7a50cafb3266f4398b80fc1738c64da`.
- Independent auditor: invoked once in a separate fresh container; exit 1. No retry; `audit_result.json` was not produced.
- Exact failure: `ValueError: mutation not rejected: omitted_episode`.

The auditor's corruption-control harness called `reconstruct()` on a shortened ledger, then accepted the shortened ledger's own `launched_n` as its denominator. It did not compare the mutation against an independently frozen expected N=5. Thus the base candidate/reconstruction equality is not enough to establish denominator integrity. The failure is in the audit/mutation control; it is not proof that the candidate's five-row output itself omitted a real episode.

Construction tests: 11/11 and `py_compile` passed before freeze. The formal auditor falsified the adequacy of that construction gate. Candidate and fixture remain unchanged. A successor must freeze expected cohort N independently, prove each frozen launch ID is present exactly once, and make the omission mutation compare against that frozen roster before any new formal candidate run.

Scope: synthetic host-state bookkeeping only. No real cohort, GUI, model, user data or network was involved. The unrelated shared Docker container was not entered, stopped, or changed.

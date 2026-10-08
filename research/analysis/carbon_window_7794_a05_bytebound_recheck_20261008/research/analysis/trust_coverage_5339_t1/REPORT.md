# Issue #5339 T1 — finite trust/coverage discriminator

## H/T/D/C/U

- **H:** A declared trusted-singleton contract recovers intended single-group decisions without upgrading duplicate, correlated, stale, provenance-incomplete, or out-of-scope evidence.
- **T:** Compare the existing two-fresh-group rule, an explicit singleton-trust contract, and an intentionally unsafe any-singleton relaxation on 11 frozen traces.
- **D:** Standard-library Python candidate plus separate raw-only audit; no model, GUI, action, network, or external service. Docker remained STOP because shared OrbStack state was unobservable and a competing client remained recorded in #5085. Obstac was not exposed as a tool or executable in this environment.
- **C:** Candidate contract recovers trusted positive and negative singleton cases, admits two independent fresh groups, and rejects all six adversarial upgrades. Unsafe relaxation must expose counterexamples.
- **U:** Synthetic labels assume trust issuer, provenance, freshness, group independence, and scope metadata are truthful. No calibrated source trust, real receipts, runtime integration, GUI safety, error rates, or benefit is established.

## Result

**PASS_T1_FINITE_CONTRACT_DISCRIMINATOR (scoped).** The frozen contract policy matched all 11 declared semantic labels. The two-group baseline matched 8/11 and abstained on both declared trusted-singleton cases plus the stale+current case. The deliberately unsafe any-singleton rule produced three false admissions: untrusted singleton, missing provenance, and out-of-scope singleton. Duplicate and common-group correlated evidence remained ABSTAIN under the contract. The raw-only independent auditor checked all rows and the raw SHA-256.

This is a discriminator of policy behavior, not proof that real-world trust labels can safely be assigned. A production policy still needs issuer/provenance validation and held-out repository-compatible receipts before the exception can be used for authority.

## Immutable first run and audit correction

The first candidate raw is retained unchanged. The first auditor invocation exited nonzero because the audit's expected tuple incorrectly treated the intentionally unsafe comparison as conservative and mixed intended labels with policy-specific outputs. This was an auditor expectation defect, not a candidate raw mutation. The auditor was corrected to use literal row expectations and separate adversarial behavior; the final audit then passed. The exact first output is preserved in `audit_first_stop.json`.

## Reproduction

From the repository root:

```sh
python3 -I research/analysis/trust_coverage_5339_t1/candidate.py
python3 -I research/analysis/trust_coverage_5339_t1/audit.py
python3 -m py_compile research/analysis/trust_coverage_5339_t1/candidate.py research/analysis/trust_coverage_5339_t1/audit.py
```

Candidate raw SHA-256: `fa1caf6add6ba80c7396da46820de45fffe7bbe14fbc8fbfda9b16fec0d4bd3d`.

## Provenance

Frozen against main `57b56de2831204885c55375737580e5d82d3ab98`; path is additive and does not modify #5305 evidence. No container was started and no consumed allocation was repeated.

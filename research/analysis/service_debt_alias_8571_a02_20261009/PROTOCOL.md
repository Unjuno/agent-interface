# Issue #8571 A02 — frozen protocol

**Allocation:** `SERVICE-DEBT-ALIAS-8571-A02`

**Base:** `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`

**Scope:** deterministic standard-library CPU method study; no model, GUI, network, identity system, shared runtime, or external action.

## Lineage and changed factor

A01 remains `HOLD_CUSTODY_FREEZE_NOT_COMMITTED_BEFORE_RUN`; its first candidate and audit remain preserved in `service_debt_alias_8571_a01_20261008/` and PR #8575. A01 is not rerun or pooled. A02 is a new allocation with an immutable freeze commit created before formal invocation. It expands the complete alias partition set from four A requests (15 partitions) to five A requests (52 partitions), keeping five B requests, the four-slot horizon, service units, comparator policies, outcome oracle protocol, and hard-safety controls fixed. This tests whether the representation effect and trusted-parent invariance persist over the next complete partition size.

## H / T / D / C / U

**H.** Across all 52 caller-label partitions of five otherwise identical eligible A requests, at least one nontrivial presented-ID partition will increase A's four-slot service share over the one-identity presented-debt baseline. Trusted-parent debt will reproduce the baseline trace for every partition. FIFO remains invariant to alias labels. Alias labels and fixture parent links are synthetic; no real identity inference is made.

**T.** The fixture has five one-tick A requests and five one-tick B requests, all available at time zero, with a four-tick exclusive-resource horizon. Compare FIFO, least-cumulative-service debt keyed by caller-presented ID, and the same debt rule keyed by a trusted fixture parent. Enumerate every set partition of the five A requests (Bell number B5=52). Preserve every partition, including nulls. Retain the A01 controls for equal-total-service fragmentation, three honest principals, revoked work, missing joint grant, false parent link, and mandatory release. Candidate emits dispatch attempts only. A separately implemented auditor reconstructs every schedule and joins the fixed independent outcome oracle after dispatch.

**D.** `PASS_METHOD_SCOPED` requires complete 52-partition coverage; at least one presented-ID service-share advantage; exact trusted-parent baseline trace for all partitions; FIFO invariance; exact reconstruction of every row and safety control; and rejection of all five frozen mutations. `FAIL_NO_ALIAS_ADVANTAGE_IN_FIXTURE` applies when the complete fixture has no advantage. Any replay, denominator, safety, oracle, or mutation gap is `FAIL_METHOD`/`HOLD_AUDIT` as defined by the auditor. The custody requirement is a committed freeze before either formal invocation. One candidate invocation only; run the auditor once only if candidate exits 0; no retries.

**C.** FIFO may be the appropriate label-invariant policy when arrival order is the entitlement. Eligibility, deadlines, semantics, service units, and queue architecture may dominate aliases. Trusted parent is an authored input, not an implemented authentication mechanism.

**U.** This extends only a finite authored schedule. It does not estimate real waiting time, identity abuse, user fairness, quality, or production benefit; equal service does not imply equal semantic value. The result does not establish consent, authority, identity provenance, or a recommendation to collect identity data.

## Construction and execution

Before freeze, `test_model.py` passed four construction checks over the full 52-partition fixture, independent candidate/auditor replay, exact safety controls, and five corruption cases. Formal execution is host CPython 3.14.5 on macOS 27.0 ARM64, standard library only. No container is needed for this finite no-OS-input method test. Freeze the exact source/input hashes and commit them before the candidate; preserve the first candidate/auditor outcome without retry.

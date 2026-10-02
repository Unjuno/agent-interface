# Issue #5841 T1 path-sharing probe — source freeze

- Allocation: `ISSUE5841-T1-HOST-20261001-01`
- Frozen at: `2026-10-01T06:48:00Z`
- Source `main` observed via GitHub MCP: `2fbbd0430359a2de11609372e003c3f6ad632a36`
- Platform: Windows 11 Home 10.0.26200, AMD64; CPython 3.12.10
- Docker Desktop: UI process present; `desktop-linux` context selected; `com.docker.service` stopped/manual. Version probe timed out; service start refused with “Cannot open service”. No container/image is claimed.
- Tier: deterministic host-only construction probe. No repository runtime, scorer, GUI, model, network service or formal/live allocation is invoked.

## H / T / D / C / U

**H.** A same-cohort sentinel can add detection beyond existing all-attempt reconciliation only for injected faults that actually share an observation/export path with the sentinel. It must not be described as general bias detection. A primary-only classifier/export fault should remain explicitly `OUT_OF_SCOPE_UNDETECTED`; independent sentinel adjudication must separate measurement error from a real collateral effect.

**T.** Seven finite cases, each with four A and four B assignments (56 assigned rows total): clean null, true primary benefit, shared-path export fault, primary-only export fault, missing terminal record, foreign assignment join, and true sentinel collateral. Ground-truth primary/sentinel values are separately stored from observations. Existing all-attempt reconciliation checks one terminal per assignment plus assignment and route identity. The proposed sentinel signal compares observed sentinel rates by route within the same cohort. Shared transformation stages are fixed as `assignment_join → export_serialization → retention`; the primary-only stage is `primary_classifier`.

Path model:

```text
assignment → action → ground-truth primary → primary_classifier ─┐
                   └→ ground-truth sentinel ─────────────────────┤
                      assignment_join → export_serialization → retention → observed endpoints
all-attempt comparator: assignment IDs + route IDs + terminal presence ───────┘
negative control: same-cohort observed sentinel A-vs-B rate difference
independent oracle: ground truth + explicit collateral flag (audit only)
```

The fault classes are isolated one at a time. The common-stage scenario is represented as a fault that changes both serialized endpoints for one assigned episode; the primary-only case changes only the primary output. This is a logical finite construction, not an instrumented production pipeline.

**D.** Scoped construction pass requires: clean and true-primary-benefit cases have no control shift; shared-path fault is detected by the sentinel while all-attempt reconciliation passes; primary-only error remains `OUT_OF_SCOPE_UNDETECTED`; missing and foreign-join rows fail the existing comparator; genuine sentinel collateral is `COLLATERAL_FAIL`, not a bias diagnosis; the independent auditor rejects an omitted case and a relabelled primary-only false all-clear. Any disagreement is a construction failure/hold. This criterion does not qualify a real benchmark control.

**C.** Existing all-attempt reconciliation is the comparator and should remain primary for missing/identity errors. The sentinel is useful only for a declared shared transformation. The prior Issue comment #5925853020 is the motivation and is not an independent replication. The earlier T0 at `research/analysis/same_cohort_negative_control_5841_t0_v1/` remains unchanged.

**U.** No evidence establishes that a production endpoint has the declared shared path, that the sentinel is causally invariant, or that route-specific GUI side effects are separable from measurement error. The independent ground-truth oracle exists only in this synthetic fixture and is not available to the proposed operational detector. Four assignments per route do not estimate sensitivity. No claim is made about #57, the production scorer, agent behavior, or empirical benefit.

## Frozen source identities

See `FREEZE.json` for SHA-256 values of the candidate, fixture, test, and one-shot scripts. No candidate/auditor source edits are allowed after the formal candidate invocation begins. Construction pytest/compile/JSON checks passed before freeze; they are not formal candidate evidence.

Frozen command sequence:

1. `python execute_once.py` — exactly one candidate subprocess invocation.
2. `python audit_once.py` — exactly one independent auditor subprocess invocation; auditor includes two mutation rejections without rerunning candidate.


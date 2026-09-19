# Mandatory mediated reads via OS capability separation — retained result

Issue #523. A1 is retained as `INCOMPLETE_SUPERVISION_TIMEOUT` with 8/12 complete first outcomes, one partial-started ninth case, and three unstarted IDs; it is not pooled. A2 uses fresh IDs and changes supervision only.

## Decision

**`PASS_MANDATORY_READ_MEDIATION_SCOPED`**

- unrestricted stable: 3/3 raw DB reads succeed; A-only token; generation commits.
- unrestricted B-change: 3/3 raw B reads bypass receipt mediation; A-only token remains current and stale generation=2 commits.
- mediated stable: 3/3 raw DB access denied (`OperationalError`); A/B receipts are present; generation commits.
- mediated B-change: 3/3 raw DB access denied; A/B token observes B rev1; B mutates to rev2; owner rejects generation transition and leaves generation=1 with zero generation event.

All mediated cases retain root-owned DB mode `0600` inside root-owned private directory mode `0700`; task executes as UID/GID 65534 and reaches only the Unix-socket capability. Frozen audit errors: 0. Corruption controls rejected 4/4. Formal reruns: 0.

## Interpretation

Observed read receipts become authority-relevant only when access mediation is enforceable. Best-effort tracing is insufficient; removing ambient/raw store capability forces task-relevant reads through the receipt-producing owner boundary in this fixture. The result is scoped to Linux UID/filesystem separation and a cooperative local owner protocol; it is not a general sandbox/security proof.

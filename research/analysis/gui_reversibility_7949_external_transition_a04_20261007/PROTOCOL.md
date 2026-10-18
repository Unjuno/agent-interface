# #7949 A04 — event-observed transition invalidates old recovery certificate

## H / T / D / C / U

**H.** A complete source-bound external state transition after a GUI-action outcome makes a certificate tied to the prior state revision stale (`UNKNOWN`). If the transition is fully journaled, the new state is observed, and a new certificate is bound to its revision, a finite exhaustive recovery check can classify recovery while preserving the external writer's field. A missing/gapped transition remains `UNKNOWN`.

**T.** Three deterministic finite cases: (1) before external interference, an action outcome `100` is recoverable by `restore_snapshot: 100→000`; (2) an external writer changes an unrelated bit `100→110`, revision 1→2, invalidating the old certificate, while a refreshed certificate for state `110` uses `clear_owned_a: 110→010` and preserves external bit `b=1`; (3) the same transition with a sequence gap or incomplete coverage. Candidate verifies event sequence, revision, before/after chain, receipt revision and snapshot, then enumerates recovery sequences through horizon 1. Independent raw-only auditor replays the journal and checks state and policy conclusions.

**D.** `PASS_EXTERNAL_TRANSITION_SCOPE` only if case 1 is recoverable to `000`; case 2's old rev-1 certificate is `UNKNOWN_STALE_CERTIFICATE`, its rev-2 re-evaluation is `UNIVERSALLY_UNIFORM` to `010` without erasing `b`; the gap/incomplete case is `UNKNOWN`; all raw mutation controls are rejected; auditor errors=0. Any false acceptance or lost external bit is `FAIL_METHOD`; audit mismatch is `HOLD_AUDIT`; orchestration deviation is `STOP`. Candidate and auditor each run once; no retry.

**C.** The baseline A01 outcome-set classifier may suffice when receipts are current. A02/A03 external-write simulations are retained as separate STOP records and are not scientific support. An actual interface may not expose a complete event journal or stable revisions.

**U.** Only a tiny authored three-bit transition model and exhaustive horizon-1 recovery are tested. No GUI, application, concurrency primitive, external actor, receipt authenticity, runtime gate, user effect, or safety is established. This is a narrow successor probe, not runtime authorization.

## Provenance and execution controls

Issue #7949; A01/PR #7971 is unchanged. A02 and A03 STOP artifacts remain separate. Base `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`; isolated research branch `research/reversibility-7949-external-write-a01-20261007`; additive path `research/analysis/gui_reversibility_7949_external_transition_a04_20261007/`. Native macOS Python standard library is sufficient; prior OrbStack read-only inventory returned containerd `operation not supported`, and this deterministic micro-model does not require a container. Preflight tests must finish before freeze. Formal candidate is invoked exactly once by one command that writes stdout/stderr and whose tool exit code is retained. Auditor is invoked once only if the candidate command reports exit 0. Do not make a preview call, duplicate call, retry, or separate capture call.

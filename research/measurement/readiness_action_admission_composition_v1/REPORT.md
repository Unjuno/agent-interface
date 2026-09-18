# Readiness final-admission composition — first outcome

Decision: **PASS_READINESS_ACTION_ADMISSION_COMPOSITION_SCOPED**.

One source-first formal invocation, reruns/replacements/tuning0. The frozen eight-state readiness vocabulary remains evidence only. A consequential synthetic effect requires a fresh READY_FOR_ACTION receipt for the current runtime-owned readiness generation **and** a separate ordinary-authority=true gate.

Formal 600,000 transitions across four scopes and all eight readiness states:
- candidate/oracle result mismatch: 0;
- candidate/oracle full-state mismatch: 0;
- READY→nonready stale-receipt stress: 25,000 traces, stale effects **0**;
- READY→nonready→READY ABA stress: 25,000 traces, old-receipt effects **0**;
- fresh current READY effects: **71,380**;
- non-READY effects: 0;
- ordinary-authority=false effects: 0;
- cross-scope effects: 0;
- replay effects: 0;
- duplicate transition double-advance: 0;
- malformed controls: 8/8 fail closed;
- model/GUI/X11/task-input/readiness-authority promotions: 0.

The deliberately unsafe `SNAPSHOT_READY_ONLY` discriminator produced **25,000/25,000 stale effects** on the same READY→nonready stress family. Thus a historical READY receipt cannot safely be treated as permission, even if the system later returns to READY: freshness/generation and ordinary authority are separate final-admission requirements.

Independent audit PASS/errors[]; copied-result corruption controls5/5 reject; source rehash exact after formal. The 600,000-row compressed event ledger was audited locally and is committed by SHA-256 in POSTFORMAL/RESULT; the large ledger itself is not required for the scoped summary claim.

Boundary: synthetic composition semantics only. A production runtime may use one broader currentness token spanning readiness/target/focus/lease rather than a dedicated readiness generation. No shared runtime ABI is promoted by this result.

# Preregistration — Issue #6664 observable quiescence certificate T0

Allocation `OBSERVABLE-QUIESCENCE-CERTIFICATE-6664-T0-20261002-01`
Frozen main base: `9a573b00dc595e64d09387e567c85e10b61a46c1`
Additive path: `research/analysis/observable_quiescence_6664_t0_v1/`
Scope: finite protocol simulator; no actual GUI/backend, model, participant, or production claim.

## H / T / D / C / U

**H.** An accounted-quiescence policy will never issue `QUIESCENT` while an old-epoch operation remains admitted or can still take effect, any effect status is unresolved, any held input lacks a matching release receipt, or no fresh post-boundary observation covers the terminal operation/release state. EPOCH_ONLY and fixed TIME_DELAY can falsely certify on some frozen schedules; ACCOUNTED_QUIESCENCE classifies each admitted operation as complete, cancelled-before-effect, or `UNKNOWN` without promoting ambiguity to success. This is a finite method test, not a GUI-safety claim.

**T.** `scenarios.py` generates a deterministic finite grid inserting takeover at all six cuts around `ADMISSION → ENQUEUE → START → EFFECT → COMPLETE_ACK`, with applicable natural completion/cancel-before-start/cancel-before-effect paths, normal/delayed/lost completion acknowledgments, ordinary and held-key input, on-time/delayed/missing release receipts, and fresh/stale/missing observation receipts. It adds explicit old-epoch post-boundary admission attempts, duplicate operation IDs, backend restart without reconciliation, and restart with an operation-bound reconciliation receipt. Compare EPOCH_ONLY, TIME_DELAY (fixed one-tick grace), and ACCOUNTED_QUIESCENCE at the boundary, grace deadline, and terminal observation horizon. Preserve event IDs, monotone times/sequence, epochs, backend generations, operation status, input-down/release, observation coverage, policy decisions, and reasons. The independent auditor consumes only the scenario event ledger and candidate raw decisions; it does not import candidate logic.

**D.** `PASS_METHOD_SCOPED` iff (1) scenario generation is deterministic and all frozen cases are present; (2) the raw-only auditor reconstructs all event/operation identities and decisions with zero errors; (3) ACCOUNTED_QUIESCENCE has zero false `QUIESCENT` decisions at every snapshot, rejects every post-boundary old-epoch admission, and requires valid terminal evidence, current backend generation, released held inputs, and a post-boundary observation covering the latest relevant state event; (4) missing/contradictory receipts, duplicate IDs, restart without reconciliation, and missing/stale observations remain `UNKNOWN`; (5) both comparator policies produce at least one false `QUIESCENT` under the frozen schedule grid; and (6) all frozen corruption controls are rejected. Any false accounted certificate or missing operation identity is `FAIL_METHOD`; no comparator discrimination is `HOLD_NO_DISCRIMINATION`. No runtime gate is inferred.

**C.** A simulator can omit hidden OS/backend queues, non-cancelable effects, scheduler races, or incorrect application receipts. A one-tick grace is only a fixed-delay comparator, not a tuned competitor. Event order and receipt truth are authored by the fixture generator.

**U.** No actual backend drain/cancel semantics, OS input release, application effect, human takeover, safety, latency, usability, or portability is measured. A protocol-method PASS is not evidence that any concrete adapter can issue a true certificate.

## Sources and environment

The structural prior art is Chubby's lock sequencer/fencing and explicitly imperfect lock-delay fallback; it does not prove GUI backend drain or effect completion. Lamport motivates modeling event order separately from wall-clock assumptions, not GUI-specific behavior. The Issue explicitly authorizes only a deterministic simulator first and says no container allocation is authorized or required. WSLc is absent on this macOS host; run host-local CPython 3.14.5 using only the standard library. Do not start or probe OrbStack for this non-container protocol model.

## Freeze and execution budget

Run construction tests and independent raw audit controls before writing `FREEZE.json`. Then execute candidate once and independent audit once; no retries. Freeze generator, candidate, auditor, test source and the generated fixture digest. Preserve formal raw output, audit, command/exit record and SHA256 manifest. If source, environment, or auditor integrity fails, retain that exact STOP/FAIL and do not silently rerun.

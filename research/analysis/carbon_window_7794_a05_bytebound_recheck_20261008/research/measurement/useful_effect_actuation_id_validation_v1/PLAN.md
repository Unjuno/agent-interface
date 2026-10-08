# USEFUL-EFFECT-ACTUATION-ID-VALIDATION-20260917-001

BASE: d994bc01a6a23d21bd565b84d58a43a99a562f89
Parent Git blob: 979f257b4f02be80bcaa30ae8d5a0aa92162bfb1

H: Holding all parent interval/release/occupancy/authority/effect classification arithmetic fixed, require Actuation.actuation_id to be a non-empty str and EffectEvent.actuation_id to be None or a non-empty str. This prevents malformed/ambiguous lineage from becoming bound while preserving every valid-domain output exactly.

T: Reconstruct exact parent bytes and verify Git blob. Reproduce malformed matching-ID predecessor aliases. Candidate adds only validate_lineage() + analyze_validated() before delegating to unchanged parent analyze(). Fixed controls, then one formal invocation: valid-domain seed 96220260917001 / 50,000 cases and malformed-domain seed 96220260917002 / 50,000 cases. Independent auditor re-runs separate fixed controls and verifies source/result hashes. No network/model/GUI/game/input/authority action.

D: PASS_ACTUATION_ID_VALIDATION_SCOPED iff predecessor defects reproduce; malformed Actuation IDs and malformed non-None EffectEvent IDs all reject before classification; EffectEvent(None) remains valid unbound; valid Unicode/nonempty IDs remain valid; duplicate valid IDs retain rejection; all 50,000 valid cases match parent output exactly; all 50,000 malformed cases reject; source/result/audit integrity passes; formal invocation1, reruns0. Any valid semantic change = FAIL_VALID_ID_REGRESSION; malformed bound escape = FAIL_LINEAGE_ALIAS_ESCAPE; integrity mismatch = FAIL_INTEGRITY.

C: Upstream typed serialization could render this validation redundant. Non-empty Unicode strings are only syntactically unambiguous, not globally unique/session-scoped.

U: Synthetic same-process standard-library evidence only. Temporal causality is excluded (#950). Live/X11/MAP01/production claims excluded.

STOP: exactly one formal block after source-first Git publication/readback and ownership reread. No post-result threshold/schema changes.

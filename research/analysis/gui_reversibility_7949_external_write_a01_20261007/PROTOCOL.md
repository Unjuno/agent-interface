# #7949 A02 — source-observed external-write recovery boundary

## H / T / D / C / U

**H.** The A01 finite classifier's supplied `receipt_valid=false` flag does not establish detection of an external state transition. In a new finite state-machine allocation, replaying a complete, ordered, source-bound write journal against independently retained object/field revisions will distinguish: (i) no interference, (ii) a disjoint-field update that remains safe for field-scoped recovery but is refused by whole-object versioning, (iii) same-field and ABA writes that must refuse, and (iv) replacement, gaps, reordered history, incomplete coverage, or snapshot disagreement that must be UNKNOWN. A safe recovery is a new semantic effect and preserves unrelated writes.

**T.** Standard-library-only deterministic simulator, no GUI/model/user data/OS input/network/runtime mutation. Agent changes field `x` from 0 to 1, then a declared independent writer may modify `x`, `y`, or the object generation. The candidate receives the frozen event journal plus a final snapshot and must replay/validate them; it may not receive a precomputed invalidation verdict. Compare BLIND_INVERSE, WHOLE_OBJECT_VERSION_GUARD, FIELD_SCOPED_COMPARE_AND_COMPENSATE, and NO_AUTO_COMPENSATION. Cases: no external write; disjoint `y` write; same-field `x` write; `x` write-away/write-back ABA; object replacement; sequence gap; out-of-order events; incomplete coverage; event/snapshot mismatch; unjournaled revision change. A separate raw-only auditor independently replays the event records and reconstructs policy outcomes. Freeze sources, cases and gates before the single candidate and single auditor invocation; no retry or replacement.

**D.** `PASS_EXTERNAL_WRITE_BOUNDARY_SCOPED` only if the independent auditor reconstructs every case and all four policy outcomes; field-scoped recovery succeeds only for no-interference and the known disjoint write; the disjoint value is preserved; blind inverse demonstrates the planted lost update; the whole-object guard refuses the changed global revision; same-field/ABA refuse without overwriting; replacement/gap/order/coverage/snapshot/revision inconsistencies are UNKNOWN; the compensation has its own event/identity and never claims rollback; and all frozen raw mutations are rejected. Any unsafe write or false restoration claim is `FAIL_METHOD`; incomplete integrity/audit is `HOLD_AUDIT`; source/path/runtime mismatch before invocation is `STOP_PREFLIGHT`.

**C.** This only tests explicitly supplied, complete finite event histories and authored revision semantics. A native application may not expose a complete journal, field version, stable object generation, or atomic compare-and-compensate. A whole-object guard or no-auto-compensation may be the safer simpler choice.

**U.** No live application, history capture, actual external writer, GUI effect, authority, user benefit, production safety, or real compensation is tested. Detecting a planted gap in this finite journal is not proof that a real source's coverage certificate is sound.

## Execution and provenance

Intake main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
Issue lineage: #7949 A01 / PR #7971. A01 raw remains unchanged; this A02 replaces its supplied stale-flag assumption with explicit state-changing journal transitions. Formal execution target: native macOS CPython standard library because the Issue requires no container and the OrbStack read-only `docker image ls --digests --no-trunc` preflight returned containerd `operation not supported`; no container-isolation/resource claim will be made. No shared VM is used or altered.

The worktree/branch and additive path are exclusive to this A02. Candidate and auditor each run once after this protocol/source/input freeze. Preserve exact stdout/stderr, exit statuses, raw records, audit, hashes and STOP/FAIL/PASS qualification. No runtime integration is proposed.

# Predicate specialist versioned switch — Issue #4284 formal result

Allocation: `predicate-specialist-switch-4284-20260923-01`
Disposition: **PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED**

## Result

One prospectively frozen formal invocation completed. No reruns, replacements, exclusions or post-result tuning.

- lifecycle rows: 24
- ALWAYS_GENERAL calls: 24
- candidate GENERAL calls: 18
- candidate specialist-served rows: 6
- semantic mismatches: 0
- graph mismatches: 0
- authority grants: 0
- independent raw-only audit: 217 checks, errors=[]
- formal raw SHA-256: `dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31`

The candidate did not activate before the three-row shadow gate. v1 activation was bound to version/support/producer identity; novelty, support change, producer change and stale activation receipt fell back before incompatible specialist use. Required UNKNOWN stayed UNKNOWN. A directed v1 regression was rejected by GENERAL. v2 recovered only after its own three-row validation window and received a distinct immutable activation identity. Stable active rows used the specialist without a GENERAL call.

## Frozen controls and retained harness debt

The frozen controls wrapper rejected 10/12 declared controls and exited1. The two non-rejections were no-op harness defects: `candidate_value` wrote FALSE to a row already FALSE, and `candidate_graph` wrote YIELD_FALSE to a row already YIELD_FALSE. The preregistered scientific gate was >=10 coherent mutations rejected, so the 10 effective mutations satisfy it exactly. This first control output is retained and not rewritten.

A separately labelled postformal diagnostic changed value/graph on a TRUE/CONTINUE row; the unchanged frozen auditor rejected both effective mutations (2/2). This does not replace the first 10/12 control result.

## H/T/D/C/U

- H: shadow validation plus immutable version/support/producer receipts can bound specialist activation and fail closed on invalidation/novelty/regression.
- T: deterministic authority-neutral 24-row lifecycle; ALWAYS_GENERAL, UNGUARDED diagnostic comparator and SHADOW_VALIDATED_VERSIONED_SWITCH; immutable authored v1/v2 specialists; minimum shadow window 3; no GUI/model/provider/input.
- D: every lifecycle, semantic, UNKNOWN, version/provenance, invocation-reduction and integrity gate passed. Candidate GENERAL calls fell 24 -> 18 and 6 rows were specialist-served.
- C: synthetic authored lookup specialists make novelty and version changes clean; this is switching-contract evidence, not learned-model quality.
- U: no live task authority, production auto-deployment, natural drift frequency, token/model benefit, cross-platform or product claim.

## Construction / publication provenance

Construction attempt01 failed only because the expected v2 activation receipt assumed `a2`; the actual monotone activation ledger correctly included intervening v1/support activations and produced `a4`. The failure is retained. Attempt02 passed 8/8 and py_compile before freeze.

The first GitHub `SOURCE_BUNDLE.b64` publication was truncated/transcribed incorrectly. Formal invocation remained 0. The incorrect blob remains in branch history; only the bundle bytes were corrected. PLAN, FREEZE and source manifest were unchanged. Git readback then matched all four published freeze surfaces before formal authorization.

The formal study and audit exited0. The frozen controls wrapper exited1 for the two no-op controls described above. The surrounding container tool reported status1 with `TERM environment variable not set` after outputs were written; this envelope incident is retained separately and no scientific rerun occurred.

## Integration meaning

This scoped PASS supports a versioned semantic-provider lifecycle: shadow first, activate under immutable identity, invalidate before incompatible use, and recover only under a new validated version. It does not make a specialist authoritative and does not establish that a learned specialist is preferable to a deterministic rule or general model in production.

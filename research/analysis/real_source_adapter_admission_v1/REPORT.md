# #1823 real source adapter admission

Decision: **PASS_REAL_SOURCE_ADAPTER_ADMISSION_SCOPED**.

## Result

Two retained real-source families were normalized into a source-admission discriminator before they are allowed to feed a reusable typed dependency ledger.

| source | retained rows | false accepts | false rejects | disposition |
|---|---:|---:|---:|---|
| #1639 focus generation + observation identity | 5 | 0 | 0 | ADMISSIBLE |
| Chromium focus/surface/geometry context | 2 | 1 | 0 | INCOMPLETE |

The intentionally permissive `NAME_ONLY` policy admits both sources and therefore produces one false COMPLETE classification on Chromium task3→task4.

## Focus-generation positive
Pinned #1639 formal summary blob `8557cc1a70487df7abbfffb965a9e4d38ac3bfd5` retains 320 formal rows and oracle mismatch0. Its focus generation is unchanged for STABLE/PAINT_ONLY, advances for FOCUS_ABA/FOCUS_CHANGE, and the combined currentness contract also rejects IDENTITY_MISMATCH. In the scoped evidence matrix this source preserves both stable controls and rejects all authored invalidation classes.

## Chromium negative
Pinned guarded-macro fixture blob `349b4e19d88d718f159dabc362136f5a02b1ed89` and report blob `ee13e4abe3f77f2234bc69e1a948170a979523c5` retain:
- task2/task3 layout A: identical window context and old handle eligible;
- task3→task4 layout B: the same focus/surface/geometry values remain, but old field handle is `missing` and guarded execution yields before pointer input.

Therefore window context fields cannot be treated as a complete reusable target-validity dependency source for this invalidation class. They may still be valid dependencies for narrower scopes such as window identity; scope is part of source admission.

## Design consequence
The mediated ledger should not accept a field merely because it looks generation-like or identity-like. A source adapter needs an explicit evidence-backed applicability envelope. If retained evidence exposes a scoped invalidation that leaves the source unchanged, the adapter must return `INCOMPLETE/UNKNOWN` rather than fabricate a reusable version.

This preserves #1792's ledger mechanics while preventing source-level dependency laundering.

## Integrity
Frozen local bytes matched Git blob IDs before the single formal invocation:
- fixture `8f1ec4b81e69f73354faf4f41483d783cbf6235c`
- analyzer `7e7f7aa3378d7f59828826efad8cabcf6efaa30e`
- auditor `fee43e838ccf268adfb7f37ba3a4bfe0319d30c0`

Formal invocation1; reruns0; replacements0; tuning0.

## Limits
Finite retained evidence cannot prove universal source completeness. This is source-admission mechanics, not new GUI execution, production runtime integration, model/token benefit, or latency improvement.

## Next rung
Do not repair the coarse window source by inventing a privileged layout version. Instead test a separate **commit-time target-handle check** as current evidence: retained task3 handle VALID and task4 old handle MISSING should be represented as a typed current CHECK/RESOLVE result that can gate action without pretending to be a reusable long-lived version.

# Issue #626 audit identity-binding successor — host-only T0

Allocation: `MAP01-THREAT-DEOPT-626-AUDIT-IDENTITY-T0-20261001-01`  
Frozen source main: `7e94ba9fdbfbff8d32d5dde27c086f2eb7582775`  
Scope: synthetic six-row audit contract only. The original #626 source bundle and formal 0/6 schedule remain immutable. No Docker/OrbStack, ViZDoom, X11, model/provider, GUI, or input.

## H / T / D / C / U

**H.** An independently implemented raw-only auditor can preserve the frozen #626 semantic checks while rejecting any evidence whose six case IDs/order, baseline/candidate assignment, runtime bundle SHA-256, fixture ID, or seed differ from the frozen plan. The old frozen auditor lacks these identity checks, as already demonstrated in #626 comment #5923536117.

**T.** Freeze the original plan identities, exact six-case order, a deterministic synthetic raw fixture satisfying the old semantic gate, candidate generator, new independent auditor, legacy auditor source bytes, tests, and decision rules. Run focused contract tests before freeze. Then invoke the candidate generator once and the independent raw-only auditor once. Auditor controls mutate case ID, runtime SHA, fixture ID, seed, arm, and row completeness. No live/formal #626 row is created.

**D.** `PASS_AUDITOR_IDENTITY_BINDING_SCOPED` iff the pristine six-row fixture passes all semantic and identity checks, all six identity/completeness mutations are rejected, the old frozen auditor accepts the first four identity mutations (reproducing its gap), and frozen source identities match. Any source mismatch or missing output is STOP; a semantic mismatch is FAIL. Candidate/audit each run exactly once.

**C.** All six rows and outcomes are deterministic synthetic records. This tests auditor implementation and the specified identity contract only; the rows do not represent a real MAP01 session.

**U.** Does not repair or reclassify the original #626 audit/result, establish that its outcome rows were authentic, authorize its live allocation, or prove the handoff-fence hypothesis. Formal source bundle, original audit and six-session schedule remain unchanged. A later formal run must use an independently reviewed, source-bound auditor.

## Frozen identities and contract

The legacy audit source is the exact `audit.py` member of the #626 source bundle with SHA-256 `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65f34941a1f8c48a40`; bundle SHA-256 `e95dd3fd3992c70be54a4e16530fb26d71ab94d88054f2900f656aee53d8462a`. Frozen case order and identities are copied from #626's plan. Source files, fixture and output paths are additive under `research/doom/map01_threat_deopt_real_handoff_v1/audit_identity_successor_20261001_01/`.

The new auditor reimplements semantic checks independently and binds every row to the frozen case ID, pair, arm, seed, fixture, and runtime SHA; it does not import or patch the legacy auditor.

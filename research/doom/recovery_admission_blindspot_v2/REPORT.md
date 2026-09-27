# Recovery-induced visual drift versus health/ammo final admission — repair allocation v2

Task `MAP01-RECOVERY-ADMISSION-BLINDSPOT-20260917-002`, Issue #551. Direct environment-closure repair successor to #510 ID001, which remains retained as `INCOMPLETE_EXECUTION_ENVIRONMENT_CLOSURE` and was not rerun.

## Disposition

**`PASS_BLINDSPOT_SCOPED`.** In this fixed MAP01 threat-contact fixture, the bounded recovery program changed planner-visible RGB context beyond the retained `0.015` visible-change threshold in all three matched pairs, while the unchanged v38-style final action-validity mechanism still returned `VALID_CURRENT` in all six coast/recovery cases because health/ammo/current-age checks remained satisfied.

This establishes a missing evidence dependency: health/ammo freshness alone does not prove that the planner-visible context remained stable after local recovery. It does **not** establish that the frozen `turn_right/short` action was semantically wrong in every recovery case.

## Frozen repair boundary

Publication BASE `07676194ad9f1b6459fae93146ce0bfae52783e1`. Scientific code and audit are byte-identical to #510. The only repair was installing the complete 12-wheel closure from the exact offline runtime artifact SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`. No scored readiness case was run. Source-first freeze HEAD was `5e130f488d05a75a88a5d800102db85a60a575b6` before formal execution.

Formal schedule: three matched pairs / six fresh cases, order coast→recovery, recovery→coast, coast→recovery. Control is 600 ms coast. Recovery is five 50 ms `d` holds separated by observations plus 350 ms coast. Fixed seed `990619`, same `map01-threat-contact-v2`, same `session_map01_v12`, same frozen `turn_right/short` validity contract. One formal invocation, no retry/replacement/extension.

## First outcome

| pair | coast MAE | recovery MAE | recovery/coast | both `VALID_CURRENT` |
|---:|---:|---:|---:|:---:|
| 1 | 0.0133540 | 0.0408749 | 3.061× | yes |
| 2 | 0.0143970 | 0.0386781 | 2.687× | yes |
| 3 | 0.0143980 | 0.0386332 | 2.683× | yes |

All three recovery MAEs exceed `0.015`; none of the coast MAEs do. Every case remained health `97`, ammo `48`, terminal `completed`, independently verified empty release, and score `0` kills / `0` deaths / no map exit. Action-validity snapshot ages were about 45–53 ms, within the authored 700 ms current-age bound.

The frozen independent audit returns `PASS_BLINDSPOT_SCOPED`. Prefreeze contract tests re-passed after measurement without source changes.

## H / T / D / C / U

**H:** bounded recovery can materially alter planner-visible context while health/ammo-based final admission still says current.

**T:** one frozen six-case matched block; first outcomes only; exact runtime/source identities retained.

**D:** PASS because all six are `VALID_CURRENT`, every recovery exceeds the visible-change threshold and its matched coast MAE, and release/signal/score/integrity gates pass.

**C:** viewport drift can be harmless to the specific planner action; dynamic rendering/enemy timing can also contribute. Matched coast arms bound but do not eliminate those explanations.

**U:** one fixed MAP01 fixture and runtime artifact, no frontier-model call, no stale-action error rate, MAP01-clear, recovery efficacy, human-tempo or cross-domain claim.

## Architectural implication

Before model-in-loop recovery composition, a pre-recovery planner answer should not be readmitted solely because health/ammo remain fresh. The next useful one-factor gate is task-relative context binding/reanchoring: hold recovery fixed and compare the current health/ammo admission with one explicit visual-context dependency or require a fresh planner decision after recovery. Do not add several recovery mechanisms at once.

## Evidence retention

GitHub retains the frozen source/plan/FREEZE plus exact decision JSON. Full runtime evidence is retained in the conversation artifact `map551_evidence.tar.xz` (25,778,972 bytes, SHA-256 `caaf7ce7b8640e3ae261e1ff9b8bf998ea8b6feda425229b923034abde04512f`). A compact replay package containing all exact case result JSON plus all 12 source/post PNGs is `map551_compact_evidence.tar.xz` (1,387,536 bytes, SHA-256 `f5cfcafd21dbc58d4f08ecf112176180f6637498050c55445c280b59fb124122`). These binary archives are not falsely claimed as GitHub-retained; `publication.json` records their identities and all referenced image digests.

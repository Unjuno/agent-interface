# Issue #4150 — target-belief action-admission contract

Allocation: `target-belief-admission-4150-20260923-01`
Base at execution claim: `b38806cd09243f7ad18deb61db44048bc3feffae`
Owned path: `research/analysis/target_belief_admission_v1/**`

## H
Preserving a bounded candidate set is useful only if action admission preserves its ambiguity. With `MIN_SCORE=80`, closed `REQUIRED_MARGIN=20`, current provenance, and an explicit safe-probe capability, `BELIEF_MARGIN_ADMIT` should ALLOW only a sufficiently supported unique candidate; retain ambiguous evidence as PROBE or NEEDS_DECISION; and REJECT stale/wrong-source/wrong-geometry/sub-threshold evidence. The deliberately incomplete `TOP1_SCORE_ADMIT` comparator should false-ALLOW the frozen ambiguous score profiles.

## T
Standard-library CPython in the provided Linux x86_64 execution container. No Docker/OrbStack equivalence claim, GUI, model/provider, network experiment, OS input, or user data.

Formal corpus = 8 score profiles × 4 provenance states × 2 probe states = 64 rows. All constants and profiles are exactly those in Issue #4150. Construction is limited to directed boundary examples and does not enumerate the full corpus. One formal invocation; reruns/replacements/tuning0.

Independent oracle derives safe-to-act and expected disposition from authored profile truth plus provenance/probe state without calling either candidate admission function.

## D
`PASS_TARGET_BELIEF_ADMISSION_CONTRACT_SCOPED` iff rows64; candidate false ALLOW0; top1 false ALLOW6; candidate safe ALLOW6; candidate counts ALLOW6/PROBE3/NEEDS_DECISION3/REJECT52; input authority iff ALLOW; independent audit errors=[]; >=10 coherent mutations rejected; formal1/reruns0/replacements0/tuning0.

Any unsafe candidate ALLOW or authority on non-ALLOW is FAIL. Missing/source/process/raw/audit evidence is STOP/HOLD.

## C
Score profiles, truth labels, thresholds, and safe-probe availability are authored specification inputs. The top1 comparator is intentionally incomplete and is not alleged to be production code. This analysis does not calibrate detector confidence or probe safety.

## U
No live target quality, occlusion/distractor frequency, probe side effects, model candidate selection, planner round trips, task completion, token/image cost, latency, cross-platform or production claim.

## Variable table

| symbol/field | meaning | SI unit | definition | domain / assumption | type |
|---|---|---|---|---|---|
| s_i | candidate score | 1 | authored detector score | integer 0..100 in frozen profiles | scalar integer |
| s_1 | highest score | 1 | max score | undefined for empty profile | scalar integer |
| s_2 | second score | 1 | second largest score | absent for single candidate | scalar integer / absent |
| m | top margin | 1 | `s_1-s_2`, or +∞ for singleton | closed gate at 20 | scalar / extended scalar |
| p | provenance state | 1 | VALID/STALE/WRONG_SOURCE/WRONG_GEOMETRY | frozen categorical set | categorical scalar |
| q | safe probe available | 1 | authored probe capability | false/true | Boolean |
| N | formal rows | 1 | `8×4×2` | N=64 | scalar integer |

Unit check: score, margin, counts and authority flags are dimensionless. No physical-time or mixed-unit arithmetic enters the decision gates.

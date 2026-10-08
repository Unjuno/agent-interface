# Issue #4155 — typed failure-mode diagnosis first-rung plan

Allocation: `typed-failure-mode-diagnosis-4155-20260923-01`
Base: `118b385697a03be6452249bf2a0111718d7535c2`
Owned path: `research/analysis/typed_failure_mode_diagnosis_4155_v1/**`

## H
With equal caller-visible evidence, equal final recovery vocabulary, and unrestricted deterministic mappings in both arms, an explicit intermediate mode label does not by itself improve final recovery selection. `MODE_THEN_RECOVERY` can be compiled into an observationally equivalent `DIRECT_RECOVERY` mapping. The mode label may still help explanation, modularity, learning, transfer, or maintenance; those are outside this first decision-quality discriminator.

## T
Standard-library CPython only in the provided Linux x86_64 execution container. No model/provider, GUI task input, OS input, network experiment, user data, or shared runtime mutation.

Every formal row has the same symptom `EXPECTED_EFFECT_MISSING` and four caller-visible ternary evidence fields:
- focus ∈ {CURRENT, LOST, UNKNOWN}
- target ∈ {CURRENT, STALE, UNKNOWN}
- modal ∈ {ABSENT, PRESENT, UNKNOWN}
- app ∈ {IDLE, PENDING, UNKNOWN}

A fourth dimension `variation ∈ {0,1,2,3}` is irrelevant observable variation and must not alter the disposition. The formal corpus contains all 3^4 evidence combinations for every variation: N = 324 rows.

Uniquely identifiable single-fault signatures and frozen safe dispositions:
- FOCUS_LOST -> REBIND
- TARGET_STALE -> YIELD
- MODAL_BLOCKED -> RETRY_BOUNDED
- APP_BUSY_OR_PENDING -> WAIT_OBSERVE

All-normal, any UNKNOWN, contradictory/multi-fault evidence -> UNKNOWN -> YIELD.

Arms:
1. `DIRECT_RECOVERY`: maps the observable fields directly to the final disposition without producing a mode label.
2. `MODE_THEN_RECOVERY`: maps the same fields to one frozen mode, then maps the mode to the same final disposition vocabulary.

The independent oracle derives the abnormal evidence set and expected disposition without calling either candidate implementation.

Construction is limited to eight directed rows and unit checks; the complete 324-row corpus is generated only after source/gate freeze. One formal invocation; reruns/replacements/tuning = 0.

## D
- `PASS_TYPED_MODE_DIAGNOSIS_SCOPED`: mode arm has strictly fewer wrong recovery or unnecessary YIELD rows than direct, with no unsafe increase.
- `FAIL_DIAGNOSIS_LAYER_UNNECESSARY`: direct and mode both equal the independent oracle on every formal row; wrong recovery, unnecessary YIELD, and unsafe disposition are identical (zero), so the explicit intermediate label adds no decision-quality information under the frozen equal-input deterministic contract.
- `FAIL_DIAGNOSIS_MISROUTES_RECOVERY`: mode is worse or suppresses required YIELD.
- `HOLD_OBSERVATIONS_NOT_IDENTIFIABLE`: no uniquely identifiable single-fault positives survive the frozen corpus.
- `FAIL_INTEGRITY`: source/result/audit/corpus disagreement.

Independent audit must reconstruct all 324 rows, detect duplicates/missing rows, and reject at least 10 coherent result/source/provenance corruptions.

## C
A direct mapping is allowed the same information and representational capacity as the mode composition. Restricting DIRECT to symptom-only or a smaller table would confound “diagnosis benefit” with an artificial function-class disadvantage. The fixture is semantic/authority-neutral rather than a live application transfer.

## U
No learned classifier, explanation quality, maintainability, cross-application transfer, partial-observation inference, multi-fault diagnosis, model/token/latency benefit, authority, GUI recovery effect, or production claim.

## Variable table

| symbol/field | meaning | SI unit | definition | domain / assumption | type |
|---|---|---|---|---|---|
| x | caller-visible evidence row | 1 | tuple `(focus,target,modal,app,variation)` | frozen enumerated domains | categorical tuple |
| D(x) | typed diagnostic mode | 1 | deterministic mode classifier | 5 frozen modes | categorical scalar |
| R(m) | recovery selected from mode | 1 | frozen mode→recovery map | 4 recovery values | categorical scalar |
| A(x) | direct recovery arm | 1 | direct observable→recovery map | same 4 recovery values | categorical scalar |
| O(x) | independent oracle recovery | 1 | abnormal-set oracle | same 4 recovery values | categorical scalar |
| v | irrelevant variation index | 1 | authored observation variation | integer 0..3 | scalar integer |
| N | formal row count | 1 | `3^4 × 4` | N=324 | scalar integer |

Dimensional/unit check: every gate is categorical or a dimensionless count. No timing threshold, physical unit, or mixed-unit arithmetic participates in PASS/FAIL.

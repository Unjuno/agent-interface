# Effect-time contract generation binding v1

Decision: **RETAIN_EFFECT_TIME_GENERATION_BINDING_SCOPED**.

## Question
If a compensation contract legitimately evolves over time, may verification always use the latest contract, or must an effect be evaluated against the contract generation that was active when that effect executed?

## Container-first experiment
No repository was used as the execution environment. The experiment was constructed and frozen locally, then executed in disposable SQLite fixtures. Local freeze `01a3c2ba35fa9ed52f8046fa0e546dab610744c7`. Plan SHA-256 `e4a9eac37f04d3dfedc53f6eca033814a832af0d57adf18fb04bb94fca530648`. Source/plan exact to local freeze: True/True.

Two policies: `latest_contract` always evaluates compensation under the newest contract receipt; `effect_bound` evaluates against the newest receipt that existed before the wrong effect's journal entry. Three schedules: stable contract; a narrowing update before the effect; the same narrowing update after the effect. Every compensation restores primary=`old` but leaves collateral=`damaged`. Five repetitions per policy/schedule = 30 first outcomes.

## Results
| Policy | stable | pre-effect narrow | post-effect narrow | total |
|---|---:|---:|---:|---:|
| latest_contract | 5/5 correct | 5/5 correct | **0/5** | **10/15** |
| effect_bound | 5/5 correct | 5/5 correct | **5/5** | **15/15** |

Stable uses generation1 requiring primary+collateral, so damaged collateral means incomplete compensation. In `pre_effect_narrow`, generation2 removes collateral before the effect; both policies correctly treat the later primary restoration as complete under the contract active at effect time. In `post_effect_narrow`, generation1 governed the effect, then generation2 narrows requirements after damage. `latest_contract` retroactively reports complete 5/5; `effect_bound` retains incomplete 5/5.

The mechanism therefore permits pre-effect contract evolution while preventing post-effect semantic laundering. It does **not** authenticate who may issue a new generation.

## Verification
Independent audit reconstructs contract receipt hashes, append-only journal ordering, effect-time active generation, current state, and verdict. Formal integrity 30/30. Extraction verifies 68 files with zero mismatches; replay audit byte-identical; tests 5/5 before and after extraction. Four copied-evidence corruption controls (receipt, effect binding, outcome, state) all reject. No formal ID rerun.

## H/T/D/C/U
**H:** always using the newest contract permits a post-effect requirement change to retroactively launder a previously invalid compensation.

**T:** local SQLite state + append-only contract/effect journal; 2 policies x 3 schedules x 5 first outcomes.

**D:** RETAIN effect-time generation binding in this fixture.

**C:** some domains intentionally define current policy as retroactively governing historical classification; those require an explicit different contract.

**U:** contract updates are authored and trusted. This does not establish authorization/authentication of generation changes, distributed consensus, GUI semantics, external effects, or production ABI/performance.

## Next boundary
Who is allowed to issue a new pre-effect contract generation, and how is that authority/lineage bound? Temporal binding is solved here; authorization is not.

Raw archive `effect_contract_generation_evidence.tar.xz` — 11728 bytes — SHA-256 `86a093805093d94c6575b326e69db0983cf366d9fe379817bf96dcda5b4a0ffa`.

# First task-relevant feedback from retained MAP01 evidence

Task `MAP01-FIRST-USEFUL-FEEDBACK-POSTHOC-20260916-001`, Issue #503.

**Disposition: `SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK`.**

This is a descriptive retained-evidence posthoc. It does not rerun MAP01, call a model, emit input, or make a v38-v39 causal comparison. It asks whether the already-retained v38/v39 first outcomes are sufficient to timestamp the first decision-relevant feedback after each admitted primary plan without relabeling arbitrary viewport change as useful feedback.

## Why this rung exists

The retained control-tempo analysis established exact post-admission captures, but explicitly left semantic/task-useful feedback unverified. The project P0 still needs a useful-control measurement contract before a matched recovery experiment can claim benefit.

This rung separates three notions:

1. **viewport change** — not useful feedback by itself;
2. **state feedback** — an independently reconstructed public HUD health/ammo transition inside the admitted program envelope;
3. **stronger task-effect feedback** — a plan-bound independently scored kill/death/map-exit/progress transition with a retained timestamp.

A state transition observed after admission is not automatically caused by the action and is not automatically beneficial.

## Frozen sources and method

Publication BASE: `e2f3afadef75f8778a4e9f07b51f7c9329b23c76`.

Retained source identities:

- v38 report SHA-256 `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58`;
- v38 runtime events SHA-256 `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`;
- v39 report SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`;
- v39 runtime events SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`;
- FreeDoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

The analyzer does **not** use retained typed health/ammo values to select its measured feedback. `hud_independent.py` separately parses the hash-bound WAD digit patches and reads the exact retained PNG pixels. Retained typed values are used only as a cross-check of the independently reconstructed values.

For each `INPUT_ADMITTED` primary plan:

- bind executor admission id/accepted_ns to the retained runtime `accepted` event;
- obtain terminal_ns from the retained runtime `terminal` event for the same id;
- independently reread the admission snapshot PNG;
- scan exact observations with `accepted_ns <= capture_ns <= terminal_ns`, ordered by capture time then sequence;
- select the earliest observation whose independently reconstructed health or ammo differs from the independent baseline.

The admitted inventory was frozen before the full computation:

- v38: `plan-0-primary-0-0`;
- v39: `plan-0-primary-0-1`, `plan-3-primary-0-1`, `plan-4-primary-0-1`.

The complete retained-evidence pass was consumed once by commit `591b783c6457825ad3b507232e46ea0e5b8da314`. No retry, replacement or threshold tuning occurred.

## Construction history

Setup failures are retained rather than rewritten:

- Actions run `35112289653`: stopped before a construction result because the first analyzer incorrectly assumed every admitted lifecycle was duplicated inside the same decision's `execution_trace`. The retained runtime `accepted`/`terminal` events are the authoritative lifecycle source; no construction result was pooled from this run.
- Actions run `35112655504`: analyzer produced an excluded construction output, but the audit still used the superseded inventory function signature and stopped before audit completion. This output is not the authoritative construction result.
- Actions run `35112691129`: authoritative construction. v39 `plan-0-primary-0-1` independently reread admission health 97 / ammo 48 and selected sequence 30 as the first state feedback, 233.888977 ms after admission, ammo 48 -> 47. Audit passed and all five mutation controls were rejected.

Construction timing did not set any full-compute threshold.

## Full first outcome

GitHub Actions run `35113241046` completed the one frozen full pass. Source identity verification, exact four-program inventory check, analysis, audit, five mutation controls and artifact upload all passed.

| Run / admitted plan | Independent baseline | Exact observations in program envelope | Earliest state feedback | Stronger plan-bound task-effect feedback |
|---|---|---:|---|---|
| v38 `plan-0-primary-0-0` | health 97, ammo 48 | 2 | **none**; both observations remain 97 / 48 | none retained |
| v39 `plan-0-primary-0-1` | health 97, ammo 48 | 8 | seq 30, **233.888977 ms**, ammo 48 -> 47 | none retained |
| v39 `plan-3-primary-0-1` | health 68, ammo 44 | 2 | seq 115, **214.439344 ms**, health 68 -> 65 and ammo 44 -> 43 | none retained |
| v39 `plan-4-primary-0-1` | health 61, ammo 41 | 7 | seq 161, **191.977156 ms**, ammo 41 -> 40 | none retained |

The independent pixel/WAD reconstruction agrees with the retained typed health/ammo values on every measured frame.

### Decision

`state_feedback_all_admitted_plans = false` because the v38 admitted plan contains no health/ammo transition inside its retained program envelope.

`stronger_task_effect_all_admitted_plans = false` because both retained runs expose only a run-level `post_control_score`; they do not retain a plan-bound timestamp for kill, death, map exit or another independently scored useful effect.

Therefore the frozen decision is:

> **`SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK`**

This is a completed negative measurement result, not a reason to substitute viewport motion, terminal completion or programmed action duration as useful feedback.

## Audit and evidence retention

The frozen audit returns PASS with four admitted plans and decision `SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK`. Five direct mutations are all rejected: decision, source hash, earliest selected sequence, baseline value and unsupported stronger-effect insertion.

The exact full Actions artifact is retained byte-for-byte as four Base64 chunks:

- ZIP size 4,994 bytes;
- ZIP SHA-256 `74f38f7a9e9c567fa9a41f5ded5c169cbc1e3ca7960da467e41bd79b5e408cbd`;
- contained `result.json` SHA-256 `931f93977a6e3cf32d0529af6113b135660defb46f38c9c3185d3638a0b9369e`;
- contained `audit_result.json` SHA-256 `56503b6b544477d4b65bb8d9fabc5b8fce87ed94256c509aeec9de803607f7be`;
- contained `negative_tests.jsonl` SHA-256 `88a7239b8ee0188c5f1e63c880ca0289f965d767bde297e36237a8212e9c9bbf`.

The exact authoritative construction artifact is also retained:

- ZIP SHA-256 `4c6edaeb3a3d3084db9f4aec31423249f9c6d42d62acbe11c5ba11326962147b`.

`decode_artifacts.py` reconstructs both archives and verifies the full result/audit/negative-test member hashes. The seven artifact chunk Git blobs were read back and matched their measured-container bytes before publication closure.

## H / T / D / C / U

**H:** retained exact frames are sufficient to independently timestamp decision-relevant state feedback for every admitted plan, and possibly a stronger task effect.

**T:** one construction discriminator followed by one source-first frozen complete pass over the four retained admitted primary plans; no new live allocation.

**D:** `SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK`; v39 reconstructs state feedback in 3/3 plans, while v38 reconstructs none inside its sole admitted program envelope, and no run has plan-bound stronger task-effect timing.

**C:** health/ammo changes may be environmentally caused or harmful. A longer observation window could find later state change but would cross the frozen primary-program terminal and contaminate plan attribution with subsequent activity.

**U:** two stochastic retained episodes only; health/ammo are narrow decision-relevant signals, not a general useful-effect oracle. Run-level scorer totals do not identify when or under which plan a kill occurred.

## Architectural implication / next rung

Do **not** launch a matched recovery-benefit claim from the current retained schema. The next minimal live instrumentation rung should timestamp, in the same clock domain:

1. exact physical input occupancy/release;
2. the exact observation that first changes task-relevant public state;
3. an independently scored plan-bound useful/harmful effect transition such as kill/death/map-exit/progress where available.

Only after that measurement contract exists should a bounded recovery mechanism be compared against a matched control. Before allocating that rung, coordinate with the active occupancy lane and any newer GitHub issue to avoid duplicate formal work.

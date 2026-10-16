# Issue #8313 T0 A01 protocol

Allocation: `5947-MULTI-UPDATE-PROVENANCE-T0-A01-20261007`  
Source: `798ac5ad709168ff1d27b115f10f4f96b126bb71`  
Environment: host Python 3.14.5, standard library only; deterministic CPU fixture.  
Excluded: model/tokenizer, GUI, user data, network, live application, actions, container claim.

## H / T / D / C / U

**H:** A no-model fixture and separate raw-only auditor can establish that each matched context arm keeps task/query, baseline, final/current observation, authority, current cue byte offset, and total UTF-8 bytes fixed while only the history representation varies. Current-only and baseline-to-current queries remain present at conflict depths 0/1/4/8. A separate cue-position pair should change only cue position.

**T:** Generate four arms at each depth/query: CURRENT_ONLY, FULL_CONFLICTING_HISTORY, equal-size NONCONFLICTING_HISTORY, SOURCE_LINKED_DELTA. The context slot is fixed-width within a depth; context bytes outside that slot are identical across matched arms. Audit manifest bindings, byte hashes and lengths, current cue, task/query/state/authority equality, baseline, history schedule and source lineage, and a separate position positive control. The candidate and auditor each run once after this freeze. Four construction mutations are run before freeze; no repair or retry is permitted after formal execution begins.

**D:** `PASS_FIXTURE_METHOD_SCOPED` only if the independent auditor reports zero errors, every stratum has exactly four arms with equal lengths and cue offsets, both queries and all depths are present, source-linked deltas preserve ordered observed lineage, the separate position control moves the cue, and all four mutation controls are rejected even after the mutation manifest hashes are refreshed. Otherwise preserve FAIL/STOP and do not rerun this allocation.

**C:** Equal UTF-8 bytes and cue offset do not establish equal tokenization, visual salience, or attention. A later model may ignore the slot or current cue; admission may prevent any task effect. Synthetic fixture success does not validate the parent model hypothesis.

**U:** Authored text bytes and a synthetic oracle only. No model behavior, tokenizer equivalence, context-window effect, GUI image, accuracy, latency, task effect, adaptation, deployment, or safety result. Any T1 needs separate collision/resource/authority review and a frozen local model identity, settings, usage budget, precision/materiality thresholds, and serialized-input audit.

## Frozen construction controls

1. Change final current truth and refresh file hash: reject on current-cue truth.
2. Move current cue in one matched arm and refresh hash/offset: reject on the frozen cue position and matched-stratum rule.
3. Drop a source-linked episode without updating lineage and refresh hash: reject on expected depth/lineage.
4. Relabel an inferred delta as observed and refresh hash: reject on evidence-kind lineage.

All controls operate on temporary copies. The formal raw fixture is untouched by these tests.

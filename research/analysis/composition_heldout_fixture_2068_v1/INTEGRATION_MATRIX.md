# #2068 model-facing composition integration matrix

Status: preparation artifact only. This document is not a model, token, latency, or live-task result.

| Requirement | Existing evidence on `main` | Integrated enforcement needed | Status |
|---|---|---|---|
| Three-arm comparison | `research/analysis/composition_heldout_fixture_2068_v1/` has baseline/composed/fallbacks-disabled rows | One provider-backed runner must execute the same cases and settings in all arms | UNVERIFIED |
| Actual model accounting | Fixture `RESULT.json` records deterministic stage fields | Capture provider-reported input/output/cache/reasoning usage per attempt; missing values stay unavailable | UNVERIFIED |
| Cue affects later decision | Fixture includes `cue_ignored` and `cue_used` oracle cases | Persist cue identity and prove the next model decision differs because of it | UNVERIFIED |
| Stale/UNKNOWN safety | Fixture covers stale target, missing provenance, unknown effect, and expiry | Model-facing adapter must abstain/requery; no stale cue may authorize an action | FIXTURE PASS / LIVE UNVERIFIED |
| Raw fallback | Fixture has raw-fallback and fallback-disabled cases | Retrieve immutable raw evidence on ambiguity/exception and account the extra call/latency | FIXTURE PASS / LIVE UNVERIFIED |
| Task vs effect correctness | Fixture distinguishes `EFFECT_VERIFIED_TASK_FAILED` | Independent task/effect oracles must remain separate in live runs | FIXTURE PASS / LIVE UNVERIFIED |
| Failed calls/retries/preflight | Fixture has retry and skipped-stage fields | Include failed provider calls, retries, schema preflight, and skipped stages in the ledger | FIXTURE PASS / LIVE UNVERIFIED |
| End-to-end latency | MAP01 occupancy measures physical timing only | Measure request→decision→effect→verified completion with model wait separated | UNVERIFIED |
| Credential/provider contract | No repository Actions secret or model workflow is configured | Explicitly authorize and pin endpoint/model/settings before fresh allocation | BLOCKED AT EXECUTION GATE |

## Promotion boundary

Do not promote a composed model-facing path from the deterministic fixture. A fresh container run with an authorized provider endpoint is required. If provider usage is unavailable, record `HOLD_NO_MODEL_AUTHORITY` and retain the fixture result without pooling it with model-facing evidence.

# Construction record — Issue #3898

This bundle is an independent successor to #3873. It does not alter the predecessor's allocation, evidence, or conclusion.

## H / T / D / C / U

- **H:** On a fresh seed, the same three-arm finite task allocation may reproduce #3873's scoped correctness and efficiency result.
- **T:** One OrbStack allocation, seed `284937`, model `gpt-5.6-luna` at `low`, fixed order `plain → ephemeral → persistent`, six tasks per arm. Three schema-only preflights plus fourteen task calls; hard maximum 17 host calls, no retries.
- **D:** Retain only with 6/6 exact submissions and verified releases per arm, successful persistent repair, zero stale-target admissions, exact raw request/response/receipt/thread reconciliation, zero independent-audit errors, and persistent beating both references on cumulative input tokens and planner generations by task six with token break-even by task six. Complete audited misses are FAIL; source/runtime/provenance/audit failures are typed STOP/HOLD.
- **C:** Preserve predecessor evidence; no model/provider substitution, tuning after outcome inspection, shared-source edits, host OS input, retry, or replacement seed. Network-none containers; private deterministic Chromium fixture only.
- **U:** One replication in one synthetic task family/configuration cannot establish population, production, broad GUI-reliability, or human-speed claims.

## Construction attempts (all before formal model calls)

1. Host Python parser test stopped because host Python 3.14 lacks `jsonschema`; this says nothing about the protocol. The same parser test passed in the pinned OrbStack model-runner image (`PASS_SCHEMA_ONLY_SEPARATE_FROM_TASK_SEMANTICS`, zero model calls).
2. The fake IPC command smoke and its independent raw audit passed (`PASS_RUNNER_COMMAND_SMOKE`, zero real model/broker calls).
3. Runtime startup attempt v1 stopped because the partial checkout omitted a transitive source module. Attempt v2 preserved the traceback identifying the omitted root `research` package. Neither made a model call.
4. Attempts v3/v4 used the wrong pinned image for the Xvfb-only startup prerequisite; the model-runner image has no Xvfb. These are preserved as image-selection construction failures, not protocol failures.
5. Runtime startup attempt v5 ran in the exact pinned OrbStack outer image, network-none, read-only source mount, and passed independent audit: one observation, clean fixture finish, zero model/broker calls. Empty fixture evaluation is intentionally `success: false`; this gate proves lifecycle startup/finish only, not task success.

All original STOP artifacts are immutable. Fresh source/environment locks and evidence hashes are checked before any formal call. No formal seed-284937 output directory exists at freeze time.

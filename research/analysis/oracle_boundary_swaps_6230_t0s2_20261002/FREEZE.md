# Issue #6230 T0 successor-2 freeze — 2026-10-02

**Parent retained unchanged:** `research/analysis/oracle_boundary_swaps_6230_t0_20261002/`, package disposition `HOLD_AUDITOR_INTENT_EQUIVALENCE` (Draft PR #6279). This is a new allocation, not a repair/rerun of its consumed candidate or auditor.

## H / T / D / C / U

**H.** A raw-only auditor that independently reconstructs each arm's exact model/executed intent can distinguish the four planted diagnostic boundary classes and reject a locally consistent execution-oracle intent that differs from the matched actual arm's frozen intent.

**T.** Seven finite no-model cases × four arms. The four class-identification cases are semantic-limited, observation-limited, execution-limited and joint-only. Guard cases are ambiguous truth, answer leakage, and reset/carryover. Independent auditor carries a separate exact table and compares all row fields, including the paired actual/execution-only model-intent identity; eight mutations include changing both execution-only `model_intent` and `executed_intent` together (so local equality remains but cross-arm equality fails).

**D.** `PASS_METHOD_SCOPED` only if all 28 canonical rows exactly equal the independent raw table, execution-only intent equals the matched actual intent in all seven cases, exact execution never changes that intent, the planted 4×4 outcome patterns are present, ambiguities/leaks are uncredited, all arms have a common initial-state identity, safety is never bypassed and all eight mutations are rejected. Otherwise `FAIL_METHOD`.

**C.** Authored finite table; no stochastic model, real interface, task family or physical actuator. A PASS validates only method/accounting logic and does not rehabilitate or supersede the parent's HOLD.

**U.** Real observation sufficiency, oracle-to-deployable availability gap, adaptation, task transfer, external effect truth, reset quality and real-time control remain untested. T1 stays separately gated.

## Frozen execution contract

- Issue: `Unjuno/agent-interface#6230`; successor branch `research/oracle-boundary-swaps-6230-t0s2-20261002`.
- Base: `1885210c4e326672391743ac10e227fea0f7a36f`.
- Evidence path: `research/analysis/oracle_boundary_swaps_6230_t0s2_20261002/`.
- Source hashes (SHA-256): candidate `75697bdc09bcecb111dc09bd6fab590a6d52a5e941b42a5be1abbb384e076480`; auditor `e09532e46640c366817aefcf54936b1de14061e7c00c3ad5c223425bda1e363c`; tests `f0e6e55973ba26d02b04e140adc605ef85acd4723b3d4ec253a30d5d1b661e53`.
- CPython 3.12.10 on Windows x64; stdlib only; no model, network, GUI, game, input or external task effects.
- Candidate once; if successful, independent raw-only auditor once; retries/substitutions 0.
- Docker Desktop service is stopped and the engine unresponsive. The finite method fixture has no container-dependent semantics, so host CPU is a scoped fallback, not container evidence. Do not start/alter Docker, WSL or shared allocations.
- Construction tests before freeze are distinct from formal candidate/audit invocations. No formal raw output existed at freeze time.

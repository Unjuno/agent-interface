# #8859 trace-classification feasibility audit R01

Date: 2026-11-22. This is a read-only audit of retained evidence; no provider,
model, GUI, Docker, WSLc, or formal allocation was used.

## Frozen source packet

The sole retained positive candidate examined in detail is
[`composition-evidence-20261024-r03`](../composition-evidence-20261024-r03/README.md),
whose original result is synthetic Fake X composition only. Its packet hashes
bind LF-normalized `run/ledger/attempts.jsonl` to
`e6962ddea1a38968a354ca2a2e31c69d7d6672aacfaaa3d0e4ac1a54816ef958`; the
Windows checkout has CRLF and a different raw-byte SHA. The independent score
bytes match exactly at
`8d3e061570e62d5bc4055cc37a7e08e87f9ed47bf41ae8c01dd38b7467e95e45`.
The packet README records 2 provider attempts, 6 public MCP calls, 22 input and
8 output tokens, one completed input transition, verified release, and an
independent positive synthetic pixel score. The provider is explicitly an
injected deterministic callable, not a real provider/model; runtime
`task_success` remains null.

## Event classification against the frozen evidence/release contract

| Retained MCP call | Observed role | Classification | Reason |
|---|---|---|---|
| `observe-before-stale` | Bind initial image/scope | Required | Establishes the source identity consumed by the first plan. |
| `mint-before-stale` | Mint initial scoped alias | Required | Supplies a bounded target binding; no authority is granted. |
| `initial-compiled-call` | Returns `SAFE_YIELD/association_changed`, zero completed transitions | Required | Refuses a stale plan before input; removing it would erase the tested stale-dependency guard. |
| `recovery-window-review` | Re-observes and reviews the changed generation | Required | Establishes a fresh source/scope after the association change. |
| `mint-after-review` | Mint `field_recovered` against reviewed source | Required | Binds the follow-up target to the new scope and observation. |
| `replan-compiled-call` | One transition, `TASK_SUCCEEDED`; release verified | Required | Executes the reviewed plan and provides terminal effect evidence. |

No retained call is classifiable as redundant from this trace without
counterfactual evidence. All six are protocol-justified for the frozen stale
generation condition. The run is one successful synthetic trajectory, not a
matched pair or a set of comparable eligible alternatives.

## Feasibility decision

`CLASSIFIABLE_SINGLE_SYNTHETIC_TRACE; NO_COMPARABLE_PAIR; NO_PREFERENCE_ASSAY`.
The trace demonstrates that event-level classification is possible for one
synthetic path, but it provides no excess-work observation, real provider
accounting, human preference, or held-out task comparison. It cannot calibrate
an efficiency score or support a product efficiency claim. Other retained
positive Calc compositions were not promoted to comparators where their README
reports incomplete all-attempt usage or a synthetic provider/worker. The
current-main G10 readiness record also rejects an unmodified legacy record
without reconciled caller events and with provider usage UNKNOWN.

## Next finite gate

Wait for at least two matched, independently successful traces on the same
task/app contract with complete caller/provider-attempt usage and verified
release/effect. Then have independent annotators classify each event as
required, justified optional, redundant, or unknown before seeing comparative
outcomes. Keep unknown events unpenalized. A blinded preference assay is a
separate later gate and requires its own approved human-subject protocol.

This audit changes neither #57 nor #8859 disposition and does not spend an
allocation. Raw evidence remains in the cited source packet; this file is an
additive interpretation with direct event IDs and source hashes.

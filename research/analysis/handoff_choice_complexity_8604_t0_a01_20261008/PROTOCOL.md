# Issue #8604 T0 A01 — inert handoff-card method audit

Status at protocol freeze: pre-formal; no participant or live study authorized or performed.

## H / T / D / C / U

**H — hypothesis.** A finite card generator can vary the number of explicitly available dispositions while preserving identical request facts, evidence state, and authority semantics, and a separately authored key auditor can score only factual scope comprehension without treating a user's chosen disposition as objectively right. The stronger human-latency/comprehension transfer hypothesis is not tested here.

**T — test.** Standard-library deterministic Python on the Windows host CPU; no Docker/WSLc, human, model, network, GUI, or action dispatch. Freeze 8 vignette families × 3 matched conditions (2, 3, and 4 options) = 24 cards, each with 5 independently keyed factual questions. Conditions retain a fixed mandatory safe-stop option and the same target, operation state, completed/pending facts, evidence timestamp/scope, and authority boundary; additional options are inert inspect/wait/takeover dispositions with explicit non-authorization semantics. Compare candidate-produced cards and keys against an independently coded oracle. Run adversarial mutations for changed target/effect state, omitted pending status, authority inflation, missing safe-stop, duplicated/ambiguous option IDs, unkeyed/incorrect answers, and answer-key leakage of the preferred disposition. No fabricated reaction times or participant data.

**D — decision.** `PASS_METHOD_SCOPED` only if all 24 cards preserve the family invariants; condition option cardinality is exact; the mandatory stop option and no-dispatch boundary hold; all 120 factual key entries match the independent oracle; and all frozen mutations are rejected. `FAIL_METHOD` for any semantic drift, unsafe/authority-inflating option, incorrect or preference-scoring key. `HOLD_AUDIT` if independent reconstruction or raw custody fails. The result cannot support a claim about humans, Hick–Hyman scaling, response latency, choice overload, comprehension rates, or interface benefit.

**C — counter-hypotheses.** Holding facts fixed while varying options may still alter reading burden or framing; a syntactically valid key may omit important interpretation; the authored option set may not represent real handoff choices; safe-stop presence may make some option-count comparisons unlike the eventual interface. An exhaustive synthetic pass can be vacuous if its oracle shares the generator's assumptions.

**U — use boundary.** This is only a finite artifact/key construction-method audit. It authorizes no recruitment, collection of human data, runtime UI, approvals, actions, or product design promotion. Any participant study requires separate ethics/privacy/consent review, power analysis, and explicit authorization.

## Custody

Run construction tests before freeze. Commit sources, protocol and inputs together. From that freeze commit, invoke the candidate once and the independent auditor once; retain raw outputs, stdout, exit codes and hashes. No retries, overwrites, or post-freeze source/input changes.

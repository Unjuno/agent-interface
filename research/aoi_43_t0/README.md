# #43 AoI T0: accounting correction and scope

Date: 2026-09-30  
Disposition: **HOLD_INCOMPARABLE_DROP_ACCOUNTING / RETAIN_ORIGINAL_CONSTRUCTION_ONLY**

The retained `43-aoi-t0.py` and `43-aoi-t0.json` are unchanged historical
construction evidence. They do **not** establish a critical-drop reduction from
one queue policy to another. The two named policies implement the same queue
transitions, while their `critical_drop_count` fields count different event
classes. In particular, the reported 0.041 versus 0.001 values and the associated
approximately 97.6% reduction must not be interpreted as a policy benefit.

This additive correction does not rerun, repair or replace the consumed output.
It does not alter the older #1021/#1022 formal queue-semantics evidence.

## Exact reviewed artifacts

Source and output were read from main
`7e599018d7941730233ba1ed1328280ce068fd3f`, after
[#5461](https://github.com/Unjuno/agent-interface/pull/5461) merged at
`f6d9358ba0c72c29e8da1a4ff701891d60b9c364`.

| Artifact | Git blob | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `43-aoi-t0.py` | `a5330575a5c25a0d28a7db273d0619830a876ada` | `97f606c87216bf0c0cfde4a355b63cc0133bf7b08a305bbf88008113459cd5bf` | 1,539 |
| `43-aoi-t0.json` | `094b11e5a1035cb842cce9e549daedf313a37f29` | `fda9cdc5baf47a49a4230c96ce00b75c51ba951d670d64bc2253fa30a7db2b19` | 433 |

Both complete byte streams recreate their advertised Git blob IDs. The output's
original CRLF bytes are included in its identity. This verifies preservation,
not independent execution of the historical construction probe.

## Static equivalence and accounting defect

For the same seed, both arms initialize the same random generator and generate
the same incoming observations. Neither counter affects random draws or control
flow. Induction from the empty queue gives identical contents after each step:

1. Below capacity, both append the incoming observation
2. At capacity with a queued noncritical observation, both remove the first such
   observation and append the incoming observation
3. At capacity with only critical observations, neither removes an item; the
   common length check rejects the incoming observation in both arms
4. Both service the first queued observation at the end of each tick

Thus the retained source has identical delivered items and queue-age trajectories
for paired seeds. It does not implement a latest-only versus critical-preserving
policy comparison, despite those arm names.

The only relevant difference is in case 3: source line 12 increments the `latest`
arm's counter by `int(not item["critical"])`, whereas line 17 increments the
`critical` arm's counter by `int(item["critical"])`. The first counts rejected
noncritical arrivals; the second counts rejected critical arrivals. Their values
cannot be compared as the same critical-loss endpoint.

## What the retained output says

The JSON records 1,000 trials, horizon 200 and capacity 4. Both arms report mean
age `1.2725347524678694` and mean per-trial p95 age `2.951`; their differently
defined counters report `0.041` and `0.001`. These numbers are retained exactly.
Equal age values are consistent with the identical transition code, not evidence
of a correctness-preserving trade-off between distinct policies. The counter
comparison is non-adjudicable as a critical-retention benefit.

## H / T / D / C / U

- **H:** The published arm comparison cannot support its critical-drop benefit
  interpretation because identical transitions use inconsistent outcome labels
- **T:** Read the exact source and retained JSON; verify byte identities; compare
  every capacity/arrival/service branch analytically. No simulator, runner,
  auditor, model, GUI, container or scientific allocation was executed
- **D:** HOLD_INCOMPARABLE_DROP_ACCOUNTING; retain original construction bytes and
  withdraw the policy-benefit interpretation. This is an analytical assessment
  of the recorded comparison, not a new empirical result
- **C:** Different counter definitions alone explain the reported difference;
  no queue-policy advantage is needed to explain it
- **U:** No real planner, semantic event oracle, task effect, timing calibration,
  runtime adoption, token saving or general freshness/critical-retention benefit
  follows. A scientifically useful successor would first need genuinely distinct
  frozen policies, one common independently checked endpoint and a separately
  justified allocation. A corrected counter alone would not create two policies

## Review trail

- [Original Issue #43 T0 report](https://github.com/Unjuno/agent-interface/issues/43#issuecomment-5910402558)
- [Identical-policy and incomparable-counter finding](https://github.com/Unjuno/agent-interface/pull/5461#issuecomment-5910636050)
- [Independent counter-inversion review](https://github.com/Unjuno/agent-interface/pull/5461#pullrequestreview-5365822014)
- [Issue-level audit qualification](https://github.com/Unjuno/agent-interface/issues/43#issuecomment-5910705018)

The earlier [#1021 formal return](https://github.com/Unjuno/agent-interface/issues/43#issuecomment-5713242267)
is a separate result and is not reclassified by this correction.

# Audit note — 2026-09-27

## Reverification

The two additive translation test modules were rerun in the pinned
`linux/arm64` runtime image (`029e1867…96a093e`) with networking disabled,
read-only root, and a read-only repository mount. Result: 10/10 tests pass
(4 enriched-receipt and 6 v1 translation tests). This invocation did not rerun
the v10 refresh/final-admission suites or the generated-controller AST gate;
the earlier 19/19 + AST result remains a recorded prior result, not a fresh
full-suite CI result from this audit.

## Formal outcomes

- Seed 990639 / Issue #4536: STOP at adapter receipt schema rejection before
  policy translation. The required historical receipt was not preserved.
- Seed 990641 / Issue #4544: HOLD at the existing running-action freshness
  guard, before the policy-invalidation translator. The exact compared clock
  operands were not logged; no causal explanation is established.
- Both allocations are consumed. Neither was retried. No gameplay PASS/FAIL,
  MAP01 clear, or policy-path formal validation is claimed.

## Remaining validation boundary

The deterministic fixture uses retained calibration probes but a synthetic
missing historical invalidation timestamp. The adapter attaches a host-domain
tag to the received invalidation before translation; this audit does not
establish from a formal receipt capture that the upstream timestamp is always
host-monotonic. The formal run stopped before exercising that adapter path.
Treat the translation as an offline candidate only. A future successor should
preserve the exact incoming receipt and clock operands, explicitly validate
timestamp-domain provenance at the adapter boundary, and preregister a fresh
allocation only after those deterministic gates pass.

## Local verification command

```sh
docker run --rm --pull=never --platform linux/arm64 --network none --read-only \
  --entrypoint python3 --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -v "$PWD:/workspace:ro" -w /workspace \
  issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e \
  -B -m unittest -v \
  research.doom.map01_policy_invalidation_clock_4544_v1.test_clock_translation_v2 \
  research.doom.map01_policy_invalidation_clock_4536_v1.test_clock_translation
```

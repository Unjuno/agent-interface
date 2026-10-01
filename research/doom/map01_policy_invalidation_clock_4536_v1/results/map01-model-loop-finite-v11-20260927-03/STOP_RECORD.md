# MAP01 formal result — seed 990639

Classification: **`STOP_ADAPTER_INVALIDATION_RECEIPT_SCHEMA_REJECTION`**.
The one-time allocation was invoked once and is permanently consumed. Do not
rerun seed `990639` or this output path.

## H/T/D/C/U

- **H:** Translating the host-side invalidation timestamp with a conservative
  same-session runtime offset should avoid mixed-domain ordering errors while
  failing closed for the stale action. This allocation does not establish it.
- **T:** One pinned MAP01 model-in-loop allocation, seed `990639`, up to 24
  decisions, output directory `map01-model-loop-finite-v11-20260927-03`.
- **D:** The run stopped at the policy invalidation translation boundary with
  `ValueError: exact host-domain invalidation receipt required`. The monitor
  supplied a receipt with additional metadata beyond the helper's exact-key
  schema. Four model turns completed and a fifth was interrupted; 8 physical
  input admissions occurred. All 13 recorded owner releases (including close)
  were verified empty. No final report or score exists. The required dual-domain
  invalidation record and stale-action admission receipt were not persisted.
  This is an adapter/test-harness STOP, not gameplay FAIL and not a MAP01 clear.
- **C:** No shared runtime code was changed. The generated successor controller
  differed at the final-admission boundary only; 15/15 deterministic and
  adjacent regression tests had passed before allocation. The formal allocation
  exercised a larger, metadata-bearing monitor receipt not represented in the
  original deterministic fixture. Preserve this exact failure and all raw
  outputs. No retry.
- **U:** Exact invalidation outcome/status/timestamp, whether it was the same
  hard invalidation suspected in #4516, whether timestamp translation then
  rejects the stale action, whether a later action proceeds, and all gameplay
  outcome remain unknown.

## Raw and identity summary

- Environment: ViZDoom 1.3.0, MAP01, skill 1, ticrate 35; WAD SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Pinned image: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`.
- Runtime source manifest matched the frozen 20-file list; SHA-256
  `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.
- `runtime/events.jsonl` SHA-256
  `14b829b25e79c767fb2d1ca8912ba2eddf855f242b3dadf13652b81087effef8`.
- `planner-protocol.jsonl` SHA-256
  `5fec34cdafc597225dee2dde255f6e5789d5a1ecf4a359a84e2c04d86987ac5b`.
- `runtime/owner-events.json`: 13/13 releases verified empty. No final score.
- `runtime/policy-invalidation-clock-translations.jsonl` is absent because
  receipt validation raised before publication.
- `FORMAL_AUDIT.json` contains the full per-file SHA-256 map for retained run
  artifacts and a machine-readable event/release summary.

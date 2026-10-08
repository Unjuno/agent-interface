# Issue #5911 finite route-selector consistency T0

**Status:** pre-registered deterministic method check; no real trace or runtime
claim.

## H / T / D / C / U

- **H:** Given an explicit finite route graph, selector, and intervention on
  that same graph, `branch_change`/stationarity status must equal the change in
  the selected endpoint set. A fixed selected route admits a numeric endpoint
  delta; a changed route is nonstationary; a tied optimum is retained as an
  explicit set with no scalar delta.
- **T:** Freeze against main `8afb359a4052d0b242337965378b5917338b3267`.
  Execute five fixed cases on identical two-endpoint graphs: (1) min-cost
  model path 130 -> 80 ms vs alternate 260 ms, (2) 130 -> 210 vs 260, (3)
  130 -> 280 vs 260, (4) 130 -> 260 vs 260 exact tie, and (5) an explicit
  max-cost selector control where alternate 260 stays selected while model
  changes 130 -> 120. Candidate invocation once; then a separate exhaustive
  route enumerator/auditor once over the candidate bytes. No GPU, container,
  model, GUI, live task, networked runtime, or source/trace from the predecessor
  is used. Construction unit tests are kept distinct from the frozen candidate
  and audit invocations.
- **D:** `PASS_METHOD_SCOPED` only if the first two min-cost cases retain
  `model` with deltas -50/+80 ms, case 3 changes from `model` to `alternate`
  and withholds numeric delta, case 4 returns explicit optimum set
  `[alternate, model]` and withholds numeric delta, and the max-cost control
  retains `alternate` with delta 0. The independent enumerator must agree with
  every candidate field and the hand-calculated literal oracle; otherwise
  `FAIL_AUDIT` with the exact mismatch.
- **C:** This models two explicitly competing endpoints with additive integer
  millisecond costs and a fixed `min_cost`/`max_cost` selector. It does not
  determine whether the predecessor's 260 ms value was semantically a
  competing endpoint in a real execution trace.
- **U:** Synthetic finite-fixture consistency only. No runtime timing,
  optimization validity, causal speedup, route realism, or Agent Interface
  efficacy claim. The predecessor #5851 result and #5912/#5913 evidence remain
  unchanged.

## Frozen outcomes and process

The regression tests were written before `candidate.py`. The first test run
(`python3 -B -m unittest -v test_candidate.py`) failed all five then-existing
tests only at the explicit `candidate.evaluate must exist` assertion because
the candidate module was absent; the run exited 1. The candidate was then
implemented to those assertions. Six construction tests and one separate
max-selector construction probe pass. These construction calls are not the
one-shot candidate/raw allocation below.

Formal command pair, after `FREEZE.json` is written and verified:

```text
python3 -B candidate.py cases.json
python3 -B audit.py cases.json candidate.raw.json
```

The first stdout is the candidate raw record. It must be retained byte-for-byte
as `candidate.raw.json`; the second stdout is retained as `audit.raw.json`.
No retry, replacement, extension, or post-result source change is permitted.

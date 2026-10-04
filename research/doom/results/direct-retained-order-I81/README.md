# Direct retained-input timestamp-order guard — I81

**Disposition: `PASS_ORDERING_INVARIANT_CONSTRUCTION / HOLD_LIVE_TELEMETRY_VALIDATION`.**

## H / T / D / C / U

**H.** The direct retained-input parser should report a hold interval as measurement-ready only when all monotonic endpoints share one clock domain and satisfy `admitted_ns ≤ input_ack_ns ≤ release_call_started_ns ≤ release_call_returned_ns`. Equality is allowed because timestamp resolution may collapse adjacent calls.

**T.** Add fail-closed regressions to the current direct analyzer, first run them against the unchanged base to preserve the counterexample, then apply the guard. Run the focused suite and an independent raw-only exhaustive check over all four-timestamp sequences in `{0,1,2,3}`. No runtime/resource allocation is required for this parser invariant.

**D.** Pass construction only if valid sequences preserve the exact interval formulas and every inverted sequence returns `measurement_ready=false`, with no hold row emitted. Otherwise retain the first failure and stop this candidate.

**C.** These clocks could be incomparable if events came from different clock domains. The selected analyzer contract already subtracts admission and release timestamps, so one common monotonic domain is a prerequisite for a meaningful interval; it must be verified at the producer/source-closure gate before live use.

**U.** This checks parser arithmetic/order only. It does not establish that production events actually share a clock, that the X11 request reflects physical key-up, that a MAP01 run emits these rows, or that task feedback/recovery is useful.

## Change and results

Current main was `4ca1db66b6adcb4ea15fc3c744315ad39a87749e`. The original analyzer accepted four timestamp-order corruptions; first regression-first output is retained in `RED_BEFORE_FIX.txt`. The repair validates the complete chain before calculating bounds. Seven focused unit methods pass, including four named corruptions, exact equal-boundary admission, bool-timestamp rejection, and all 256 tuples in the small domain. A separate program (`audit_matrix.py`) reads only frozen `raw_cases.json` and `candidate_results.json`; it does not import the analyzer or candidate test module. It independently returns `PASS_ORDERING_INVARIANT`: 35 monotonic cases, 221 invalid cases, zero errors.

Final frozen construction commands from repository root:

```powershell
python -m unittest -v research.doom.test_analyze_map01_direct_retained_input_v1
python -m py_compile research/doom/analyze_map01_direct_retained_input_v1.py research/doom/test_analyze_map01_direct_retained_input_v1.py research/doom/results/direct-retained-order-I81/candidate_matrix.py research/doom/results/direct-retained-order-I81/audit_matrix.py
python research/doom/results/direct-retained-order-I81/candidate_matrix.py --output-dir $env:TEMP/direct-retained-order-I81-repro
python research/doom/results/direct-retained-order-I81/audit_matrix.py --input-dir $env:TEMP/direct-retained-order-I81-repro
git diff --check
```

Candidate and audit outputs are separate. The matrix runner refuses existing inputs/outputs and the auditor refuses an existing result. The final one-shot candidate and audit outputs are under `frozen-run/`; the earlier exploratory matrix outputs at this package root are retained separately. The original current-main source/test Git blobs are recorded in `source-baseline.json`; final tree/input/output hashes are in `FREEZE.json` and `SHA256SUMS.txt`.

No Docker/WSLc/OrbStack, X11, GUI, game, input dispatch, model/GPU, formal allocation, physical key-up, application effect, performance, or recovery experiment was run. Historical allocations and outputs remain unchanged. The existing assigned #5156 work order received the construction counterexample before this repair; the reviewable PR carries the proposed fix and evidence for integration review.

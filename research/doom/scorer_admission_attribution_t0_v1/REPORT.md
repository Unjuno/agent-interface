# Scorer admission-attribution T0 construction

## H / T / D / C / U

**H.** A positive score delta observed after recovery admission is ambiguous if the preceding scorer sample predates admission. An attribution policy should require a baseline strictly after command admission and before the first recovery input, then a bounded later positive sample; any missed polling period rejects attribution.

**T.** One deterministic CPU-only synthetic run with five frozen cases. In the ambiguity case, the same samples `(100, 0), (200, 1)` are compatible with a hidden kill at 140 (before admission at 150) or at 180 (during recovery after first input at 160). Other cases cover a valid baseline at 155 and bounded positive sample at 205, missing baseline, excessive sample gap, and a missed polling period. Threshold: maximum baseline-to-positive-sample gap 100 ns in the synthetic clock.

**D.** `run.py` produced five rows. Independent `audit.py` passed with zero errors: four co-occurrence rejections and one admission-bracketed progress classification. Six focused unit tests passed. The existing main measurement audit test suite also passed 7/7 on this head; its acceptance fixture places all scorer samples after input events and still passes, demonstrating it does not enforce the admission bracket.

**C.** Synthetic single-clock construction only. There is no game, model, live input, GPU, Docker, WSLc, or formal allocation. The outcome supports the scoring policy boundary, not runtime integration or efficacy.

**U.** `ADMISSION_BRACKETED_PROGRESS` is not exact event-time attribution or causal evidence that recovery caused progress. The bounded sample may still follow other game events. Live instrumentation must provide a same-domain mapping for admission, first input, and scorer sample times; host AppServer and guest `perf_counter_ns` values cannot be compared directly. Current-main source-07 has only a post-control refresh; the separate owner’s checkpoint draft was not modified.

## Reproduction

From the repository root:

```powershell
python research/doom/scorer_admission_attribution_t0_v1/run.py
python research/doom/scorer_admission_attribution_t0_v1/audit.py
python -m unittest discover -s research/doom/scorer_admission_attribution_t0_v1 -v
$env:PYTHONPATH='research/doom'; python -m unittest test_audit_map01_measurement_integration_v1 -v
```

The first command writes `raw.json`; the second independently checks the retained rows and writes `audit.json`. The last command checks the existing measurement audit behavior without modifying it.

## Frozen inputs and hashes

Freeze base: `48405df03913bbe94f29b2e576f7fe5532972095`. See `FREEZE.json` for the hypothesis, cases, thresholds, decision gate, clock rule, and scope limits. SHA-256 digests for the candidate, tests, runner, auditor, raw result, and audit are in `SHA256SUMS.txt`.

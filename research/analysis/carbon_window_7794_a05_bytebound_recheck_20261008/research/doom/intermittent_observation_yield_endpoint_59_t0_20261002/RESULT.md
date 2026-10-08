# Issue #6562 — capture-interval endpoint successor

## Disposition

**STOP — missing exact source-hash freeze before candidate invocation.** The candidate and raw-only auditor outputs are retained, but the auditor's internal synthetic PASS is not promoted to a formal allocation PASS. No retry or rerun is authorized or performed.

## Question and observed boundary

The preserved #6297 candidate and independent oracle disagree at the capture-interval end: at `available_at = interval_end`, the candidate returns `CONTINUE` while the oracle returns `YIELD_CAPTURE_ORDER_UNKNOWN`. They agree at the tested `end - 1` and `end + 1` neighbors. The original #6297 fixture omitted equality; its sources and outputs remain unchanged.

## Successor execution evidence

- TDD red: the frozen predecessor candidate failed the end-equality assertion (`CONTINUE` instead of `YIELD_CAPTURE_ORDER_UNKNOWN`).
- Successor construction test: one standard-library unittest passed, covering five points: 99, 100, 199, 200, 201 for interval `[100,200]`.
- Candidate invocation: one; 5 rows, 4 typed YIELD, 1 CONTINUE; zero retries. Raw output SHA-256: `dcd2cc6a4c4345aaee40f1150866feb1bce1e134721b76e14bac8a67e1a596dd`.
- Separate raw-only auditor: one invocation; 5 rows, zero errors; decision, authority, row-omission, and candidate-hash mutations all rejected. Its internal status is `PASS_SYNTHETIC_ENDPOINT_CONTRACT_SCOPED`; audit output SHA-256: `4885d8598be81448401d5689b95c9abb5fd918ed29277b2d90399d01177614b9`.
- Exact source hashes were first collected after the candidate run. This violates the required pre-candidate provenance gate and controls the overall disposition as STOP.

## H / T / D / C / U

- **H:** Under the predecessor oracle's closed-interval interpretation, either endpoint is ambiguous and must YIELD; only a strictly later availability can continue, with fresh sequence and stable health.
- **T:** Five frozen-shape integer-time cases around `[100,200]`; additive successor path; no live task or runtime. The exact sources were not hash-frozen before candidate invocation, so the formal T1 gate stopped.
- **D:** The successor construction and raw-only audit outputs are observed as above. These do not satisfy the formal gate because pre-run source identity is missing.
- **C:** Synthetic timestamps and the predecessor oracle convention only. The upstream producer may define a half-open interval; this experiment does not resolve that contract.
- **U:** No runtime deployment, input release, useful task feedback, threat survival, MAP01 progress, causal benefit, or change to #59's live gate.

## Runtime and preservation

The run used local CPython 3.14.5. WSLc is unavailable in this macOS environment; no Docker engine, GUI, game, model, or shared resource was invoked. The pure boundary function has no container-dependent behavior. All result files are additive. #6297 and #59 historical evidence is unchanged.

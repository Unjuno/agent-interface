# Coordinate-scale experiment — formal allocation 001

## Frozen protocol

This is an isolated successor to the presentation-encoding comparison in
Issue #4666. The frozen H/T/D/C/U and thresholds are in `../../PROTOCOL.md`;
the exact source, model, image, and seed allocation is in `../../FREEZE.json`.
The excluded construction pair (seed 8866620) is retained at
`../../construction/seed-8866620/` and is not included in formal scores.

## Result

Disposition: **PASS_NORMALIZED_COORDINATE_SIGNAL_SCOPED**. The independent
raw-only auditor found zero integrity errors across all 12 paired cases and
24 model calls. Both arms identified the correct target semantics in 12/12
cases. NORM01 produced in-range coordinates in 12/12 cases versus 7/12 for
PIXEL. Engine target hits were 2/12 versus 0/12. Median center error was
60.9695 px for NORM01 and 190.9034 px for PIXEL (ratio 0.3194); NORM01 had
lower paired error in 12/12 cases. All preregistered gates passed.

| Seed | PIXEL center error (px) | PIXEL in frame | PIXEL Engine hit | NORM01 center error (px) | NORM01 in frame | NORM01 Engine hit |
|---:|---:|:---:|:---:|---:|:---:|:---:|
| 8866621 | 207.93 | yes | no | 53.01 | yes | no |
| 8866622 | 232.35 | no | no | 20.41 | yes | yes |
| 8866623 | 39.86 | yes | no | 3.47 | yes | yes |
| 8866624 | 154.77 | yes | no | 65.61 | yes | no |
| 8866625 | 174.33 | yes | no | 56.33 | yes | no |
| 8866626 | 189.71 | no | no | 52.70 | yes | no |
| 8866627 | 87.05 | yes | no | 32.87 | yes | no |
| 8866628 | 265.11 | no | no | 79.44 | yes | no |
| 8866629 | 192.10 | yes | no | 81.58 | yes | no |
| 8866630 | 203.70 | no | no | 86.70 | yes | no |
| 8866631 | 259.62 | no | no | 83.60 | yes | no |
| 8866632 | 104.96 | yes | no | 89.10 | yes | no |

## Execution and audit

- Runner: pinned `linux/arm64` Python image, Docker bridge only to local Ollama;
  24/24 formal calls captured, plus one declared excluded warmup. No retries.
- Model: local `qwen2.5vl:7b`, digest
  `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.
- Freeze SHA-256: `010c7303ce8364c0ab396f6d3fc49a08cbffcfdb7c84794947f5598e9a0c575e`.
- Independent auditor: separate pinned Docker container with `--network none`,
  source/evidence read-only; result is `audit/AUDIT.json` (errors: `[]`).
- Raw prompts, request bodies, model responses, image bytes, truth, timestamps,
  and hashes are retained under `calls/`.

## Limits and interpretation

The result supports only a static coordinate-format signal for this model,
host, generator, difficulty, and twelve seeds. Both arms' exact semantic
identification was 12/12, but even NORM01 reached the benchmark's target object
only 2/12 times. This is not evidence of successful GUI control, clicking,
motion tracking, realtime behavior, full B0/C1 task effect, held-out generator
composition, or cross-domain transfer. Requests were sequential; residual
backend-load effects are possible. The paired errors and misses are reported
without clipping or exclusions.

## Reproduction

Run the isolated tests from the repository root with the three source
directories on `PYTHONPATH`; the raw audit can be repeated using the pinned
image with the evidence mounted read-only and output directed to a separate
writable directory. Do not rerun the consumed model allocation or rewrite raw
records. A follow-up should test whether this proposal-level signal survives a
properly instrumented GUI/action stage under a separately preregistered
allocation.

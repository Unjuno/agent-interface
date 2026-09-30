# Issue #5435 T4 — identity-bound alert batching under responder capacity

**Disposition: `PASS_FINITE_MODEL_GATE`; transfer to human/model/runtime alerting: `UNCERTAIN`.**

Across 24 deterministic ten-alert streams and five policies (120 traces), `SAFE_IDENTITY_BATCH` reduced published non-actionable alert deliveries from 96 to 72 (25%) versus emit-all. It recorded the same 16 unique actionable misses as emit-all, no hard-alert suppression, no hard-alert misses, and no worse hard-alert latency in every stream. The result passes the exact preregistered model gate. The stream, score, utility and responder behavior are authored; this is not evidence of human alarm fatigue or production safety.

## H/T/D/C/U

- **H:** Identity-bound duplicate batching can reduce non-actionable notification load without reducing unique actionable responses or worsening hard-alert latency under bounded responder capacity, including a held-out low-severity score shift.
- **T:** One network-disabled OrbStack Docker run over 3 arrival patterns × 2 capacities × 2 deadlines × 2 score conditions = 24 streams, each evaluated under 5 policies. Every stream contains 10 fixed alert deliveries and deterministic expiry/response behavior.
- **D:** **PASS within this finite model.** Non-actionable published alerts decreased 25% (96→72); SAFE_IDENTITY_BATCH had the same 16 unique actionable misses as emit-all, no hard-alert suppression, no hard misses and per-stream hard response latency no worse. Independent replay auditor passed all 120 traces.
- **C:** Probability-threshold and text-signature batching did not preserve all shifted low-severity actions; severity-only reduced alert count but missed more low-severity actionable entities. Emit-all remains preferable if the real responder has ample capacity or if identity is unreliable.
- **U:** Authored event identity, labels/scores, bursts, deadlines and a simple deterministic responder only. No adaptive fatigue, human, model context, calibrated alert population, live verifier, or production claim.

## Aggregate outcomes

| policy | published | served | non-actionable published | unique actionable misses | hard misses | suppressed |
|---|---:|---:|---:|---:|---:|---:|
| EMIT_ALL | 240 | 184 | 96 | 16 | 0 | 0 |
| SEVERITY_ONLY | 48 | 48 | 0 | 72 | 0 | 192 |
| PROBABILITY_THRESHOLD | 156 | 135 | 24 | 25 | 0 | 84 |
| SIGNATURE_BATCH | 180 | 152 | 48 | 25 | 0 | 60 |
| SAFE_IDENTITY_BATCH | 216 | 172 | 72 | 16 | 0 | 24 |

The score-shift subset alone shows the failure boundary: probability-threshold and signature batching each missed 17 unique actionable entities across 12 streams, compared with 8 for emit-all. Identity-bound batching also missed 8, because it keeps the first alert for each distinct entity even when the probability score shifts to 0.05. On this fixture, the maximum hard-alert response latency was zero ticks for all policies because hard events arrived on service ticks and were priority ordered.

## Frozen execution and independent audit

- Preregistration: [Issue #5435 comment 5911613008](https://github.com/Unjuno/agent-interface/issues/5435#issuecomment-5911613008).
- Frozen base: main `e7a68325c06385a8dc61d41ca33802cbe22678e4`.
- Formal candidate command: `docker run --rm --network none -v "$PWD/research/analysis/alert_actionability_5435_t4:/work" python:3.12-slim python /work/experiment.py` with stdout retained at `raw/formal.json`.
- Candidate invocations: exactly 1; exit 0; 24/24 streams and 120/120 policy traces; no RNG, retries or tuning.
- Runtime: OrbStack Docker Engine 29.4.0, linux/arm64; `python:3.12-slim`, image/repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Independent auditor replayed event tapes, retained/suppressed alerts, queue service, expiry, latency, unique-action misses and gate summary: PASS.
- Corruption controls v2 rejected 4/4 altered reports. The first mutation-control script run rejected only 3/4 because its score mutation accidentally selected a calibration-like row and rewrote 0.8 to 0.8; that test-harness failure is preserved as `raw/corruption_controls_v1.json`. The script was corrected to target a shifted row, without changing/rerunning the candidate or auditor; v2 then rejected the shifted score corruption.

## Artifact hashes

| artifact | SHA-256 |
|---|---|
| `PLAN.md` | `9681c170d1ae71bf25c1470b1cb28fe39c26b48254ea28b74e0bbd53b2c5f9cd` |
| `experiment.py` | `032bcd9988cfc64a4f1950be13204a03b2fa1e187ae0e098cf9f49aed5285ddf` |
| `audit.py` | `41c9612f0b477f0ef326b78c3a0c13ce53beedde216db6f38c5b56e563d3a97b` |
| `smoke.py` | `06b544786b7da0ac034a5b341d62b586fbc548bcca8bf607afa67bcbb1461d17` |
| `corruption_controls.py` v2 | `86c9b74be7ad6ca3d4cf9a3f919ed9e5399d2e3e40761b4405f4e31167bc3129` |
| `raw/formal.json` | `9b3226ea9e9ae4f0a062cbbcd8ace1f54e942d620da9ef05427546b788c94c93` |
| `raw/audit.json` | `2f7a8516aeea4b6fd680c71719e6a054a0a09b1c10f494daf29cdcf5038211a8` |
| `raw/corruption_controls_v1.json` | `628174ac4a4b70ee56b4539e05c1738d85725fffcc44e759df72a0920ec219f0` |
| `raw/corruption_controls.json` v2 | `dff0f3e9d0b35121873636eb33dc2ebbbbf724ca3e2a7fec997eab0719fb713e` |

## Continuation boundary

Do not rerun or retune this fixed T4 allocation. A successor may test real or independently sourced alert traces and a richer responder, but must preserve exact incident identity, score UNKNOWN, immutable raw evidence, and separate miss/burden/latency measurements. Human fatigue and model-response adaptation require their own evidence.

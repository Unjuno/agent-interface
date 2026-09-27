# Issue #4885 formal result — HOLD_AUDIT_OR_GPU

## H / T / D / C / U

- **H:** On fresh dense synthetic application screens with small repeated controls, an aligned deterministic edge view added to RAW would preserve correct target-region hits and absent-target abstentions and reduce normalized region error by at least 0.05.
- **T:** Compared the registered 10-positive/2-absent 1280x800 synthetic settings-card screens using Qwen2.5-VL 3B Q4_K_M on the RTX 3080: one RAW image versus the exact same RAW image plus aligned grayscale `FIND_EDGES` image. Prompt, decoding, seed, source screenshot and coordinate frame were fixed. The one-shot formal block made 24 calls (12 RAW, 12 EDGE); no retries.
- **D:** The frozen independent audit recorded **`HOLD_AUDIT_OR_GPU`**, with errors `["response_schema:F11:EDGE", "response_schema:F12:EDGE"]`. The gate does not permit a model-quality disposition while response-schema errors remain.
- **C:** All images are synthetic; no training, live GUI, click, user data, provider, or authority. Ollama was isolated on a dedicated internal Docker network with a read-only model store; the client was GPU-less and the auditor was networkless/CPU-only. Existing R3 Ollama was left running.
- **U:** This is one small synthetic layout family, one local Qwen model and one laptop GPU. It says nothing about real-app transfer, identity, click safety, calibration, latency benefit, or runtime/product readiness.

## Formal observation

The independent auditor saw 24/24 expected request/response records and no source, prompt, model, decoding, pairing-order, GPU-overlap, or Ollama-placement errors. The two errors were `response_schema:F11:EDGE` and `response_schema:F12:EDGE`: both EDGE responses returned `present=false` together with a non-null point (`[742,637]` and `[632,749]`). The paired RAW responses for those absent-target cases instead returned `present=true` with points, so neither representation supplied a valid exact abstention there. Per the frozen rule, these output/schema failures force HOLD; they are not repaired or retried.

Among schema-valid rows only, the scorer recorded:

| Arm | Valid positive hits | Valid absent rows / exact abstentions | Mean normalized error on positives |
|---|---:|---:|---:|
| RAW | 10/10 | 2 / 0 | 0.000000 |
| EDGE | 9/10 | 0 valid rows (both absent EDGE rows failed schema) | 0.006757 |

These are descriptive partial metrics, not an adjudication. On positive cases, EDGE missed one target rectangle (F05); its mean normalized distance was higher than RAW. No clean benefit is shown, but the predeclared output-integrity HOLD takes precedence over a FAIL or REJECT label.

## GPU evidence and cleanup

Construction audit: `CONSTRUCTION_AUDIT_PASS`, 4/4 calls, errors=[]. Formal audit: all 24 calls had Ollama GPU residency and at least one sampled GPU-memory observation above the 0 MiB baseline within the call interval. Across 586 host samples, peak GPU memory was 4491 MiB and sampled utilization peaked at 100%. Post-run evidence records the R8 container/network removed and GPU returned idle; R3 remained running.

## Reproduction and retained artifacts

Exact source/input freeze and GitHub readbacks are recorded on this Issue and in `FREEZE.json`. `results/formal/raw_calls.jsonl.gz` losslessly contains every full request (including exact image bytes), response and per-call Ollama placement receipt; the companion hash manifest gives both raw and gzip SHA-256 values. `results/formal/audit.json`, host GPU samples, construction records, console logs, pre/post environment records, all source PNGs and the independent audit source/tests are retained. The output directory is immutable for this allocation; no second inference is authorized by this record.

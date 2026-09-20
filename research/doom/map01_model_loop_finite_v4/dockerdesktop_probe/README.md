# Issue #3880 — Docker Desktop construction probe

Status: construction-only host/container clock and lease transport probe. This is **not** the preregistered OrbStack gate or the MAP01 allocation. It does not consume seed 990623.

## H / T / D / C / U

- **H:** In this Windows host + Docker Desktop linux/amd64 setup, a request/response clock-offset interval from the actual stdin/stdout transport is narrow enough to map an absolute host deadline conservatively into the mounted production `Lease` implementation's container `perf_counter_ns()` domain. The host fails closed if a delayed request has under 20 seconds of authorized time remaining.
- **T:** One short, CPU-only construction run: 41 host-send/container-receive/container-send/host-receive samples over about 1.4 s; then four JSON-line lease controls over the same Docker stdio channel: +25 s live, expired, +31 s over-horizon, and a 6 s delayed request that should be rejected by the host before transmission when its remaining lifetime falls below 20 s. The container imports the exact mounted `research/live_control/lease.py`; no duplicate validator is used.
- **D:** Construction passes only if every sample has finite ordered offset bounds; conservative mapping lets the +25 s lease pass with 20–30 s remaining at container admission; expired and +31 s controls are rejected by `Lease`; delayed control is rejected before any container request; and records prove the translated deadline never exceeds the host deadline expressed using the observed offset lower bound.
- **C:** Windows host, Docker Desktop 29.8.0, local Python 3.12 slim image on linux/amd64, network disabled, container root read-only, source mounted read-only, bounded `/tmp`, no game/model/input/GPU. This differs from Issue #3880's pinned OrbStack linux/arm64 runtime and socket transport; results cannot satisfy that gate.
- **U:** No OrbStack clock behavior, long-term drift/suspend/restart behavior, MAP01 readiness, gameplay, model, input safety, or task outcome is tested. The measured one-way latency is not independently decomposed; offset bounds use request/response timestamps. A passing construction is only justification to design and run the separately frozen OrbStack gate.

## Reproduction

From this directory in a checkout with Docker Desktop running and the selected image already cached:

```powershell
python driver.py --repo <checkout-root> --out <new-empty-output-directory> --image <local-image-id>
```

The driver creates the output directory exclusively and writes `raw.jsonl`, `result.json`, and `SHA256SUMS`. It never retries a failed invocation. Preserve a failed output as-is and classify it as STOP/HOLD; do not reuse its output path.

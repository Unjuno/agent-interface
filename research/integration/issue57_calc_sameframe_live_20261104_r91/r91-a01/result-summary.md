# R91-A01 result

## Outcome

The one registered Docker/Xvfb Calc attempt completed with Docker exit code 0. The first reviewed 1280x800 frame passed the frozen surface gate (2,125 unique RGB colors; dominant fraction 0.669220703125); no added 250ms readiness wait was needed. The task record and independent post-close verifier both report A1=731 and A2=864, with input releases confirmed. The saved FODS was independently parsed before close and its final crop matched the frozen crop exactly (0 changed pixels).

The original frozen audit reported `FAIL_OR_UNKNOWN` because Windows PowerShell wrote a UTF-8 BOM in `docker-exit-code.json`, while the audit JSON reader required plain UTF-8. This was a report-format incompatibility, not a Docker execution failure. A separate post-hoc audit copy changed only JSON decoding to `utf-8-sig` and wrote to `audit-recheck.json`; using the same pinned image offline, it returned `PASS_SCOPED`, with no failed gates and no audit errors. The original `audit.py`, `audit.json`, and audit exit record remain preserved unchanged.

## Interpretation and limits

The bounded readiness sampler passed in its first observation, so this run shows that it does not add its maximum one-second wait when the GUI is already ready. Together with the r90 refusal, this supports the value of checking the actual frame before input; a single successful r91 attempt does not estimate reliability or prove a broad improvement.

The compiled method receipt reports `SAFE_YIELD / effect_unavailable` after the Save action by design: Ctrl+S is a request whose persisted-file effect is not asserted from a GUI frame. The registered Calc path records a call-bound Save request, then the parent-held save controller accepts only the exact completed/released Save action and matching attempt/process/window generations and method-receipt hash. After neutral close and exact target exit, the parent verifier independently checks the saved FODS hash and values. R91 passed these composed handoff and verifier gates in one attempt. This is scoped evidence that the registered effect handoff worked; the `SAFE_YIELD` status alone is not an integration failure. No speedup is claimed because there is no matched conventional baseline. This does not establish WSLc, MAP01, general recovery, or product completion.

## Docker stability

Docker Desktop was already responsive before the run (Engine 29.8.1, 12 CPUs, 25,202,294,784 bytes visible memory, no running containers). Host WSL limits were 24GB RAM, 12 processors, 8GB swap, gradual memory reclaim; no stability setting was changed. The pinned container exited 0 in about 57 seconds, and the engine returned to zero running containers.

## Audit provenance

- `audit.json` is the original frozen audit result.
- `audit-recheck.py` differs from the frozen auditor only in BOM-tolerant UTF-8 JSON decoding and the output filename.
- `audit-recheck.json` is its offline result under the same pinned image and read-only/no-network audit settings.
- `docker-exit-code.json`, raw server output, source screenshots, task artifact, controller receipts, and verifier records are retained in this attempt directory.

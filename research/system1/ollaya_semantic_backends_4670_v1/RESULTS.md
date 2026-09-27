# Results — Ollaya local semantic backend comparison (#4670)

## Outcome

Neither candidate passed the preregistered acceptance gates. Decider 0.8B was more accurate and passed the changed-state gate; Laya was substantially faster on ordinary decisions and much smaller in observed RSS. Both failed mandatory abstention, total accuracy, same-state intent, warm-p95, and the overall pass condition. These synthetic results do not establish deployment readiness.

| Metric | Laya `laya:en` | Decider `decider:0.8b` | Gate |
|---|---:|---:|---:|
| Exact workflow decisions | 51/80 (63.75%) | 61/80 (76.25%) | >=72/80 |
| Required safety cases not yielding + UNSAFE | 18/24 | 11/24 | 0 |
| Same-state intent rows correct | 4/8 | 7/8 | 8/8 |
| Changed-state rows correct | 2/8 | 8/8 | >=7/8 |
| Close-choice rows correct | 8/8 | 8/8 | descriptive |
| Warm API p50 | 966 ms | 2,658 ms | descriptive |
| Warm API p95 | 9,092 ms | 21,309 ms | <=2,000 ms |
| Sampled server memory | ~3.40 GiB | peaked at sampled ~6.47 GiB | <=6 GiB |
| HTTP errors / malformed API responses | 0 / 0 | 0 / 0 | 0 / 0 |

Memory is based on periodic Docker stats samples, not a process-level peak sampler; the reported values are therefore observed sampled peaks. Decider remained below its 8-GiB container cap and did not OOM, but exceeded the preregistered 6-GiB RSS limit. All formal containers used CPU F32, 4 vCPU, 8 GiB, Docker `--network none`, read-only rootfs, and a read-only model-store mount; Docker network I/O remained 0 B.

## Diagnostic pattern

Laya's errors cluster in intent pairs (4/8), changed-state (2/8), nuisance-field and obvious CONTINUE cases; it selected YIELD/UNSAFE for only 6/24 required safety rows. Decider correctly handled all eight changed-state and close-choice rows and seven of eight intent rows, but marked only 13/24 required safety rows YIELD/UNSAFE. It returned REPAIR on six insufficient-evidence cases and failed five repeated-predicate rows. The eight-question batched predicate request was costly for both: Laya p95 was ~9–11 s; Decider requests were ~20–23 s.

## Instrumentation history / eligibility

An initial Laya attempt used `keep_alive: 0`, which caused server logs to show model reloads after each row (9–19 s); a Decider attempt was stopped before a scored row. These attempts are retained locally but are not eligible results. The final runs used an identical corrected runner with `keep_alive: -1`, separate warm-up log, server-loaded model held `Forever`, and API total/load/eval durations recorded separately. The final runs contain exactly 80 scored rows per arm, with all raw requests and responses.

One protocol issue remains: the issue's original treatment described the same serialized state/options across arms, while the final pre-run workload uses intent-specific two-label choices for the same-state intent stratum and the shared four-choice workflow labels elsewhere. This was fixed in the frozen files before the final formal runs and is reported transparently; do not reinterpret these numbers as a pure identical-option-set comparison. The stale/scope-invalid combined stratum contains four stale and four scope-invalid rows. The 24 mandatory safety cases include insufficient, conflicting, stale, and scope-invalid rows. Two extra must-yield rows in the repeated-predicate stratum count toward exact accuracy (26 must-yield total).

## Provenance

- Ollaya 0.7.2, source commit `f9e2d11fee1d01235878bfa6cfa1eb1e42bbbaea`.
- Runtime image `ghcr.io/ollaya-dev/ollaya@sha256:7765396cadaa762e1024679e63497178f012d5c8988a3337a68426a68d5c7315`.
- Python image `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9`.
- Frozen runner GitHub blob SHA `7e428e7fe1b4fbadc3743eb4d60ab61915d8b7b3`.
- Workload GitHub blob SHA `c6041a39580689b981ee2d2e5b423c9a796bb785`.
- Laya raw JSONL SHA-256 `030355a2cfae03bbf8b2a89916141ff7b64c552291116ce138cc2a3c3d0e120f` (136,371 bytes), compressed artifact `results/laya-final-formal.jsonl.gz.base64`.
- Decider raw JSONL SHA-256 `65dca82b558a41d2ae1da807066e952c7837adabf086721d11ee2f12a397f65a` (137,874 bytes), compressed artifact `results/decider-final-formal.jsonl.gz.base64`.
- To reconstruct on PowerShell: `[IO.File]::WriteAllBytes('laya.jsonl.gz',[Convert]::FromBase64String((Get-Content -Raw results/laya-final-formal.jsonl.gz.base64)))`, then `gzip -d laya.jsonl.gz`; repeat for Decider. Verify the resulting raw SHA-256 above. The compressed files are lossless gzip payloads encoded as base64 for text-only GitHub Contents API storage.

## Per-arm gate summary

Laya: total accuracy FAIL, required safety FAIL (18 mismatches), same-state intent FAIL (4/8), changed-state FAIL (2/8), warm p95 FAIL (9,092 ms), sampled RSS PASS (~3.40 GiB), valid API shape PASS, HTTP errors PASS (0). Decider: total accuracy FAIL, required safety FAIL (11 mismatches), same-state intent FAIL (7/8), changed-state PASS (8/8), warm p95 FAIL (21,309 ms), sampled RSS FAIL (~6.47 GiB), valid API shape PASS, HTTP errors PASS (0). The executable-output-zero gate is not a meaningful model comparison here: this harness deliberately attaches no executor and the native decide API returns typed answers only; no row contained an `execution` field. Safety is therefore assessed by the stricter pre-registered YIELD + evidence-safety UNSAFE gates.

## Decision

`FAIL_OLLAYA_BACKEND_ENVELOPE_SCOPED` for both arms under the preregistered gates. Do not select either as a safe autonomous action executor. Decider is a better candidate for a follow-up on changed-state/intent discrimination, but its YIELD failures, latency and memory disqualify it for the present safe semantic-decision lane. A successor should test a deterministic evidence/authority gate outside the model, small batched-question subsets or per-question routing, and a larger task-valid oracle—each as a separately preregistered study.

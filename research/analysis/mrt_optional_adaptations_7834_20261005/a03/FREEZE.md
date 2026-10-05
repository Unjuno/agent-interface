# A03 freeze

Allocation: MRT-7834-A03-20261005
Prospective freeze comment: 5986196185
Base main at freeze: 853c9bc85fb63430277e793edde108bf9f87f1d9

Candidate source (reused exact A02 blob): ae209124dc65f44dbf4291251331ca3ac589b454
Independent auditor source (reused exact A02 blob): f9dca6e630c8377c0a3213339c2bbd28777ee4e6
A03 fixture blob: 2992f2f6ff8ab8c50e4347caa9cd7f45f08ecce9
Runner blob: 3391ed768260e1d55872e8ed16d6b176dac6711a

A03 is a new WSLc container replay of the same finite construction, not a rerun of consumed A01 or A02. Fixture changes only the allocation identity. Candidate maximum=1; auditor maximum=1; retries=0.

Runtime frozen before invocation: WSLc 3.0.1.0 / WSL 3.0.1.0 / kernel 6.18.40.1; linux/amd64 image node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 (image ID sha256:7c3b093add7c43400ee83b815ab2cda98794a10045bcf76ce9bb2f89b97cbc5c); Node v22.23.3. Pull=never, network=none, CPU=1, disposable --rm, source read-only, result input read-only, output paths writable. No memory cap requested or inferred. This finite enumerator is CPU-only; GPU is not applicable.

Candidate command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a03-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a03-20261005\candidate-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 node /src/runner.js candidate

Auditor command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a03-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a03-20261005\candidate-out:/input:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a03-20261005\audit-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 node /src/runner.js audit

Disposition thresholds: PASS_METHOD_SCOPED_A03 requires exact 30-row reconstruction, eligible weight 3, proximal assignment effect matching independent oracle 1.0, separate distal -2.0, executed-only 4.0, unweighted/no-carryover 1.5, pooled no-history IPW 1.0, all four NONIDENTIFIABLE gates, and 11/11 mutation rejection. Any discrepancy is FAIL_METHOD. Environment/source/image failure before candidate is STOP_ENVIRONMENT with no retry.

Scope remains a deterministic two-type/two-session authored fixture; no empirical MRT, real interface/user/task effect, external validity, long-carryover behavior, or effective sample-size claim.
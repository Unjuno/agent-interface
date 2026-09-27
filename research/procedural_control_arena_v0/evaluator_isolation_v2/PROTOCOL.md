# Evaluator isolation v2 — durable report successor

This is a new allocation after v1 `formal/001` STOP. It does not retry, repair, or replace that result. It addresses the specific evidence-loss cause with an evaluator-only host bind for `/evidence` and a 30-second app auto-close window. The controller still has no bind mounts, source, scorer report, seed, shared PID namespace, or Docker socket. The result is a scoped single-seed isolation canary, not B0/C1 performance or a hardened hostile-X11 boundary.

## Preregistered successor allocation

- Seed 2003, difficulty 1.0, fixed clock; generator check yields first stage `target`, deadline 2.6 seconds.
- One dedicated cookie-authenticated X11 display; controller performs one `w` key-down/key-up and stores the raw XWD.
- Evaluator source remains baked into its pinned-ID image. Only the evaluator mounts the host `formal/002` evidence directory at `/evidence`; its report survives container exit. Controller has no mounts.
- Both containers use the same internal Docker network. The external auditor uses a separate pinned Python container with network disabled and read-only evidence/source mounts.

PASS requires the report, seed, target-first stage, natural `deadline_miss`, and `w` down/up ledger; valid XWD matching the probe digest; evaluator PID 1 argv with seed 2003; no seed/source/report visibility through controller process/path probes; controller unprivileged, read-only, capabilities dropped, no mounts/shared PID/socket; evaluator's only host bind is `/evidence`; internal network; and an independent raw-only audit with no errors. A confirmed leak is FAIL. Missing evidence, infra or provenance is STOP. This allocation also runs once only.

## Sequence

1. Build separate images from the exact tracked Arena v0 source and save image IDs/logs.
2. Run construction seed 2002 only to validate host-side report persistence and capture collection. It is not formal evidence.
3. Freeze all code, evidence, image IDs and the exact seed in `FREEZE.json`; commit/push and inspect the exact GitHub commit before execution.
4. Run `python run_formal.py` exactly once; `formal/002` uses exclusive directory creation.
5. Preserve the raw manifest and audit the resulting artifacts in a separate `--network none`, read-only, pinned Python container.

Base OS packages are resolved during construction; freeze the resulting image ID and never rebuild after freeze.

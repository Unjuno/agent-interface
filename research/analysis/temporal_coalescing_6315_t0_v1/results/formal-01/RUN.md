# Formal record — Issue #6315 T0 allocation 01

Status is split and explicit: candidate execution succeeded; independent audit-v1 execution succeeded but its decision logic was defective; the repaired audit-only successor independently returns `PASS_METHOD_SCOPED` for the frozen 14 case/mode rows and 4/4 mutation controls. Do **not** represent allocation-01 as an unqualified formal PASS. Candidate was not rerun. Auditor-v1 raw files remain immutable alongside the correction.

## Frozen execution environment

- Source base: `3e8a8534aadc9751600468501b71a25bc912b57e`; latest `origin/main` at freeze: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe` (ancestor of source base).
- OrbStack Docker context `orbstack`; server Docker 29.4.0, Linux aarch64, root `/var/lib/docker`.
- Image `python:3.12-slim`, ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`, pull `never`.
- Candidate limits: network none, read-only root, source/fixture bind read-only, separate writable results bind, 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. Auditor was in a second container with only auditor source, fixture, candidate raw mounted read-only and result directory writable.
- Construction tests before formal run: 3/3 pass.

## Exact candidate invocation and raw outcome

```sh
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1",dst=/src,readonly \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1/results/formal-01",dst=/out \
  --workdir /out --entrypoint python python:3.12-slim \
  /src/candidate.py /src/fixture.json /out/candidate.raw.json
```

Exit 0, stdout 0 bytes, stderr 0 bytes, raw candidate 1,093 bytes. Candidate raw SHA-256 `e8c3c30b38f5ab018c0caa272f31f3cdadc960331ba00c1adeb29cf9118f5812`.

## Auditor v1 exact invocation and audit defect

```sh
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1/audit.py",dst=/src/audit.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1/fixture.json",dst=/src/fixture.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1/results/formal-01/candidate.raw.json",dst=/src/candidate.raw.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/temporal_coalescing_6315_t0_v1/results/formal-01",dst=/out \
  --workdir /out --entrypoint python python:3.12-slim \
  /src/audit.py /src/fixture.json /src/candidate.raw.json /out/audit.raw.json
```

Exit 0, stdout 0 bytes, stderr 0 bytes, audit raw 3,032 bytes. SHA-256 `55a4f8e4e6ada61f9a9ecbb569343afb41d577ea5eb2b99602bd730c747ff809`. The raw auditor labeled the result `PASS_METHOD_SCOPED`, but review found two semantic defects: it returned `PRESERVED` if source truth and projection truth were both known and equal even when projected evidence did not retain the source witness; it also could label a known projected false as enough when source coverage was incomplete. Treat this as `HOLD_AUDIT_IMPLEMENTATION`, not formal pass. No raw file overwritten.

## Distinct audit-only successor (not a candidate rerun)

The corrected auditor preserves a separate source-truth epistemic gate and treats loss of projection evidence as `NOT_PRESERVED` only when the full source is known. Construction tests pass 3/3. Auditor v2 was run once, separately, with the same isolation settings and immutable candidate raw; exit 0, stdout/stderr empty. Its `audit-v2.raw.json` reports 14 case/mode rows, two expected `NOT_PRESERVED` witnesses (`count_drop/exact_full_stutter`, `deadline_drop/exact_full_stutter`), `UNKNOWN` on missing timestamp and incomplete coverage, preserving controls, and 4/4 rejected mutations. SHA-256 `55a4f8e4e6ada61f9a9ecbb569343afb41d577ea5eb2b99602bd730c747ff809` is recorded in `SHA256SUMS`.

Interpretation remains narrow: the corrected evaluator result is `PASS_METHOD_SCOPED` for this finite synthetic fixture; the original allocation's audit defect remains part of the evidence. There is no live GUI/capture, continuous-time guarantee, app effect, model, action-authority, privacy/safety rate, or product-benefit evidence.

# Container T1 execution record

Disposition: **`PASS_METHOD_SCOPED_CONTAINER_REPRODUCTION`**.

- Allocation: `MAP01-REJECTED-ACTION-COVER-CONTINUATION-T1-20261001-01`,
  owner-bound to local Codex task `01a0b98d-3cbf-7710-b1a4-28c16e0b49da`.
- Start: 2026-10-01 11:20 UTC; candidate started 11:21:39.087 UTC and exited
  0 at 11:21:39.253 UTC. Independent auditor started 11:22:08.887 UTC and
  exited 0 at 11:22:09.045 UTC. Candidate=1; auditor=1; retries=0.
- Current main at start: `943b3942f33b62db31d4239302aac092e6d38f47`, newer than
  the T0 source base. Frozen v39 controller SHA-256
  `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`, report
  SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`,
  and retention manifest SHA-256
  `8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2` all
  matched the frozen input identities at start.
- Runtime: Docker context `orbstack`, engine 29.4.0, Linux/aarch64; image
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
  Start-gate inventory showed no running containers and an empty dedicated
  output directory. The later #6000 reservation began at 11:35 UTC and was
  separated by the requested five-minute handoff.
- Isolation confirmed by both inspect receipts: network `none`, read-only root
  filesystem, read-only `/src`, only `/out` writable, 1 CPU, 512 MiB, 64 PIDs,
  all capabilities dropped, `no-new-privileges`. No image pull/build, network,
  model, GPU, GUI/game, OS input, or unrelated container operation.
- Candidate produced six rows, exactly byte-identical to the T0 host output
  (`b55e716a87b0bf335fbc0e58cb683b2b775dd6cfe914dbaee14212d6658d0356`).
  Auditor independently returned `PASS_METHOD_SCOPED`, six cases, zero
  mismatches, exactly byte-identical to the T0 host audit
  (`0e395dac713881e1418fe6f150eda7eaee58f074f91154d6a43a76108e6fd7a7`).
- Candidate CID:
  `a030acea04bfa5b5e91b82ca8ed04be3f19dabbcaa903e3f410c797af0d172d3`.
  Auditor CID:
  `b59b3928d463ac73133e745a12362da1021debff0989025795ebfb6c6e10e05a`.
  Both containers remain present in exited state; neither was removed.
- The 11:20–11:30 UTC CPU slot was released effective 11:22 UTC in
  [#5085 comment #5930295634](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5930295634).

This confirms one deterministic finite contract reproduction in a pinned
container. It does not add live, temporal-policy, enemy-suitability, input,
safety, liveness, survival, task-effect, or MAP01 evidence.

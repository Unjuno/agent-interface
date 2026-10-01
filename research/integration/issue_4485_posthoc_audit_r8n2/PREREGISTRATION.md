# #4485 posthoc raw audit — r8n2

## Boundary

This is a read-only, posthoc reconstruction of the already-retained seven-case
raw tree committed by #4485 at `3fd9659d0e8c15beb794f8df769ca5235e6f43e2`.
It does not rerun the broker, fake executable, frozen auditor, or any model; it
does not alter #4485's `STOP_AUDIT_IMPLEMENTATION_MISMATCH`; and it cannot
promote the original frozen D gate to a scientific PASS or FAIL.

## H / T / D / C / U

- **H:** An independently authored verifier can reconstruct the seven retained
  case records, source hashes, original audit inventory, and the original
  timeout-auditor discrepancy without executing the system under test.
- **T:** One network-none OrbStack/Linux-arm64 container invocation reads the
  pinned #4485 commit, checks the exact 50-file raw hash inventory and each
  preregistered case invariant, and emits a posthoc audit report. A separate
  construction invocation checks the read-only mounts, writable output mount,
  image/runtime identity, and all frozen `OBSTAC_*` values without auditing or
  changing the scientific raw.
- **D:** `PASS_POSTHOC_RAW_AUDIT` requires all source/freeze/raw digests to
  reconcile, all seven case records to match the retained facts, and the
  original audit's sole timeout mismatch to be independently reproduced.
  Integrity/environment mismatch is `STOP_POSTHOC_PROVENANCE`; contradictory
  retained case facts are `FAIL_POSTHOC_RAW_RECONSTRUCTION`. None changes the
  original allocation disposition, which remains
  `STOP_AUDIT_IMPLEMENTATION_MISMATCH`.
- **C:** This uses the exact retained source commit and raw bytes, a new
  stdlib-only verifier that does not import or call the frozen auditor, and a
  pinned network-none OrbStack container. The primary alternative explanation
  is changed or incomplete publication, detected through GitHub commit/tree
  readback and the original audit's frozen per-file digest inventory.
- **U:** This establishes only byte-level posthoc consistency of the retained
  records. It does not establish a formal broker-contract result under the
  original gate, model or GUI utility, desktop integration, product correctness,
  or any runtime performance claim.

## Obstac execution contract

- Docker context: `orbstack`; platform: `linux/arm64`.
- Image: `python:3.12-slim`, pinned by image ID
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Network disabled; container root read-only; `/repo`, `/study`, and `/audit`
  are read-only mounts; only a fresh dedicated `/evidence` directory is writable.
- The runner must verify `OBSTAC_SOURCE_COMMIT`, `OBSTAC_SOURCE_TREE`,
  `OBSTAC_IMAGE_ID`, `OBSTAC_FREEZE_SHA256`, `OBSTAC_DOCKER_CONTEXT`,
  `OBSTAC_PLATFORM`, and `OBSTAC_RUN_KIND` before doing work.
- Exactly one `posthoc-audit` invocation is authorized. No retry or edit of
  predecessor evidence is allowed.

## Frozen inputs

- Intake/current main: `d50eade61f9f52961b848e05fda6b25a9724e092`.
- Immutable #4485 evidence commit/tree:
  `3fd9659d0e8c15beb794f8df769ca5235e6f43e2` /
  `5e974d0f13b145ef6739ebcab6472dd713cd5016`.
- Original #4485 `FREEZE.json` SHA-256:
  `88cea8c4a8ee3b5a27a7fbe690f2d29cc5e0e547e0f5e2712491751d6645f332`.
- Original frozen auditor SHA-256:
  `5db21a108c9753bcd5c7e27e9499f94f3762a608f6761da47a8429ac44834cc4`.
- Original raw-only audit report SHA-256:
  `55c121b1cf72fe37c1a28177e9d64e4e741201da6d76b3be64576f9d3b546bf2`.
- Formal raw inventory: 50 files in the original audit manifest; the manifest
  itself is retained as the 51st file and separately hash-pinned above.
- Source broker SHA-256:
  `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`.
- Source test SHA-256:
  `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`.
- Fake executable SHA-256:
  `e6824182c55dd5dbe15024402ccd63dcaddaf4407e0634bce13e65bb98739aa0`.
- Frozen timeout fake sleep: `2.0` seconds; broker timeout: `1.0` second.

The freeze digest is computed over this file's exact committed bytes and is
passed as `OBSTAC_FREEZE_SHA256` into both construction and formal-audit
containers.

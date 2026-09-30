# Issue #5134 OrbStack boundary pilot — executed 2026-09-30

## Disposition

**`STOP_BOUNDARY_PILOT` — raw captured; independent audit exited 1. Do not
promote this to a PASS and do not rerun this pilot allocation.** The runner
completed one real OrbStack bind-mount transition and its in-place control.
The separate raw-only audit stopped on `atomic_fd_order`: `run.py` retained
each descriptor-open timestamp in `atomic.opened[]`, while `audit.py` expected
that timestamp copied into each corresponding `atomic.rows[]` item. Raw
inspection can join those records by reader/PID and shows the expected order,
but this is not a zero-error frozen audit and no patched-auditor replay was run.

This is a small construction/boundary rung, not formal allocation
`needle-publication-orbstack-bind-5066-20260928-03`. It does not meet that
allocation's 56 concurrent, 28 post, and 28 unsafe row denominators and does
not release, replace, or consume it.

## H / T / D / C / U

The preregistered H/T/D/C/U and frozen procedure are in [`PLAN.md`](PLAN.md)
and [`FREEZE.json`](FREEZE.json). In brief, H asked whether one OrbStack
bind-mounted `os.replace` returns complete old bytes through four retained
descriptors while fresh path opens see complete new bytes, and whether matched
in-place truncate/write exposes the paused strict prefix. The decision gate
required all four reader traces in both arms, exact bytes and order, and a
zero-error independent audit. C changed only the publication method. U is one
macOS host, OrbStack, pinned Linux/arm64 image, and one transition.

## Frozen execution identity

- Allocation: `needle-publication-orbstack-boundary-20260930-01`.
- Source commit/tree: `963a81e68d39b78b45e9ea7f559a292c04ddba77` /
  `01aa7786c9fa90ecf3aa95d0b65c149f28753e5e`.
- Frozen base main: `c20f55df3f3a5ca8eb2694455dc5f8ca689a878d`; the run receipt
  observed descendant main `815c7d9503b2aa48f6d0b1c1fb6d8f0fddd917ac`.
- Docker context/version: `orbstack`, `29.4.0 linux/arm64`.
- Image: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
  (`linux/arm64`).
- Container isolation: network none; read-only rootfs and source; dedicated
  writable output; 0.25 CPU, 512 MiB, 32 PIDs, 32 MiB shm, all capabilities
  dropped, no-new-privileges.
- Obstac classification: `OBSTAC_CONSTRUCTION=1`.
- Formal runner container ID
  `02dbff74f4fba5e01a8d5922dc2cfa3e1cc6145f7c2dc1c2ed8f579578b2d220`, exit 0.
- Separate auditor container ID
  `a733bb0548a7b517efc89da035a7651dcb9514b28972629480bb870067eb3a3e`, exit 1.
- Runner output: `RAW_CAPTURED`, 4 atomic readers, 4 in-place partial readers.
- Frozen auditor result: `STOP_BOUNDARY_PILOT`, sole error
  `atomic_fd_order`; counts 4 atomic, 4 unsafe partial, 4 unsafe complete.
- No retry. All formal outputs, receipts, inspect records, logs, audit inputs,
  and audit outputs are preserved under [`result/`](result/).

## Raw observation (diagnostic, not a promoted audit result)

The retained raw lists the four atomic opens separately from the four later
read rows. Matching reader IDs/PIDs, all four open timestamps precede
`replace_start_ns=161087361296750`; replacement returned at
`161087361488376`; all four held-descriptor read starts follow that return.
All held-byte SHA-256 values equal the seed bytes
`2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`; all
fresh-path values equal candidate SHA-256
`c73513e65ea4a1d144c73605c3f57116ee8eef9295790c950f610770db67bef9`.
The four paused in-place readers recorded the same strict-prefix digest
`2449675130a612dc4161ddda7a1480869ffb1b4e8dd15389d1a7bd86cf087f63`; their
complete reads after writer completion match the candidate digest. The
independent auditor did reconstruct all bytes and those other invariants, but
its missing timestamp join blocks the pilot's frozen decision gate.

## Artifact digests

All artifacts below are the byte-preserved runner output copied from the
dedicated `/tmp/unjuno-5134-orbstack-boundary-20260930-01` output directory.

- `raw.json` — SHA-256 `cd83825ee429a70aa54cfcfdd7d95ee6a9c4a114bc0966e2c808db2167f5c7bb`
- `invocation_receipt.json` — SHA-256 `b9255e7158287e038fef369d78844db8894fb462a6f26ca3c1536ef54525171a`
- `execution.json` — SHA-256 `e37aaf47f6b10f4fc3be8389430997bd8686d6b0a98c012c94fb7aa323f6212c`
- `audit-input/input_manifest.json` — SHA-256 `5d119f2e267e2e2865fa23421babe6dbca36f10c89300522ab986b2924f76da3`
- `audit-output/audit.json` — SHA-256 `d35a9f245f400714e89f2665ff214b100656ad87ebe5dcad759c1dfcc31cc13c`

The first three launcher stops occurred before output creation and before any
Docker run: a freeze seed-field mismatch, a moved main SHA, and a stale base
constant. Those launcher defects were corrected and the experiment was then
executed once. They are retained here for provenance; they are not container
experiment retries.

## Validation and limits

Local pilot CI: 4/4 tests PASS; Python compilation PASS; `git diff --check`
PASS. The tests validate the harness and seed derivation, not the measured
container behavior. The only empirical claim supported here is the recorded
single-transition observation on this host/image/path. The audit STOP means
the preregistered pilot decision is not PASS. This does not establish all
seven transitions, formal allocation -03, other filesystems/platforms, crash
durability, production safety, task/model quality, authority, or latency.

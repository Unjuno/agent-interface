# Issue #3940: independent audit of retained XDamage ordering evidence

## H — hypothesis

Independently recomputing the retained raw aggregate will confirm the directed
boundary result: `CAPTURE_THEN_CLEAR` loses the between-capture-and-clear tiny
update, while `CLEAR_THEN_CAPTURE` preserves the update in this declared X11
schedule. This audit does not rerun the consumed allocation.

## T — frozen evidence check

- Source evidence: branch
  `research/issue-3940-xdamage-order-20260922`, commit
  `3b001a30d0faa442aa5b9fd0f8cc9212b17c6a05`.
- Lossless capsule `evidence.tar.xz`, SHA-256
  `a1f90fae8fe927b14cbc708cb09035cfa17ea500935bce330058e719b7dfe51a`.
- Existing formal raw rows: 120; exact bytes 654,012; SHA-256
  `e6869cbaa74ec826ea80ebcde01e5811eadbc460f654d0f72b1dae7108687d55`.
- Independent auditor: `audit_bundle.py`; it imports neither frozen runner nor
  frozen auditor. It validates every capsule-entry byte length/hash, frozen
  schedule identity, row/trace order, monotonic gate bracket, native response
  binding, notification count, decompressed pixel length/hash, and reconstructs
  expected PPM pixels from each logged draw before recomputing the policy gate.
- Exact local command used the cached Python 3.11 slim image, Linux/amd64,
  network disabled, read-only root and bind mounts, dropped capabilities,
  no-new-privileges, 1 CPU, 512 MiB and 32 PIDs:

  ```text
  docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=32 --memory=512m --cpus=1 --mount type=bind,source=<evidence.tar.xz>,target=/evidence.tar.xz,readonly --mount type=bind,source=<audit_bundle.py>,target=/audit.py,readonly python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9 python -B /audit.py /evidence.tar.xz
  ```

## D — result

`PASS_INDEPENDENT_XDAMAGE_RAW_AGGREGATE_AUDIT`: 23/23 capsule entries match
their embedded byte counts and SHA-256 values; all 120 rows reconcile with the
frozen schedule. The independent oracle recomputed:

| Policy | Rows | False suppression | Middle/persistent loss | After-update correct | Stable/before/restore correct | Next captures | Redundant |
|---|---:|---:|---:|---:|---:|---:|---:|
| `CAPTURE_THEN_CLEAR` | 60 | 12 | 12/12 | 12/12 | 36/36 | 12 | 0 |
| `CLEAR_THEN_CAPTURE` | 60 | 0 | 0/12 | 12/12 | 36/36 | 36 | 24 |

The independently computed raw-row digest matches the one recorded in the
Issue's first-result comment. The archived owner audit also reports
`PASS_XDAMAGE_ORDER_BOUNDARY_SCOPED`, `errors=[]`, and 10/10 rejected corruption
controls; those archived mutation-control results were not independently
re-executed by this aggregate auditor.

### Evidence-replay limitation

The capsule's `files` map contains 23 materialized entries (881,875 bytes),
although its `file_count` field says 1,505. It includes aggregate `rows.jsonl`
and the frozen audit source, but not the per-case directories/files (`row.json`,
`gate.json`, native stdin/stdout/stderr and PPM sidecars) required by the frozen
auditor's `load()` routine. Running that exact frozen auditor against the
materialized capsule stops with `KeyError` during its corruption-control setup
because a per-case sidecar is absent. We did not synthesize those files or
relabel the exception as an experiment failure. Thus the aggregate scientific
result is independently recomputed here, but the original file-binding audit
is not reproducible from this capsule alone; retain that as an evidence
replayability limitation for #3940.

## C — controls and scope

No Xvfb, native process, GUI input, model/provider call, or formal allocation
was started in this audit. The compressed capsule and audit script were mounted
read-only. This is a raw-aggregate audit of the one retained private-Xvfb
allocation, not an estimate of natural race frequency and not proof of generic
desktop/rendering behavior, latency benefit, or production adoption.

## U — remaining uncertainty

The source package needs its original per-case sidecars (or a source-bound
export format that lets the frozen auditor consume the aggregate without
reconstructing receipts) for byte-level replay of the frozen file-binding and
mutation-control checks. No claim is made about XDamage beyond the declared
single-drawable schedule. Issue #3940, ROADMAP O1/O3, and the global roadmap
remain open.


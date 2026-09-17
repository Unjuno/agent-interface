# Request-origin currentness under AF_UNIX concurrent ordering — first outcome

Task: `CURRENTNESS-REQUEST-ORIGIN-AFUNIX-SHADOW-20260918-007`  
Issue: #1244  
Parents: #1126 / PR #1231 and #1234 / PR #1242  
Candidate Git blob: `3e9fc5474de9af820b653c36e5db5d912edfc076`

## Disposition

**`PASS_REQUEST_ORIGIN_AFUNIX_SHADOW_SCOPED`**

The exact request-origin currentness candidate was held byte-for-byte. This rung adds only real local AF_UNIX subprocess transport plus an independent invalidator thread, with explicit ACK/release barriers that make happens-before ordering auditable.

## Primary result

Primary invocation1, reruns0. 512 fresh cases completed, 128 per frozen stratum:

- `INVALIDATE_BEFORE_RESPONSE`: 128/128 response installs returned `STALE_RESPONSE_REFUSED`; subsequent uses were `UNKNOWN_DECISION` 128/128.
- `INVALIDATE_BEFORE_REQUEST`: 128/128 responses installed `DECISION_INSTALLED`; uses were `ADMITTED` 128/128.
- `RESPONSE_BEFORE_INVALIDATE`: 128/128 responses first installed; after invalidation, uses were `STALE_EPOCH_REFUSED` 128/128.
- `TRANSPORT_REPLAY`: first response installed128/128; retransmission was `RESPONSE_REPLAY_REFUSED`128/128; rebinds0; the originally installed decision remained admissible128/128.

Across all512 cases: candidate/oracle disposition mismatches0, timeline/happens-before violations0, exceptions0, socket parse errors0, cleanup residual processes0, response replay rebinds0, authority promotions0 and planner-generation influence0. All six planner-generation magnitudes were exercised.

Exact raw trace:512 lines /610,231 bytes, SHA-256 `3f5f4df95971947e5d3215613be80e70fffc20145068e89fef3cb05e3bab2273`.

## Independent audit and source integrity

Independent trace auditor: **PASS**, errors `[]`. All six frozen source files are SHA-256 identical before/after primary, including the exact parent candidate copy. Primary did not mutate shared runtime or any external system.

## Retained postformal audit-tooling defect

The frozen copied-result corruption wrapper evaluated eight mutations but exited its final assertion because only7/8 were rejected. The unrejected `trace_status_semantics` control was a **no-op mutation** on this formal schedule: it blindly chose trace row0, whose stratum was `INVALIDATE_BEFORE_REQUEST`, and attempted to change `install1.status` to `DECISION_INSTALLED`, which was already that exact value. Thus neither result nor trace bytes changed semantically for that control.

This is retained as a postformal audit-tooling defect; the scientific primary is not rerun or relabeled. A read-only targeted diagnostic selected the first actual `INVALIDATE_BEFORE_RESPONSE` row (index3), changed `STALE_RESPONSE_REFUSED` to `DECISION_INSTALLED`, updated only the trace digest/length metadata, and the already-frozen auditor rejected it with `candidate_oracle_mismatches`, `safety_or_integrity`, and `status_counts`. Timeline and authority mutations were also rejected by the frozen auditor. No candidate/formal source was changed.

Frozen corruption controls:7/8 rejected; targeted read-only semantic mutation: rejected. This diagnostic is evidence about the auditor, not an additional scientific primary.

## Evidence retention

The exact512-row raw trace is gzip-compressed with deterministic `mtime=0`, base64 encoded and split into reconstruction chunks. Reconstruction was checked locally byte-for-byte against the raw trace before publication. The manifest pins raw/gzip/chunk hashes.

## Interpretation / boundary

Within this directed Linux-container shadow transport, runtime-owned request-origin epochs survive actual subprocess/socket/thread composition: a response that was requested before currentness invalidation cannot be laundered merely because it arrives after invalidation; a request begun after invalidation remains usable; a decision installed before later invalidation is refused on later use; and transport replay cannot rebind the consumed request.

This does **not** estimate uncontrolled race probability or throughput and does not establish remote planner transport, process-crash recovery, Windows/macOS behavior, model/task benefit, token savings, GUI/X11/MAP01 behavior or production readiness. The next valid rung is shared-runtime shadow integration of this exact contract without granting input authority.

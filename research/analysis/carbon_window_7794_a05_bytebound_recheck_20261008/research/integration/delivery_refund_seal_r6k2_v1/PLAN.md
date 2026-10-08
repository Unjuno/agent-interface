# Terminal delivery refund boundary — #4328

Allocation: `delivery-refund-seal-20260924-r6k2`.
Base main: `46e85863a9d0bfa9f5b7648fd81f3423907ca106`.
Owned branch: `research/delivery-refund-seal-4316-20260924-r6k2`.
Owned path: `research/integration/delivery_refund_seal_r6k2_v1/`.

## H / T / D / C / U

H: a transient ABSENT read does not exclude future payload receipt. A receiver-owned serialized SEAL establishes terminal nonacceptance before reclaiming an uncertain charge. HOLD is safe but conservative; QUERY_ABSENT is the diagnostic comparator.

T: six schedules NORMAL_ACK, RECEIVED_ACK_LOST, DATA_DROPPED, DATA_DELAYED, QUERY_REPLY_LOST, FOREIGN_QUERY_REPLY; three policies HOLD, QUERY_ABSENT, SEAL_ABSENT; two repetitions, reversed policy order in repetition2.36 fresh three-process cases, six immutable six-case batches. Sender and relay stage two CUE bodies, reconcile twice, attempt another CUE and two AUTO packets, then release delayed original packets. Bodies are generated4096-byte fixed data, not GUI observations. Session budget16384 bytes, CUE budget8192; remaining8192 is reserved for AUTO. No allocation retries/replacements/exclusions/tuning.

D: all36 complete cases,108 actual actor exits0, six launcher exits0, exact bytes/identity/protocol/ledger/order reconciliation, all24 AUTO packets per policy. QUERY_ABSENT exposes exactly two DATA_DELAYED overages; candidate overages0. Candidate refunds8192 exactly once in each DATA_DROPPED/DATA_DELAYED case and accepts the extra CUE; HOLD refuses it. Already-received bodies are not refunded. Lost/foreign query replies retain charges. CANCELED identity blocks the delayed body before last-hop transmission. Independent audit errors=[]; all12 effective mutations reject without parser errors. Only then PASS_TERMINAL_DELIVERY_REFUND_BOUNDARY_SCOPED. Complete contradiction FAIL; incomplete execution/evidence/control gate HOLD/STOP. Construction results excluded, not held-out generalization.

C: SEAL is not read-only, but a cooperative receiver-state transition. It abandons the old evidence. One receiver epoch, serialization across header/body and seal, truthful identities, single budget owner, and no data retries are assumptions. A receiver that reads a canceled payload and only then discards it does not satisfy our byte accounting. A general GUI/model endpoint may lack this protocol.

U: no GUI/model/human/task input, source authentication, reboot/tombstone persistence, multi-owner transactions, power-loss, partial-body recovery, delayed-ACK repair, natural fault rates, token/energy/latency benefit or production promotion. Same-author independent code/process audit is not external human review. Timestamps are ordering diagnostics, not calibrated measurements; combined uncertainty and coverage factor are not estimated.

## Execution / preservation

Standard-library CPython in the provided Linux container. Docker/gh are unavailable. No Docker/OrbStack image-attestation claim, install or experimental internet access. AF_UNIX only. Local files belong to this allocation.

Construction attempt01 combined batches in one outer call and timed out during b2; partial bytes and missing exits remain under excluded_attempt01. Ordinary interpreter startup had site overhead; -S avoids irrelevant installed-site initialization. All subsequent stdlib actors and batch children use `python -S -B`. New construction2 namespaces, complete36-case plumbing matrix, independent audit and12 mutations precede public freeze. No old raw paths or outcomes rewritten.

After GitHub source/gate readback, run each `python -S -B launch.py formal INDEX` separately, INDEX0..5 once each. Child batch deadline30s; caller envelope40s. Stop on any incomplete batch. Do not resume it. Then `python -S -B audit.py . formal` and `python -S -B controls.py . formal checks/mutations`. Audit invocations are read-only, not scientific reruns.

Retain all raw JSONL, payloads, sender dialogue, real argv/PIDs/exits, missing/foreign delivered replies AND actual receiver replies, source hashes, construction failures. Count last-hop complete bodies, not first-link staged bytes, metadata, unique storage, model consumption or task effects.

Roadmap: intake/collision check -> predecessor read-only check -> excluded construction -> public source/gate freeze/readback -> six first-outcome process batches -> independent audit/controls -> additive full-evidence PR -> exact-head applicable CI/review -> scoped merge/readback -> supported own-branch cleanup only. #4316/global ROADMAP remain open.

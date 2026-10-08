# Archival qualification: K2M6 source and result record from Draft PR #4440

## Preservation only

This directory preserves the six exact Git blobs published by [Draft PR #4440](https://github.com/Unjuno/agent-interface/pull/4440), under parent [Issue #3880](https://github.com/Unjuno/agent-interface/issues/3880). The original records are unchanged; the separate qualification and manifest define this archive's narrower scope.

The owner reports historical outcome `PASS_LOCAL_CLOCK_ASYMMETRY_LEASE_BOUNDARY` for allocation `clock-ipc-asymmetry-k2m6-20260925-01`, alongside `HOLD_REMOTE_RAW_INCOMPLETE`. **This archive does not independently reproduce the formal raw audit.** Preserve both dispositions; do not treat this as complete evidence delivery.

## Exact originals

Source commit: `4d968ccf6d23eb13d6f2f1e950ac8e18aa43e444`\
Source branch: `research/clock-ipc-asymmetry-k2m6-20260926`\
Source subtree: `6de1b21e0e0c48ccb546d48888dfcfcb213ed6ef`\
Original denominator: **6 files, 29,842 bytes**.

Exact path, Git blob SHA-1, and byte-size identities are listed in [PRESERVATION_MANIFEST.json](PRESERVATION_MANIFEST.json). Every original was restored from the pinned source ref and compared with its recorded Git blob ID before staging. Three readable payloads (REPORT_JA.md, PROOF_JA.md, VERIFICATION.json) also reproduce their declared SHA-256 values in SHA256SUMS.txt.

## Historical outcome and delivery boundary

The owner-reported finite outcome is 24 child-process sessions / 48 unchanged `Lease.check` calls. The report states that MIDPOINT falsely accepted 2/8 actually expired checks and produced 12 positive deadline extensions, while LOWER_BOUND had 0/8 false accepts and zero extensions; both had 2/16 early refusals in the directed fixture. The report further records a 1,478-check raw-only audit, 14 units, and 12/12 effective controls. These are historical claims retained in the exact report/proof/verification blobs, **not rerun or independently confirmed from the missing raw capsule by this archive**.

The original publication record declares a 321-file canonical ZIP of 188,627 bytes, SHA-256 `a5bc2d7a11afa8097b5f0cabe2e31531d955db123a60a0a1912214f7ef3d0934`, and an additive patch with SHA-256 `40ad66dbfe05286021d55d9f61a7669473d54113709c4928b95446b760fa747f`. Neither file is in the original branch. A bounded search by name/theme and exact ZIP size in the current task, attachments, and `/tmp` found no candidate; this does not prove absence elsewhere. No archive or patch was regenerated, transcribed, or substituted.

## Do not conflate with Issue #3880's OrbStack gate

This local child-process K2M6 allocation is not the earlier OrbStack host-to-container calibration gate. The owner explicitly states it does not satisfy the OrbStack gate, replace #3886, or prove GUI/model/task or production benefit. Issue #3880 was reopened because the exact OrbStack runner, freeze/image identity, raw timestamp journal, lease receipts, and audit were not readable from main. This archive does not close that issue or combine the two allocations.

The reported experiment used a provided Linux x86_64 container and did not claim Docker/OrbStack image attestation. Its stated fixed offset and directed queue delays do not establish natural failure rates, oscillator drift, suspend/restart behavior, or model/task benefit. The 24-case allocation is already consumed and was not repeated here.

## Verification performed for this preservation

- All six original staged Git blob IDs match the pinned source ref.
- REPORT_JA.md, PROOF_JA.md, and VERIFICATION.json each match the SHA-256 entry recorded in the original SHA256SUMS.txt.
- Original PUBLICATION_STOP.json and VERIFICATION.json parse as JSON.
- The canonical ZIP and patch remain missing; therefore no 321-file extraction, raw-only re-audit, or scientific reproduction is claimed.
- No lease runner, source experiment, formal allocation, model, GUI, or container was invoked for this archival change.

## Ownership and retained gate

Keep original Draft PR #4440 open and retain `research/clock-ipc-asymmetry-k2m6-20260926`; keep Issue #3880 open. This qualified archival merge is only a durable copy of the already-published six-file record. It does not lift `HOLD_REMOTE_RAW_INCOMPLETE`, certify #3880's OrbStack gate, authorize rerunning the consumed allocation, or close any predecessor/parent track. Resume exact-byte delivery only when the original ZIP is available and its hash, manifest, extraction, and repository-only audit can be verified.

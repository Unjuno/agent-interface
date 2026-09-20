# Issue #3793 — retained delivery-byte binding audit

This is an independent audit-only allocation over the immutable Issue #3711
formal-02 evidence stored at PR #3745 head
`8bac49525c93835a69b6d441740a1c424faaecb2`. It does not run the CLI,
backend, GUI, model, or task input. It does not edit or replace any predecessor
raw, freeze, audit, or result.

## H/T/D/C/U

- **H:** The retained v2-successor audit can accept same-length mutation of
  `accepted.json` after its first 23 bytes, and can accept a shorter but still
  invalid strict prefix, because it does not bind those actual bytes/lengths
  to the producer/downstream receipts in `raw.json`.
- **T:** Retrieve the frozen evidence at the exact PR-head commit pinned in
  `MANIFEST.json`. Verify all 10 frozen input hashes, predecessor freeze
  bindings, original audit source hash, and result dispositions. Run the
  independent raw-only auditor once. Test the untouched baseline, replace the
  same-length `/out/attempt` path with `/bad/attempt` in accepted JSON, and
  truncate the 23-byte delivered prefix to 22 bytes. Write only a new
  `RESULT.json`.
- **D:** PASS only when the baseline reconstructs with zero errors, the valid
  same-length accepted mutation is rejected specifically by the raw producer
  SHA-256 receipt, and the still-strict/still-invalid 22-byte prefix is rejected
  by both the raw downstream byte-count and SHA-256 receipts. Source/image/
  mount mismatch is STOP; a baseline discrepancy or accepted mutation is FAIL.
- **C:** GitHub-hosted `ubuntu-24.04-arm` runs a digest-pinned Python 3.12
  `linux/arm64` container with `--network none --read-only`, frozen evidence
  mounted read-only, and a distinct empty output mount. The workflow downloads
  only public raw files pinned to the immutable PR-head commit before starting
  the container. Host download is staging only; audit execution is in Docker.
- **U:** Two finite evidence-integrity mutations only. This does not repeat
  Issue #3711's CLI allocation, establish OS/network truncation, or close the
  caller/exit-code integration boundary.

The workflow summary and its `RESULT.json` output are the allocation record.
No PASS is claimed until the actual Docker job completes successfully.

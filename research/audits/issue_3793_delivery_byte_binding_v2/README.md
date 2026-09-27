# Issue #3809 — byte-binding audit successor

This is a fresh allocation after the preserved one-shot STOP in v3-01.
It audits only retained Issue #3711 evidence from immutable PR #3745 head
`8bac49525c93835a69b6d441740a1c424faaecb2`. It does not rerun the CLI,
backend, GUI, model, or task input.

## H/T/D/C/U

- **H:** The retained v2-successor audit does not bind exact accepted stdout
  bytes or delivered-prefix bytes/count to the producer/downstream receipts.
- **T:** Verify the exact 10-file hash manifest and frozen predecessor
  relationships before parsing delivery semantics. Run two construction tests
  that prove any source/freeze mismatch returns STOP before baseline or
  mutations. Then run one raw-only Docker audit of the untouched baseline,
  same-length `/out/attempt`→`/bad/attempt` accepted JSON, and 23→22-byte
  delivered prefix.
- **D:** PASS only if source/image/mount identity matches; baseline has zero
  errors; the same-length valid JSON mutation is rejected by the raw producer
  SHA-256; and the shorter strict invalid prefix is rejected by raw downstream
  byte count and SHA-256. Any source mismatch is STOP before baseline and
  mutation evaluation.
- **C:** GitHub-hosted `ubuntu-24.04-arm`, pinned Python 3.12
  `linux/arm64` image, Docker `--network none --read-only`, read-only
  frozen evidence and source, unique empty writable result mount. Workflow is
  triggered only by pull-request `opened`; later result commits cannot rerun
  this allocation. Preflight unit tests do not read or mutate formal evidence.
- **U:** Two finite integrity mutations over the synthetic truncation record;
  no OS/network truncation, production reliability, or #3711 closure claim.

No outcome is claimed before the single Docker audit invocation. Preserve a
source/image/output STOP as the allocation's first and final formal result.

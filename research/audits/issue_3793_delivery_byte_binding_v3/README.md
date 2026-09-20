# Issue #3816 — byte-binding audit v3-03

This fresh allocation follows two preserved source/freeze STOPs. It audits
only immutable Issue #3711 evidence at PR #3745 head
`8bac49525c93835a69b6d441740a1c424faaecb2`; it does not rerun the CLI,
backend, GUI, model, or task input.

## H/T/D/C/U

- **H:** The retained v2-successor audit does not bind exact accepted stdout
  bytes or delivered-prefix bytes/count to their producer/downstream receipts.
- **T:** Verify all ten SHA-256 pins and all predecessor/freeze relationships,
  including full repository-path keys in the audit freeze. Construction tests
  assert correct key semantics and fail-closed early stopping. Then run the
  untouched baseline and the two preregistered byte mutations in one fresh
  Docker allocation.
- **D:** PASS only if the frozen baseline reconstructs with zero errors, a
  same-length valid accepted JSON mutation is rejected by its producer hash,
  and a 22-byte strict invalid prefix is rejected by downstream byte count and
  digest. Source/image/mount mismatch must STOP before evaluating baseline or
  mutations.
- **C:** One GitHub-hosted `ubuntu-24.04-arm` Docker run, immutable Python
  3.12 `linux/arm64` image, `--network none --read-only`, read-only
  evidence/source and unique empty output. Workflow triggers only on PR
  `opened`, preventing result commits from rerunning this allocation.
- **U:** Finite synthetic retained-byte integrity only. No OS/network
  truncation, production reliability, CLI/backend rerun, or #3711 closure.

No result is claimed before the one formal audit run.

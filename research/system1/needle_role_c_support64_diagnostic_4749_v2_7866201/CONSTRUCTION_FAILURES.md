# Construction chronology

- Attempt 1 stopped before fitting: a preflight compared GitHub's Git-blob SHA-1 (`ecd3a041...`) against a raw-file SHA-1. The hash domains differ. No source code was executed and there were zero optimizer updates.
- Attempt 2 again stopped before fitting because the locally patched copy contained one extra terminal newline; its Git blob was `ae980927...`, not the frozen upstream blob. No model operation/update occurred.
- Corrected the local source copy by removing the extra blank terminal line. `git hash-object` now exactly returns upstream blob `ecd3a0414178f38535406573314793a40b353878`.
- Subsequent offline Docker construction check passed: public runner blob identity exact; paired wrapper parses; fresh CPU tensors are 64x8 and 16x8 float32 and share an exact 16-row prefix at seed 7866201+3. Training updates: 0.

These are construction-stage provenance mistakes only. No formal result exists until `RESULT.md` is written after the one-shot run; no retry of a formal result is authorized.


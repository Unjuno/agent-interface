# Audit disposition

**PASS_AUDIT_SEAL_CORRECTION_A01.** Exact GitHub head bytes confirm the A03 v2 test digest mismatch. V3 binds the unchanged 1,212-byte test file to its actual SHA-256 and explicitly retains the incorrect V2 claim as superseded history. The V2 freeze, A03 candidate freeze, raw, and result were not edited.

The original retained audit tests pass **3/3** in WSLc; the V3 seal correction tests pass **2/2** in WSLc. Both used the pinned local Python 3.12.15 amd64 image with network disabled, one CPU, a 512 MiB memory cap, and a read-only source mount. WSL reported that swap-limit enforcement is unavailable; this is recorded in RESULT-AUDIT-V3.json.

The first four setup/test attempts stopped before a complete result and are recorded in RESULT-AUDIT-V3.json. No candidate, model, GUI, OS input, game, or live allocation was invoked. The original A03 candidate's consumed one-shot output was only read and independently re-audited.

This result resolves the exact audit-seal discrepancy only. PR #7774 still needs an updated current-main integration replay and non-author review before merge.

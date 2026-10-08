# Pre-allocation STOP event and resolution

The initial pre-allocation readback used UTF-8 display text whose line-ending/final-newline normalization made several source SHA-256 values appear inconsistent. Formal execution was paused at that point. A follow-up read fetched the exact GitHub Contents bytes as base64 and verified every frozen source and workflow SHA-256 byte-for-byte against `FREEZE.json`. The discrepancy was a display/readback artifact; the source freeze was valid before the formal allocation started.

The one formal allocation then ran exactly once in GitHub Actions run [36699576828](https://github.com/Unjuno/agent-interface/actions/runs/36699576828). Construction tests and the independent raw audit passed. The preregistered decision was **FAIL** on two of six gates; see [RESULT_REPORT.md](RESULT_REPORT.md), [DECISION.json](results/formal-01/DECISION.json), and [AUDIT.json](results/formal-01/AUDIT.json). No retry was made.

This file preserves the temporary STOP and its resolution. It does not mean the formal run never occurred, and it must not replace or obscure the retained formal FAIL.

The later RTX 3080 pilot-01 digest mismatch is a separate allocation; its evidence is under `results/gpu-pilot-01/`.

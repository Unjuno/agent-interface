# Native X11 sub-ms robustness v1 — interrupted first outcome

**Result ID:** `native-x11-subms-robustness-v1-20260916-01`  
**Source freeze:** `d38405b9763d45241155c50a0084449f4123af37`

## Disposition

**INCOMPLETE_OUTER_TIMEOUT / DO_NOT_RESUME_OR_POOL**.

The fixed 20-session schedule was interrupted by the container's 180 s outer execution limit. Five sessions completed with independent XLSX scoring; the sixth (`r02/1000us`) completed the controller and produced an XLSX but was interrupted before its scorer/report. No relevant child process survived. The result ID was not resumed or rerun.

Completed formal sessions (descriptive only; not a robustness decision):

| session | requested pacing | exact strings | eligible | measured median start |
|---|---:|---:|:---:|---:|
| r01/0800us | 0.8 ms | 7/16 | NO | 0.831 ms |
| r01/0900us | 0.9 ms | 16/16 | YES | 0.978 ms |
| r01/1000us | 1.0 ms | 16/16 | YES | 1.040 ms |
| r01/1100us | 1.1 ms | 15/16 | NO | 1.195 ms |
| r02/1100us | 1.1 ms | 16/16 | YES | 1.185 ms |

The planned 5/5 gate cannot be evaluated. These five sessions must not be pooled with a successor allocation to manufacture 5/5 evidence.

## Successor design

Keep the same four conditions and counterbalanced schedule but execute one four-session round as an independently checkpointed batch, five batches total, with a fresh result ID. Every batch gets its own output directory and completion receipt; aggregate only if all five batches complete.

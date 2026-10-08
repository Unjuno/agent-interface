# Formal diagnostic result — Issue #4853

Seed 7866401; exactly one formal invocation after zero-update construction pass. The frozen #4749 runner blob is ecd3a0414178f38535406573314793a40b353878. The pinned offline CPU Docker run completed with base immutable and updates base/B/C = 400/120/120 per C arm.

| Role | Control support16 | Treatment support64 |
|---|---:|---:|
| A | 0.9658203125 | 0.9658203125 |
| B | 0.9462890625 | 0.9462890625 |
| C | 0.908447265625 | 0.959716796875 |

Signed C delta treatment−control: +0.05126953125 (+5.13 pp). A/B exactly unchanged. Independent raw-only auditor reconstructed all six cells, rederived labels/predictions, and checked prefix, pair invariants, and delta; disposition PASS_RAW_AUDIT, errors=[].

A single synthetic seed is descriptive only. No inference about effect distribution, online real-time learning, GUI/task transfer, concurrent-update quality, natural-skill transfer, production readiness, or action authority. Does not alter #4749 or #4848.

Raw source-of-truth Docker volume: unjuno-needle-role-c-support64-diagnostic-4853-v1. Local-export SHA-256: control16 1DC71040E3E734DEE76DCCF144A4CAE88B705D0D4DE9E1EC9E959E3F80FD4FDB; treatment64 2DB2267FB4721F57177E66D039D75FA9AE86B9F294BEA75F1BCBD52D0B4C1C40; result DAE09F3704985252F8A83734EC051324D180181C4C951F58D5E721958771302A. The volume remains preserved locally.

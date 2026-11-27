# R43 result — 2026-10-24

Status: PASS_SCOPED in the independent post-hoc audit (9/9); exact fixture task success verified by the independent server-side oracle. The runner command exited 0. Raw, conditions, activation receipt, output, oracle evidence, both audit versions and source are sealed in `SHA256SUMS`.

The input-free preflight passed 10/10 checks against main `e6192a4294aac0d94d51e75b24583216c718d654`. A new fixture generation differed from R42's phase-1 generation. CUA activated the unique exact fixture; its returned window ID, fixture HWND and independently observed foreground HWND matched, and the owning process command line matched the fixture metadata.

One standard MCP dispatch completed. The fixture event/effect record exactly matched the frozen expected click, save and token text. The server-side oracle independently returned `verified` with `task_success=true` and a receipt binding the exact call ID, operation ID, new target generation and oracle ID. Runtime dispatch still reports `task_success=null`; this result supports the separate server-oracle claim. The completion release receipt was neutral with no keys/buttons down or unknown, included independent state-query witnesses, and the fixture exited 0 with foreground restored.

The original frozen R43 auditor reported 8/9 because it searched the oracle evidence file for a top-level receipt; the actual receipt is in the public `interface_verify_task` response under `task_effect.receipt`. The post-hoc v2 auditor changed only that extraction path, kept the nine frozen pass conditions, did not change raw data or rerun the experiment, and returned 9/9. Both audit outputs are retained.

R42's release-gate PASS and R43's task-oracle PASS came from separate attempt IDs and generations. Together they advance the two required properties, but they do not prove a same-attempt paired recovery/task result. They also do not establish WSLc eligibility or behavior, MAP01, broad reliability, matched efficiency, or real-application transfer.

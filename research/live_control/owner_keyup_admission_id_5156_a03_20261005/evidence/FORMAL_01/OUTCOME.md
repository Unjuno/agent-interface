# A03 formal outcome

Decision: **PASS_OWNER_ADMISSION_ID_SCOPED**. The frozen WSLc candidate ran once and exited 0; its independent auditor ran once and exited 0 with zero base errors and 12/12 corruption controls rejected.

| Case | Owner admissions | Explicit releases | Identity result |
|---|---:|---:|---|
| Single A down/up | 1 | 1 | exact owner-issued ID matched admission, release transition, and nested owner receipt |
| A+B then B+A | 2 | 2 | sequence 1 and 2 IDs matched their own keys despite reverse release order |
| C down/up twice | 2 | 2 | same-key cycles received distinct sequence 1 and 2 IDs and both matched |

The independent audit also verified the existing interleaved XTest/XSync order, caller brackets enclosing the owner KeyRelease/XSync interval, one verified neutral fake keymap per case, and false physical-verification/input-authority fields. Exact IDs, raw calls, source/image details, logs, exit codes, and hashes are retained in this directory.

This closes only the explicit identity-propagation construction rung. It does not establish live X11 or physical key-up, useful feedback, recovery, MAP01 behavior, latency, safety rate, task effect, or product readiness. It does not allocate the separately gated #59 lane.

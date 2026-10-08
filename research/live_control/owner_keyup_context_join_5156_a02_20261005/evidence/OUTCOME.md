# A02 result

`PASS_OWNER_KEYUP_CONTEXT_JOIN_SCOPED`. The one frozen WSLc candidate run exited 0 on three fake-Xlib cases, and the independent raw-only auditor exited 0 with zero base errors and 8/8 corruption controls rejected.

The exact current-main retained backend v4 carried the nested per-key owner KeyRelease/XSync receipt through its existing admission-context join. The single-key case, A+B admitted then B+A released case, and two sequential same-key cycles all retained matching `id`, `step`, admission position, key, owner ID, intent token, and caller/owner timestamp nesting. Each case preserved its expected XTest/XSync sequence and ended with verified neutral fake key state. Existing batch verification stayed true; physical verification and input-authority claims stayed false.

A01's separate frozen auditor FAIL remains retained because its expected-order builder grouped same-key cycle admissions before releases. A02 uses per-case operation sequences and does not reclassify or rerun A01.

Scope remains synthetic composition evidence. No real X server, game, GUI, OS input, useful task effect, recovery, latency, or live #59 allocation was exercised.

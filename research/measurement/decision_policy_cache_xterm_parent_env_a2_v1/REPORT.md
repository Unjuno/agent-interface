# Result — #1359 XTerm parent-environment A2

Decision: **PASS_DECISION_POLICY_CACHE_XTERM_TRANSFER_SCOPED**.

- formal invocation1; reruns/replacements/tuning0
- 24 matched pairs /48 fresh private-Xvfb+real-XTerm cases
- WAIT verified progress median **0**
- cached guarded reuse median **5** (min4,max6); cached>WAIT **24/24**
- cached accepted effects **120**
- accepted HARD effects **0**
- post-terminal commands **0**
- non-overlap ROI/oracle mismatches **0**
- progress/effect oracle exact **48/48**
- ROI guard p95 **0.227 ms**, p99 **0.377 ms**, max **1.266 ms**
- HARD invalidation→stop p95 **2.633 ms**, max **3.729 ms**
- action-start lag p95 **0.018 ms**, max **1.623 ms**
- independent audit PASS/errors[]; corruption controls **7/7**
- authority/task-input/XTEST actions **0/0/0**
- raw first-outcome SHA-256 `8f672accdfe0ee1f4388e5cb7e84373bb37cb569da892eb3b04a21dccae3fa1b`

The only successor factor relative to #1349 is parent Python DISPLAY/XAUTHORITY scope/restoration; #1349 remains a retained preformal setup stop. This fresh allocation establishes the guarded cached-policy mechanism on a real XTerm rendering surface under a private-X11 fixture. It does not establish an actual frontier-model boundary, real user desktop productivity, MAP01 completion, token savings, or production authorization semantics.

# #1449 T2 asynchronous-return authority preflight

Parent #1376; direct predecessor #1445/#1447 T1 A8 PASS.

One factor only: replace A8's fixed 40 ms handback with an independently delivered asynchronous frontier-return event. Keep the deterministic CLEAR/WATCH/HARD -> ADVANCE/WATCH/YIELD mapping and 5 ms local sampling semantics.

H: observed frontier return closes the local generation atomically; a fresh generation check at synthetic admission rejects any prepared decision crossing the return while preserving useful pre-return ADVANCE decisions.

T: standard-library container only. Excluded 4-case construction. After source freeze, one fresh formal invocation over 5 return delays x 4 state programs = 20 child-process cases. No model/provider/network/GUI/X11/task input.

D: post-return admissions0, stale-crossing probe rejected20/20, selector exact, HARD->YIELD with no later admission, pre-return value retained, child/thread cleanup clean, corruption controls pass. Formal reruns/replacements/tuning0.

C: apparent safety could be serialization rather than overlap; retain child PID/send/receive clocks and local clocks.

U: this proves only the variable-return authority adapter, not real model latency, semantic answer quality, GUI effect, or T2 end-to-end value.

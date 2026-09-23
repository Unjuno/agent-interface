# #1445 A8 formal result

Decision: **PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED**.

First/only formal supervisor invocation after eligible excluded construction and mandatory reread.

- 6 matched pairs / 12 fresh private-X11 child sessions; child exits 12/12 zero.
- formal1 / reruns0 / replacements0 / tuning0.
- candidate progress pixels 700 vs baseline0.
- candidate harm0; HARD effects0; WATCH effects0.
- selector wrong dispositions0; out-of-vocabulary0.
- ACTIVATE useful-effect latency max 2.692318ms (<12ms gate).
- HARD->YIELD latency max 1.975352ms (<10ms gate).
- TRANSIENT_8 resume-before-handback passed.
- 10/10 corruption controls hit expected failure classes.
- TRANSIENT_28 baseline: stop-set +40.171317ms, CLEAR@40 +40.331077ms.
- TRANSIENT_28 candidate: stop-set +40.124898ms, CLEAR@40 +40.260461ms.
- no send_begin >=40ms in any case; the candidate TRANSIENT_28 send began +0.267861ms.
- raw SHA-256 `cfb4f4e0f49190b18894aa6a3a09109e77ba25ac1520bab0bf951ce6f530d6b6`.
- audit SHA-256 `df55f8388a06069128de190799d182df12825f146742c8956b4ab81f6c06de7c`.

Scope remains controlled private-X11 T1 evidence. This closes the #1438/#1441 integrity/authority gap but does not itself prove a real Astra/frontier T2 call.

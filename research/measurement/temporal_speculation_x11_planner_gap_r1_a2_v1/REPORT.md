# #1200 A2 first outcome

Decision: **HOLD_NO_LIVE_LATENCY_DISCRIMINATOR**.

The detached outer transport succeeded: one formal supervisor process completed all 36 fresh private-X11/Tk sessions; formal invocation1, reruns/replacements/tuning0; parent #1191 partial rows pooled0; exceptions0.

Frozen expected local hits were WAIT0 / CURRENT6 / TEMPORAL12. Observed hits were **0 / 6 / 11**. The sole miss is `f11_temporal`: fresh future label -2 matched the prepared temporal branch, but admission returned `EXPIRED` and correctly fell back to planner. No wrong effect occurred.

The f11 witness shows an unusually long current-evidence acquisition tail: current state was applied at 6538241447170 ns and the current ROI capture ended at 6538396799053 ns (~155.35 ms later), exceeding the frozen +120 ms branch validity before the later future match. This is retained as observed; validity is not relaxed post hoc.

Latency gates otherwise separate:
- temporal future→effect median 4.1765 ms, p95 7.1269 ms;
- current mean 17.5948 ms; current−temporal mean 13.0577 ms;
- wait mean 29.1456 ms; wait−temporal mean 24.6085 ms.

Frozen auditor reports `passed=false, errors=[decision,hits]`, which is the scientific gate failure, not source substitution. Postformal source rehash is exact and no source mismatch exists. Authority/task-input actions remain zero.

Interpretation: branch semantics and planner fallback remained safe, but a current-evidence/scheduling tail can consume the entire validity budget and erase one expected local hit. A separately versioned successor may isolate current-evidence acquisition tail / validity anchoring as one factor; this allocation is never rerun or retuned.

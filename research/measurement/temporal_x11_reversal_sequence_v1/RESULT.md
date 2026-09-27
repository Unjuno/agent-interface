# X11 three-sample reversal sequence first outcome

Issue: #1335  
Task: `TEMPORAL-X11-REVERSAL-SEQUENCE-R1-20260918-010`  
Scientific decision: **HOLD_X11_SEQUENCE_RECOVERY_INSUFFICIENT**

The #1326 private-X11 centroid primitive was transferred without changing target geometry or localization. The only transfer factor is that three sequential rendered/captured samples now feed the fail-closed reversal estimator. The observation contract is the preregistered conservative ±1.0px point envelope, composed into ±2.0px displacement compatibility around nominal ±7.3px full motion.

Formal discipline: one supervisor invocation, zero reruns/replacements/tuning. 1200/1200 trajectories and3600/3600 actual XGetImage frames completed across four fresh sessions. Missed red detections0, point-envelope violations0, cleanup4/4. Frozen audit errors[]; targeted corruption controls4/4 rejected.

| reversal age | STRICT_EXACT | X11_BOUND_1PX | UNKNOWN | wrong |
|---:|---:|---:|---:|---:|
|25ms|0.00|0.15|0.85|0.00|
|50ms|0.00|0.40|0.60|0.00|
|75ms|0.00|0.65|0.35|0.00|
|100ms|0.00|0.90|0.10|0.00|
|150ms|0.00|1.00|0.00|0.00|
|200ms|0.00|0.89|0.11|0.00|

PASS required candidate accuracy>=0.95 at100/150/200ms. The100 and200ms gates miss. Safety does not: wrong-direction is zero at every age and all3600 captured points remain inside ±1.0px. Therefore the retained first outcome is HOLD, not PASS and not a safety FAIL.

Read-only boundary localization finds all100ms UNKNOWNs at phases90..99ms and all200ms UNKNOWNs at phases0..10ms. This is structured sampling-boundary uncertainty, not broad random degradation. The conservative ±2.0px displacement band was derived from independent point bounds; predecessor #1326 directly measured full-step displacement residual max0.700px. That suggests a distinct fresh successor may test the **bound representation** (point-composed versus directly measured displacement envelope) while keeping sequence, estimator and gates fixed. This allocation is not retuned.

Median one-scanline XGetImage acquisition was37.231µs, descriptive only. Sequence samples were geometry-equivalent to100ms intervals and were not wall-clock spaced, so no10Hz scheduler/capture latency claim follows.

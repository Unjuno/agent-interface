# #1601 XTerm termination-tail A4 formal result

Decision: **PASS_XTERM_NATIVE_EXIT_TAIL_LOCALIZED_A4_SCOPED**.

Fresh A4 changed only the outer execution envelope from the consumed #1584 stop: 120 s instead of45 s. The Xlib-capable interpreter, XTerm/Openbox fixture, fixed ROI, scientific harness, thresholds and 64-session corpus semantics remained frozen. No #1563/#1584 scientific row was pooled.

## Formal result

- formal invocation: **1**; reruns/replacements/tuning: **0/0/0**
- sessions: **64/64**
- correctness/marker/ROI/reconstruction errors: **0**
- effect -> child-ready: p50 **20.598164 ms**, p95 **21.037592 ms**, max **23.576343 ms**
- child-ready -> native XTerm exit: p50 **164.064920 ms**, p95 **214.750334 ms**, max **264.337248 ms**
- native-exit p95-p50 spread: **50.685414 ms**
- maximum decomposition reconstruction error: **0 ns**

The frozen gates therefore pass: authored effect->child-ready p95 is below30 ms; native exit p50 exceeds100 ms; native-exit p95-p50 spread exceeds40 ms; native-exit p50/p95 both exceed the authored child interval.

Independent audit returns the same PASS with errors[]; corruption controls reject4/4 score/ROI/marker/reconstruction mutations. Postformal source hashes match8/8. Residual Xvfb/Openbox/XTerm/decompose processes are0.

## Interpretation

For this private XTerm/Openbox fixture, the dominant measured terminal tail is after the fixture child has declared readiness and before native XTerm process exit. This explains why reducing image acquisition alone did not remove the controller-wall tail in the parent lineage. It supports excluding per-action native process teardown from latency-sensitive benchmark endpoints or measuring it separately.

Scope remains narrow: this does not identify the internal XTerm/kernel cause, prove a production runtime speedup, or generalize to other applications.

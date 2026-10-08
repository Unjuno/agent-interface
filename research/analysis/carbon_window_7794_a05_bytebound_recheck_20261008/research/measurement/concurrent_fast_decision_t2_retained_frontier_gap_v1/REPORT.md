# #1451 retained frontier-gap eligibility

Decision: **PASS_RETAINED_FRONTIER_GAP_ELIGIBLE_SCOPED**.

One source-first container analysis invocation; reruns0. Independent audit PASS/errors[]; three corruption controls detected.

Ten exact retained `fixed-astra-control/model-1-stdout.txt` Git blobs from OpenTTD timing-envelope runs l-02..l-11 were analyzed.

- start→exit: min **10,428.0873 ms**, median **13,222.5624 ms**, p95 **15,802.07583 ms**, max **15,974.4855 ms**.
- stdin-close→exit: min **9,989.1436 ms**, median **13,094.7407 ms**, p95 **15,438.66979 ms**, max **15,521.6686 ms**.
- shortest retained post-stdin interval / frozen T1 12 ms deadline = **832.43×**.
- shortest retained post-stdin interval / #1445 max useful-effect latency2.692318 ms = **3710.24×**.
- exit_code0 and requested route `gpt-6-astra` / `medium`:10/10.

Important limitation: all ten records have `observed_model_identity=null` and `cost=null`. This result therefore characterizes historical real model-subprocess intervals for the requested route; it does **not** independently verify the served model identity and is **not** a real-frontier T2 execution.

This closes only the historical `HOLD_NO_REALTIME_GAP` concern for this retained sample. Next informative allocation is a separately preregistered T2 run that executes the already-passed bounded lane during one actual frontier subprocess request and uses the observed subprocess return as the authority-close event.

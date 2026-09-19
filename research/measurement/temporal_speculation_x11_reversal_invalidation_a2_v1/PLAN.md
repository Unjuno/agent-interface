# #1215 A2 fresh detached-supervisor X11 reversal invalidation

Scientific contract is inherited unchanged from #1204. Predecessor partial rows are pooled0.

Only changes: fresh task/session/display identity and outer execution transport. The scientific runner is launched exactly once as a detached process; later calls poll only the same PID/result/status.

Frozen science: private Xvfb/Tk 320x240; full-frame 20 Hz; TTL200 ms; reversal offsets {5,15,25,35,45} ms x both directions x2; 20 reversal sessions +10 continuation controls; guard input only {capture_finished_ns, red_centroid_x}.

PASS gates: reversal detect20/20; false invalidation0/10; exceptions0; reversal->YIELD p95<=110 ms/max<=140 ms; median stale-exposure reduction>=75 ms; authority/input0; invocation1/reruns0.

No cadence/TTL/threshold/guard changes after source freeze.

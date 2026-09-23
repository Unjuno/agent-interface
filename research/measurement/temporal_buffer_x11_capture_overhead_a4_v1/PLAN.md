# X11 Continuous Temporal Capture Overhead

TASK: TEMPORAL-BUFFER-X11-CAPTURE-OVERHEAD-20260918-004
PARENT: #1028 / #1038
BASE: f596f106a91b510053126f9986ee59a7ed605cf9
PREDECESSORS: #1045 A1 STOP; #1053 A2 STOP; #1057 A3 HOLD

H: with the same private Xvfb/Tk animated fixture, adding only 20 Hz full-frame XGetImage plus a 500 ms bounded raw ring does not materially perturb fixture cadence and stays within frozen CPU/capture-latency/memory bounds.

T: fresh Xvfb+Tk per arm; 320x240; callback 16 ms; capture period50 ms; warmup300 ms; measured1500 ms; six counterbalanced matched pairs; one supervisor invocation; no XTest/input/model/network/shared runtime. Excluded construction used one shorter pair only.

D: geometry exact; >=25 captures/arm; zero capture exceptions; <=1 dropped slot/arm; capture p95<10 ms; candidate process CPU fraction<0.20 each; ring <=12x frame bytes; paired median callback-count ratio in[0.97,1.03]; paired median p95-gap increase<=2ms; no candidate max gap exceeds matched baseline max by>10ms. HOLD if baseline max gap>100ms in >=2 baseline arms. Reruns0.

C: Xvfb/raw XGetImage can be cheaper than real compositor+encoding; production SHM/Damage may also be cheaper. 320x240 does not establish high-DPI/full-screen cost.

U: Linux/Xvfb/python-xlib/Tk only; no model/task/privacy/MAP01/human-tempo claim.

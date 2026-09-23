# X11 Temporal Capture Cadence 10 Hz

TASK: TEMPORAL-BUFFER-X11-CAPTURE-CADENCE10-20260918-005
PARENT: #1028; predecessor #1061 REJECT_CONTINUOUS_CAPTURE_COST
BASE: a630412e2cffbee838b19e77760e579218dd553d

H: holding private Xvfb/Tk320x240, raw XGetImage,500ms ring and matched fixture fixed, halving capture cadence20Hz->10Hz removes the retained overhead-gate failure.
T: baseline no capture versus10Hz candidate,300ms warmup,1500ms measured, six fresh counterbalanced pairs, one detached supervisor invocation, fresh displays, no predecessor pooling.
D: capture>=13/arm; exceptions0; drops<=1; p95<10ms; CPU<0.20; ring<=7x frame; paired count ratio p50[0.97,1.03]; paired p95-gap increase<=2ms; per-pair max-gap excess<=10ms; HOLD if >=2 baseline max gaps>100ms. Reruns0.
C: lower cadence can pass by sacrificing temporal resolution; this tests overhead feasibility only.
U: Linux/Xvfb/python-xlib/Tk only; no model/task/privacy/high-DPI/compositor claim.

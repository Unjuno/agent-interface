# TEMPORAL-RING-X11-LIVEONLY-RUNG1-20260918-008
BASE=b6b716963fa1559f375d516180dcae8128807ca5
PARENT_A7_MERGE=b6b716963fa1559f375d516180dcae8128807ca5
PARENT_RUNG1_MERGE=c27d529ed7186d028071380a12f6bfff7cd1cbd7
ROI=[80,60,160,120]
PERIOD_MS=50
RING_AGE_MS=500
REQUEST_OFFSETS_MS=[-150,-50]
JIT_EQUIVALENT_SPAN_MS=100

H: on the same A7 real X11 live-only ROI source, already-retained ring history returns a requested two-frame100ms span without a new acquisition boundary, while JIT without replay must wait for a future-equivalent100ms span; evidence roles remain explicit and authority=false.
T: excluded one-pair construction only before source freeze. Formal six fresh counterbalanced pairs, four requests/arm/pair=24/arm, exact A7 ROI/XGetImage/payload normalization,20Hz/500ms ring, ring warmup400ms; JIT captures current and >=95ms-later future frame. One detached supervisor, reruns/replacements/tuning0.
D: PASS iff24/24 ring selections are two distinct strictly historical frames within35ms of requested offsets,24/24 JIT trials report exact-past unavailable and future-equivalent span>=95ms, ring p95<5ms, JIT median>=90ms, paired median delta>=85ms, boundaries ring0/JIT24, authority0, capture/source integrity pass.
C: replay-capable backends erase this structural advantage; this is acquisition latency, not task/model value.
U: private Xvfb/Tk fixed ROI only; no model, task correctness, real compositor, dynamic ROI or token claim.

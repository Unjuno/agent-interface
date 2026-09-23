# TEMPORAL-BUFFER-X11-ROI-CAPTURE-OVERHEAD-20260918-006
BASE=3c34e3cea2a39e961e097b41444ff4a7563a4170
PARENT_A4_ISSUE=1061
PARENT_A4_RUNNER_BLOB=c2fe5afbe7a7ef87bd40128653bc98ac0cfe61cb
PARENT_A4_FIXTURE_BLOB=0843f29618b0aa9010b22789f56d248bbeb8f7a4

H: keeping A4 20 Hz/raw-XGetImage/ring/fixture semantics fixed while changing only capture extent from 320x240 to centered 160x120 ROI will satisfy the frozen A4 capture/CPU/fixture-perturbation gates.
T: excluded one-pair construction only before source freeze. Formal is exactly six fresh counterbalanced pairs, 300 ms warmup +1500 ms measurement, private Xvfb/Tk, 20 Hz ROI XGetImage, 500 ms bounded raw ring, one detached supervisor process, reruns/replacements/tuning0.
D: PASS_X11_TEMPORAL_ROI_CAPTURE_OVERHEAD_SCOPED iff all inherited A4 gates pass plus every candidate reports capture_region [80,60,160,120]; REJECT_ROI_CAPTURE_COST for stable-baseline capture/CPU/callback gate failure; HOLD_HOST_SCHEDULING_NOISE if >=2 baseline arms exceed 100 ms max gap; region/source mismatch FAIL_INTEGRITY.
C: any improvement may be pixel-count scaling only and does not establish dynamic ROI discovery/Damage capture/model utility.
U: Linux/Xvfb/python-xlib/Tk 320x240 fixture only; fixed ROI may omit relevant content; no real desktop/privacy/model/task/token claim.

# TEMPORAL-BUFFER-X11-ROI-PAYLOAD-NORMALIZATION-20260918-007
BASE=544d93fd9c6a17815e9a11c1344acba151474db9
PARENT_A6_MERGE=544d93fd9c6a17815e9a11c1344acba151474db9
PARENT_A6_RESULT_BLOB=c04fbce7c2685b35daa7dd8b8ccf22362f1369ee
ROI=[80,60,160,120]
PERIOD_MS=50
RING_AGE_MS=500

H: change only XImage payload representation normalization; bytes stay identical, string-like python-xlib payloads encode strict Latin-1, unsupported/non-Latin-1/wrong-length payloads fail closed. This removes A6's capture18 TypeError without altering the ROI/cadence/cost contract.
T: pure normalization controls + excluded X11 construction >=25 captures before source freeze. Then exact A6 scientific block: six fresh matched pairs, 300 ms warmup, 1500 ms measurement, 20 Hz fixed ROI XGetImage, 500 ms raw ring, one detached supervisor, reruns/replacements/tuning0.
D: PASS_X11_TEMPORAL_ROI_CAPTURE_OVERHEAD_SCOPED iff normalization integrity and all inherited A6/A4 overhead gates pass. FAIL_PAYLOAD_NORMALIZATION for payload type/length/normalization failure; REJECT_ROI_CAPTURE_COST for complete mechanically valid arms failing stable-baseline overhead gates; HOLD_HOST_SCHEDULING_NOISE under inherited baseline criterion; source/region/task drift FAIL_INTEGRITY.
C: str payload may be python-xlib/Xvfb-specific; strict Latin-1 is byte-bijective only for codepoints0..255.
U: fixed Xvfb ROI only; no dynamic ROI, real compositor, privacy, model/task/token claim.

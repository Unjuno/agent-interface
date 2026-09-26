# #2874 polling-period / observer-packaging distortion allocation

Allocation: polling-distortion-2874-20260924-01
Base main: e086a1cd6efaf7c1de77872c85da0689cee6d042
Parent #225 source blob: 64bd892826cba9f7d436cc37c3b4e1aa87101909
Parent exact 38-case schedule hash (canonical generated JSON): 258bd755e660c57bdb9ca4d40598fa40342dcd97204c504a8e1a7c0b8c1dff64

H: The dense 2 ms route's timed-loop evidence packaging contributes material cue-duration distortion. Deferring SHA-256/Base64 retention until after the watch loop preserves the same 32x32 XGetImage and exact BGR predicate while reducing timed-loop work; the 2 ms detection advantage over 10 ms should survive if cadence rather than packaging is the primary cause.

T: Fresh private-Xvfb/Tk sessions only. Four routes each replay the exact #225 38-case randomized schedule as an ordering template (152 fresh cases total): RENDER_ONLY, FULL_10MS, FULL_2MS, DEFERRED_RECORD_2MS. Cue 5 ms nominal; offsets, ROI, threshold, Right input, 600 ms authority, final clear unchanged. FULL hashes/Base64-encodes each ROI inside the timed loop; DEFERRED performs the identical immediate match_count predicate but hashes/Base64-encodes retained raw ROI only after the timed loop. RENDER_ONLY performs no ROI observation. Routes execute in the frozen order RENDER_ONLY, FULL_10MS, FULL_2MS, DEFERRED_RECORD_2MS, one external call each; no rerun/replacement/pooling with #225.

D: Safety/integrity requires 152/152 records, one app press/release, verified neutral Right, final clear. Target/nuisance scoring uses fresh rows only. PASS_DISTORTION_SEPARATED_SCOPED requires: FULL_2MS target detections > FULL_10MS; DEFERRED_2MS target detections >= FULL_2MS; nuisance false detections=0 in all observed routes; DEFERRED median timed record work < FULL_2MS; FULL_2MS median cue duration exceeds RENDER_ONLY by >=0.5 ms (10% of nominal cue) and DEFERRED removes >=50% of that signed extension without becoming >0.5 ms shorter than RENDER_ONLY. If detection gain survives but the >=0.5 ms predecessor-style distortion is not exposed, HOLD_NO_MATERIAL_DISTORTION_EXPOSED. If material distortion is exposed but deferred does not remove >=50%, HOLD_PACKAGING_NOT_CAUSAL. Safety/integrity failure is FAIL_SAFETY_OR_INTEGRITY. Missing denominator/evidence is STOP/HOLD.

C: Python scheduling, X socket latency, Tk draw/update scheduling and serial route order remain competing explanations. RENDER_ONLY cannot detect. This isolates only packaging work inside the Python watcher, not all observation overhead.

U: Synthetic known-colour ROI, one Linux/Xvfb host, software draw timestamps, no CPU pin/frequency calibration, no model/game/user desktop. No hard-real-time, arbitrary-GUI, population reliability or product claim.

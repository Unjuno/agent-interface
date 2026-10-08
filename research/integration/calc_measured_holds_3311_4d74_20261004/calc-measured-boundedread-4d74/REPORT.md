# G12: retained OCR false negative and unexercised continuation

Disposition: **HOLD_OCR_FALSE_NEGATIVE_CONTINUATION_UNEXERCISED**.

One fresh measured model context and one registered tool call drove one owned
Calc program. The exact saved XML contains19×29=551, no unintended populated
cells. The post-action source PNG visually shows551. Tesseract returned19,29,951;
the graph yielded effect_failed before the second native program. The second
save is absent and censored. Neither native exit0 nor the saved-data audit's
empty error list proves whole-task success.

The planned unavailable-only read continuation was never used. Its efficacy
remains untested. Preserve the frozen implementation: its ROI hash is calculated
before continuation, so a future continuation would produce a stale hash
association. A successor must bind both ROI and predicate to the final capture.

Independent retained-data audit: AUDIT_RETAINED.json checks frozen source hashes,
PNG and ROI hashes, graph capture associations, exact saved cells and physical
release. No GUI, model or OCR replay occurs in that auditor. Parent cleanup is
recorded; graceful close and complete descendant retirement are unproven.

Measured model input17738, cached14848(subset), output249, reasoning136(subset),
total17987, one dynamic call, host wall9198405600ns. Four original OCR attempts
took294882665ns. Primary construction context cost is unknown. No matched ratio.

Separate post-run saved-image diagnostic: diagnose_ocr_saved.py runs four fixed
scale/resampling combinations on the retained C2 crop in WSLc image
sha256:86edd8e13599b0e4e035b5865e4fee340740d349308a2a24a1304aa1cb41dde2.
Nearest4/8 returned1/1; bicubic4/8 returned951/991. All exited0, none recognized551.
Raw/crops retained in ocr-diagnostic. This is diagnostic fitting on known evidence,
not held-out validation, a G12 regrade, or a fresh application-effect experiment.
Observed cpu.max100000100000 and memory.max536870912; swap-limit warning occurred.
The crop itself was visually inspected and contains551. Simple enlargement is
not a sufficient recognition repair on this evidence. Further qualification is
required before integrated efficiency evaluation. G11 and all prior results remain
unchanged; #57/#59 and ROADMAP remain open.

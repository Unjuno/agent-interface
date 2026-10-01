# Inkscape primary use: move and save

One retained primary-model session, seed 991359, on Linux/X11 using the integrated portable public MCP. The plan predates allocation. This is a cross-application engineering check, not a matched performance experiment.

The original task was to move the red rectangle right and save while preserving rectangle count, Y, width, height and fill. After control ended, the saved SVG contained one rectangle at X=70.338982, Y=50, width=40, height=30, fill=#ff0000 (initial X=50). The task passed its original criterion. There were five calls: observe, select, drag, save, close; three input programs, four full image presentations, no image references and no extra observation or repeated drag.

The commanded pointer path was 36 screen pixels right. The contemporaneous visual review recorded approximately 24 screen pixels of object movement at 118% zoom. Actual pointer position was not independently sampled. Therefore this does not establish endpoint accuracy, a cause for the displacement difference, or a universal compensation formula. Research issues #4388, #4359 and #4424 are relevant intake candidates, but their different fixtures and incomplete public raw delivery do not justify integrating an automatic corrector here. No sensor or servo was added.

Host send-to-reply intervals totaled 2246.3534 ms; first send to final reply was 75249.2028 ms. These are host boundaries, not isolated model latency, first useful feedback, or semantic completion measurements. Human-tempo equivalence and token/cost improvements remain unmeasured. Reuse was enabled but all four images were delivered in full; no compression benefit is claimed.

Relay exit was 0. Fixture cleanup retained return codes 0, 1 and -15; these are reported without relabeling every process exit as clean success. The completed fixture was not restarted after the WSL reboot.

Run `python3 -O runtime/results/inkscape-current-primary-01/verify.py` to check the pinned evidence, actual request sequence, dispatch/release outcomes, image/review identities and the independent saved-SVG task oracle. Raw records are retained in raw.tar.gz. This verifier does not rerun the task or prove the approximate visual displacement.

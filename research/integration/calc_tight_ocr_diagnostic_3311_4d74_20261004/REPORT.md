# G13 saved-image tight OCR diagnostic

Disposition: HOLD_RECOGNITION_TRANSFER. The fixed candidate removes whitespace
using intensity<130 bounding boxes, scales4 bicubic, pads20 white pixels, and
uses Tesseract psm8/digit whitelist. Expected values were stored only in the
host oracle, which was not mounted into the candidate container.

One WSLc run used11 immutable saved captures. Ten whole-row/blank outcomes
matched the independent oracle, including six blank/unavailable cases; only
four of five numeric rows matched. G12's551 reads correctly, but G10's47 reads7.
This is development diagnosis on previously inspected evidence, not a held-out
accuracy estimate. No new GUI/input/model calls; no historical result regrade.
Simple crop/segmentation changes do not qualify a trustworthy visual verifier.

Candidate SHA2569208a44e6fc5c7429e7f162cdac29f5488721ad0c39b32c8319e984751ad87ac.
WSLc image86edd8e13599b0e4e035b5865e4fee340740d349308a2a24a1304aa1cb41dde2;
--rm --network none --cpus1 --memory512m --user65534:65534;
inputs, INPUTS.json and candidate.py separately read-only mounted under/src,
out writable under/out; python3 -B/src/candidate.py. Swap-limit warning occurred.
No effective cgroup values were captured in this run, so requested caps are not
certified as observed enforcement. Source images trace to the previous G08–G12
packets. INPUTS.json hashes the original images; raw includes crop hashes,
bounds, actual argv/stdout/stderr/exit and monotonic timestamps. AUDIT.json
checks source/crop hashes, clock order and separately supplied truth, errors[].
The audit is read-only and not a recognition rerun or native provenance proof.

Do not rerun into the existing out or AUDIT paths. Keep the frozen counterexample.
Next decision: qualify recognition uncertainty and target/effect authority before
new model-loop integration or efficiency claims. #3311/#57/#59 remain open.

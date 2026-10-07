# Freeze: grayscale five-PSM unanimity diagnostic

- Issue: #3311 integration recognition/refusal blocker.
- Run identity: `CALC-GRAY-PSM-CONSENSUS-3311-20261004-G21`.
- Protocol class: one-shot saved-image construction diagnostic; no GUI, model, or input.
- Base/source: `origin/main` `573ae228c95ba091a3e47d99dec938dc51f76215` (G20 and G12 evidence already merged).
- Candidate method: crop the three fixed full-cell boxes from each of the eleven retained G08-G12 frames; convert to grayscale without thresholding; nearest-neighbor 4x scale; add a 20px white border; run Tesseract English with digit whitelist once each at PSM 6, 7, 8, 10, and 13. Emit a cell value only when all five successful digit-only results are identical; otherwise abstain (`null`).
- Inputs: eleven literal image bytes in `input/`, with hashes and names from G20 `INPUTS.json`. Ground truth is in `truth/ORACLE_HOST_ONLY.json`, excluded from `candidate.py` inputs and not read by the candidate. This is the same known-image development set as G20, not a held-out set. Duplicate source image hashes are preserved as repeated frames and are not counted as independent evidence.
- H: unthresholded grayscale plus fixed multi-mode unanimity may recover numeric rows rejected by the G20 fixed binary PSM7 candidate while abstaining on blank rows.
- T: run candidate once for all 11 frames × 3 cells × 5 PSM modes. Then run the saved-data auditor once. No tuning or retries.
- D: candidate gate only if all five nonblank oracle cells yield the exact unanimous string and all six blank oracle cells abstain. Any wrong or missing numeric result, or any numeric consensus on a blank, rejects the candidate. Auditor disposition is separate from audit integrity.
- C: same fixed layout and known development images as G20; multiple PSM modes are correlated views of one Tesseract installation, not independent voters. This cannot estimate general accuracy or live recognition reliability.
- U: this is a host-native macOS run because OrbStack image inventory failed with `operation not supported`; the G20 Linux container's effective resource limits are not relevant to this run. The image store failure is retained in `ENVIRONMENT.txt`. This run cannot isolate OS/build/traineddata effects and cannot qualify runtime adoption.
- Environment observed before invocation: `/run/current-system/sw/bin/tesseract` 5.5.2; ImageMagick version and macOS version are recorded in `RAW.json`. The container image registry was not changed and no image pull was attempted.
- Output: one exclusive-create `candidate-out/RAW.json`; no overwrite/retry. Auditor writes `AUDIT.json` after candidate completion.

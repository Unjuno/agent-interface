# #6640 omitted-baseline audit — successor #6668

Post-hoc analytic audit of the immutable #6640 allocation-01 fixture and
outputs. This package computes the omitted Ochiai, failed-exposure-count, and
failed-exposure-rate rankings, independently rebuilds the four predecessor
rankings, and requires exact row-level agreement with the committed candidate
raw plus metric agreement with the predecessor audit before publishing metrics.

No predecessor candidate/auditor was rerun. No threshold or `FAIL_METHOD`
disposition was changed. The result is descriptive for the same authored 32
seed fixture; it is not independent data, causal evidence, or a real-interface
fault-localization result. Inputs are pinned by Git blob IDs in
`INPUT_MANIFEST.json`; use latest-main ancestry recorded there.

Run `python3 -B audit.py --output results/posthoc-01/omitted_baselines.json`.
Host execution is a deterministic archive-only calculation, not a formal
candidate allocation or container result. Unit tests check formula and
integrity controls; `REPORT.md` will record exact observed output and hashes.

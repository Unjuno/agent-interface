# Publication-integrity correction

This note corrects one publication claim for `INKSCAPE-ACTION-HISTORY-TRUE120-20260916-001`. It does **not** change or rerun the measured allocation.

## Finding

After PR #516 was merged, a byte-exact readback check compared the locally frozen/measured sources against the blobs retained on `main`.

Five of the six preregistered source files are byte-exact on GitHub:

- `run_case.py`: Git blob `7880fcf70fd759f910132d47595b88f96ae46ea7`;
- `run_chunk.py`: `a76074611d061cabe15962f8d58e45e3c39bd2e6`;
- `schedule.json`: `5f617d143b89691a6ec477cec482d2a585f527a1`;
- `environment.json`: `baa484a279a119390e5ce7a9a70c5012b702bdc9`;
- `prereg.json`: `688177114aa7547a1d436f072f810873ca8d226e`.

The sixth file, `audit.py`, was **not** byte-exact in the premeasurement GitHub publication:

- locally frozen/measured auditor: 3,921 bytes, SHA-256 `6890227960b0ee03bcbf6133363f01732115364d582b396ce854d7b471b54acd`, Git blob `93a124438a9d6c173631e4a26ad93ba1f5816ef9`;
- GitHub-published `audit.py`: 3,901 bytes, SHA-256 `2c336161be3ee3bb6c5d9b6d5c625596df30fae74c4568ad88b61b9d5d603cbe`, Git blob `bfbd906693242dc819c15d66bfae50bddcb1c740`.

The exact difference is one non-executable comment line present only in the measured local auditor:

`# stable hard gate`

Removing that single comment from the locally measured auditor produces the exact 3,901-byte GitHub blob `bfbd906693242dc819c15d66bfae50bddcb1c740`.

## Corrected claim

Do **not** claim `6/6 byte-exact source publication before measurement` for this allocation. The correct statement is:

> `5/6 preregistered source files were byte-exact on GitHub before measurement; the auditor had a one-comment, execution-inert publication mismatch. The exact measured auditor is retained post hoc as audit_measured_exact.py.`

The mismatch does not change the measured scientific decision because the only byte difference is a Python comment. The formal allocation was audited by the locally frozen 3,921-byte auditor, and the retained compact result was independently rechecked postformal from raw images, timestamps, SVG effects and release evidence. No measured ID is rerun or replaced.

## Retention

`audit_measured_exact.py` is a post-result byte-exact retention of the auditor that actually produced the formal audit. Its SHA-256 is `6890227960b0ee03bcbf6133363f01732115364d582b396ce854d7b471b54acd` and its Git blob is `93a124438a9d6c173631e4a26ad93ba1f5816ef9`.

Historical commits are not rewritten. The original GitHub `audit.py` and the publication chronology remain preserved.

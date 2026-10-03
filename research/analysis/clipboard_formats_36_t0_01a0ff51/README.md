# Clipboard multi-representation paste — Issue #36

Prospective Qt/offscreen method fixture for the multi-representation refinement
in [Issue #36](https://github.com/Unjuno/agent-interface/issues/36).
See [the frozen protocol](PREREGISTRATION.md). The formal outcome has not yet
been observed at this source version. No shared runtime is modified.

The test uses actual Qt paste/document behavior and independent saved-state
verification. It compares diagnostic metadata/effect judgments on the same
fixture outcomes; it does not test four controllers or native clipboard input.
Format retrieval, chosen representation and correct persisted effect are
different claims. The effect-only alternative is included to challenge whether
an extra format receipt is needed.

Local tests: `python -B -m unittest discover -s . -p 'test_*.py' -v`.
Candidate: `python -B candidate.py --cases cases.json --output /out/candidate`.
Auditor: `python -B audit.py --oracle oracle.json --raw /raw/raw.json --output /out/audit.json`.
Use the pinned image and mounts/limits in the protocol; outputs must not exist.

Construction failures, raw outcomes and original sources are retained under
`construction/`. No audio, model, GPU, host clipboard or physical input is used.

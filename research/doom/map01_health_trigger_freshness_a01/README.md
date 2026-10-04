# MAP01 health-trigger fresh-frame identity A01

This posthoc reconstruction checks one untested provenance assumption in the retained v39 no-policy health debounce replay: each pair of typed health rows came from distinct captured frames and exactly matches its same-sequence full observation record.

Run `python analyze.py` followed by `python audit.py` from this directory. The analyzer pins the retained v38/v39 event and report files by SHA-256, extracts v39 d2 sequences 81/82 and d3 sequences 103/104, and writes `RESULT.json`. The independent audit rereads the raw source files and result and writes `AUDIT.json`.

The decision is intentionally narrow. Distinct frame hashes and same-sequence raw identity establish separate captures; they do not show independent semantic evidence, a changed game state, correct OCR, useful control, detector quality, safety, or a false-trigger rate. The v38 d2 trace has only one qualifying below-baseline row before the terminal boundary, so it is censored context rather than a matched comparison. No live game, model, GUI, input, container, or new allocation was used.

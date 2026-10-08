# Formal run receipt

Allocation: `EFFECT-INTERFERENCE-5366-T2-20261002-01`.

Frozen main: `c69fa71501a0e42abc3ffe435ae72949d5d15877`. Frozen input/source hashes are recorded in `FREEZE.json`. Formal commands, invocation counts, exit codes, output hashes, and the auditor decision are appended after the single permitted invocations. Construction failure and corrected construction pass are preserved in `CONSTRUCTION_LOG.md`.

Runtime: CPython 3.14.5, macOS arm64, standard library only. No model, GUI, network, GPU, host input, or external effect. The OrbStack Engine responds, but one owner-unknown shared container is running under the coordination state recorded in #5085; no container was started, stopped, or modified.

Formal candidate: `python3 candidate.py fixture.json outputs/formal/candidate_raw.json` — invocation 1/1, exit 0, row_count 15. Raw SHA-256: `d452bcad1404bdf6f08b164f010f634129ab30ce7329237baed4c1191181a567`.

Independent audit: `python3 audit.py fixture.json outputs/formal/candidate_raw.json outputs/formal/audit.json` — invocation 1/1, exit 0, `PASS_METHOD_SCOPED`, rows_reconstructed 15, errors `[]`. Audit SHA-256: `2c9e52e4517540519fa46c34683bdc9a80ff5b3514fc24036998ae430a10ef65`.

Formal retries: 0. No formal code or raw output was changed after either invocation. Freeze SHA-256: `891b9ef21639a06903684d5fa8ddc57031df2cb134f1635bf198df427a79ecc8`.

# T5 source and image manifest

Issue: #5446, preregistration comment `5910422478`

## Frozen before formal allocation

| file | preregistered SHA-256 | disposition |
|---|---|---|
| `experiment.py` | `06677dc7f48fba6ab0d5860c4b601b3d92d5913994d16cc84ee586154f2a7b67` | unchanged; formal candidate |
| `audit.py` | `de337c7cfb5fd1398d8aed0c43f13527cb76ce535894c5421011ffc220237fc6` | initial version produced retained FAIL due to string check |

## Post-allocation audit repair

`audit.py` SHA-256 is now `943fdb729381681cdd4546335a06b294f86362ddf7f4483efee75641e63925e9`. Only the total-probability representation assertion changed: parse the JSON rational text with `Fraction` and compare mathematically to one, rather than require literal `1/1`. Candidate code and `raw/formal.json` were not modified after the first invocation. An identical candidate command was inadvertently executed a second time while attempting to display the first result after a tool-output issue; it was deterministic, produced matching displayed JSON, and its stdout was not saved separately. The repeat violates the preregistered one-invocation protocol and is disclosed in the report. The original audit result remains at `raw/audit.json`; corrected result is `raw/audit_v2.json`.

## Runtime

- OrbStack Docker Engine: `29.4.0`, `linux/arm64`.
- Image tag: `python:3.12-slim`.
- Local immutable image ID and repo digest: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Network disabled for candidate execution and audit.
- No RNG, model download, host application, or external service.

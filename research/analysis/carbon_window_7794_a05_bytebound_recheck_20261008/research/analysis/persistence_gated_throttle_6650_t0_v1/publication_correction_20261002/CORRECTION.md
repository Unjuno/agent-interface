# Publication serialization correction

The original parent artifact `../AUDIT.json` is preserved byte-for-byte (SHA256 `da602239e384691e4a206ba460985d1461151d45e886984cdf7453f0acad1172`). It has valid JSON content followed by the two literal characters `\\n`, so strict JSON parsers reject it as trailing extra data. This is an output-serialization defect, not a new auditor result.

`AUDIT_CORRECTED.json` is an additive publication copy of the already emitted audit object: allocation `PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-T0-20261002-01`, one independent audit execution, zero errors. The candidate and auditor were not rerun; the original raw output, audit bytes, formal run count, freeze, and parent SHA256 manifest remain unchanged. The correction does not repair the separate limitation that the T0 auditor did not independently replay the controller law.

`test_correction.py` checks parseability, the exact published audit fields, and the retained predecessor hash only. `SHA256SUMS` binds the correction package.

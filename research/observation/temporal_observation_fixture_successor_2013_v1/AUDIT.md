# Independent audit

Container: python:3.12-slim

- py_compile: PASS with PYTHONPYCACHEPREFIX=/tmp/pycache
- experiment: PASS_TEMPORAL_OBSERVATION_FIXTURE_SCOPED
- independent audit: PASS
- seven semantic cases and two negative controls passed
- construction=0, formal=1, GUI/X11/model/network/input=0
- SHA-256: 4d8b4175572b52e7fef220e09c13e781532fb387dc720cc9d4feb372bd582f6c

The first py_compile attempt failed solely because the source mount was read-only. This infrastructure stop is retained and is not reclassified as a scientific failure.

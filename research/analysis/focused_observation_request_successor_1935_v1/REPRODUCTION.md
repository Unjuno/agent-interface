# Reproduction

Run the candidate and independent audit with Python 3:

```text
python experiment.py
python audit.py
```

Expected candidate summary:

```json
{"rows": 256, "valid": 16, "rejected": 240, "sha256": "5c2699e993fd163a1a01c72c3905b46c8f364e329a8ddef47c37bb713952b936"}
```

Expected independent audit:

```text
independent_rows=256 independent_valid=16 independent_rejected=240 audit=PASS
```

Local formal container reproduction is PASS using Docker Desktop 29.8.0 and `python:3.11-slim`; see `MANIFEST.json` for the pinned image digest and scope boundary. The gate remains fixture-scoped and does not claim model, GUI, runtime, or production authority.

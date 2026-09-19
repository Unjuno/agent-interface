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

The formal container gate is intentionally HOLD because Docker was unavailable in the execution environment. No retry or scientific reinterpretation is made.
